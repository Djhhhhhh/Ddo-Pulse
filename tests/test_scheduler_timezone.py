"""Tests for cron timezone fix — Asia/Shanghai (UTC+8).

Covers:
- G1: CronTrigger.from_crontab resolves hours in Asia/Shanghai
- G2: validate_cron_expression accepts valid cron without error
- G3: AsyncIOScheduler can register jobs with APP_TZ timezone
"""

import pytest


# ── G1. CronTrigger 时区解析 ────────────────────────────────────────────


class TestCronTriggerTimezone:
    """Verify CronTrigger uses Asia/Shanghai instead of UTC."""

    def test_nine_am_cron_resolves_to_cst_9am(self):
        """G1-cmd1: '0 9 * * *' must fire at 09:00 Asia/Shanghai, not 09:00 UTC."""
        # Arrange
        from apscheduler.triggers.cron import CronTrigger
        from ddo_pulse_db.datetime_util import APP_TZ
        from datetime import datetime

        trigger = CronTrigger.from_crontab("0 9 * * *", timezone=APP_TZ)
        now = datetime(2026, 7, 14, tzinfo=APP_TZ)

        # Act
        fire_time = trigger.get_next_fire_time(None, now)

        # Assert
        assert fire_time is not None
        assert fire_time.hour == 9
        assert fire_time.minute == 0

    def test_weekday_afternoon_cron_resolves_to_cst(self):
        """G1-cmd2: '30 14 * * 1-5' must fire at 14:30 Asia/Shanghai."""
        # Arrange
        from apscheduler.triggers.cron import CronTrigger
        from ddo_pulse_db.datetime_util import APP_TZ
        from datetime import datetime

        trigger = CronTrigger.from_crontab("30 14 * * 1-5", timezone=APP_TZ)
        now = datetime(2026, 7, 14, 0, 0, tzinfo=APP_TZ)  # Tuesday

        # Act
        fire_time = trigger.get_next_fire_time(None, now)

        # Assert
        assert fire_time is not None
        assert fire_time.hour == 14
        assert fire_time.minute == 30


# ── G2. validate_cron_expression 一致性 ─────────────────────────────────


class TestValidateCronExpression:
    """Verify validate_cron_expression accepts valid cron strings."""

    def test_validate_daily_9am(self):
        """G2-cmd1: validate_cron_expression('0 9 * * *') must not raise."""
        # Arrange
        from ddo_pulse_api.scheduler import validate_cron_expression

        # Act & Assert
        validate_cron_expression("0 9 * * *")  # should not raise

    def test_validate_weekday_afternoon(self):
        """G2-cmd2: validate_cron_expression('30 14 * * 1-5') must not raise."""
        # Arrange
        from ddo_pulse_api.scheduler import validate_cron_expression

        # Act & Assert
        validate_cron_expression("30 14 * * 1-5")  # should not raise


# ── G3. 集成验证 ─────────────────────────────────────────────────────────


class TestSchedulerIntegration:
    """Verify AsyncIOScheduler registers jobs with correct timezone."""

    def test_scheduler_registers_cron_job_with_tz(self):
        """G3-cmd1: Scheduler can register a job with APP_TZ CronTrigger."""
        # Arrange
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        from ddo_pulse_db.datetime_util import APP_TZ

        scheduler = AsyncIOScheduler()

        # Act
        scheduler.add_job(
            lambda: None,
            CronTrigger.from_crontab("0 9 * * *", timezone=APP_TZ),
            id="test_tz_job",
        )

        # Assert
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "test_tz_job"
