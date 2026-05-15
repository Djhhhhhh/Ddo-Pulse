"""APScheduler wiring for pipeline jobs."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ddo_pulse_core.pipeline import run_pipeline_job
from ddo_pulse_db.repository import Database

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger

    _HAS_APSCHEDULER = True
except ImportError:
    AsyncIOScheduler = None  # type: ignore[misc, assignment]
    CronTrigger = None  # type: ignore[misc, assignment]
    _HAS_APSCHEDULER = False

scheduler: AsyncIOScheduler | None = None


def validate_cron_expression(expr: str) -> None:
    """Raise ValueError if cron string cannot be parsed.

    When APScheduler is installed, parsing matches runtime scheduling. Otherwise
    we only require the usual five cron fields so API/CLI can persist jobs; the
    process logs that in-process scheduling is disabled until APScheduler is installed.
    """
    s = expr.strip()
    if not s:
        raise ValueError("empty cron expression")
    if _HAS_APSCHEDULER and CronTrigger is not None:
        CronTrigger.from_crontab(s)
        return
    parts = s.split()
    if len(parts) != 5:
        raise ValueError(
            "cron must have exactly 5 space-separated fields "
            "(minute hour day month weekday); "
            "install apscheduler for full validation and in-process scheduling"
        )


def _run_scheduled_job(job_id: int) -> None:
    db = Database()
    try:
        run_pipeline_job(db, job_id, trigger="scheduled")
    except Exception:
        logger.exception("Scheduled pipeline job %s failed", job_id)
    finally:
        db.close()


def reload_pipeline_jobs_schedule(s: AsyncIOScheduler | None = None) -> None:
    """Re-register all enabled pipeline jobs on the scheduler."""
    if not _HAS_APSCHEDULER or AsyncIOScheduler is None or CronTrigger is None:
        logger.warning("apscheduler unavailable; scheduled jobs disabled")
        return
    tgt = s or scheduler
    if tgt is None:
        return
    db = Database()
    try:
        tgt.remove_all_jobs()
        for job in db.list_pipeline_jobs():
            if not job["enabled"]:
                continue
            jid = int(job["id"])
            cron = (job["schedule_cron"] or "").strip()
            try:
                trigger = CronTrigger.from_crontab(cron)
            except Exception as exc:
                logger.warning("Skip job %s invalid cron %r: %s", jid, cron, exc)
                continue
            tgt.add_job(
                _run_scheduled_job,
                trigger,
                args=[jid],
                id=f"pipeline_job_{jid}",
                replace_existing=True,
            )
    finally:
        db.close()


def create_and_start_scheduler() -> AsyncIOScheduler | None:
    global scheduler
    if not _HAS_APSCHEDULER or AsyncIOScheduler is None:
        logger.warning("apscheduler not installed; use pip install apscheduler")
        return None
    s = AsyncIOScheduler()
    reload_pipeline_jobs_schedule(s)
    s.start()
    scheduler = s
    return s


def shutdown_scheduler() -> None:
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
