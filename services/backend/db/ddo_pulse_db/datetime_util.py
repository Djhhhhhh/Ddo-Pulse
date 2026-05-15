"""Wall-clock convention for persisted timestamps: Asia/Shanghai (UTC+8)."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo("Asia/Shanghai")


def storage_now_iso() -> str:
    """ISO-8601 local time with +08:00 offset for DB TEXT columns."""
    return datetime.now(APP_TZ).replace(microsecond=0).isoformat()


def storage_cutoff_iso(days: int) -> str:
    """Lower bound for relative window queries (same offset as storage_now_iso)."""
    return (
        datetime.now(APP_TZ) - timedelta(days=max(1, int(days)))
    ).replace(microsecond=0).isoformat()


def digest_calendar_date_today() -> str:
    """Digest bucket date YYYY-MM-DD in Asia/Shanghai."""
    return datetime.now(APP_TZ).strftime("%Y-%m-%d")
