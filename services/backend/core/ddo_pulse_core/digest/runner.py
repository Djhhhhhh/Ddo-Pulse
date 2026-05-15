"""Build digest and push to Feishu."""

from __future__ import annotations

import json
import logging
from typing import Any

from ddo_pulse_core.digest.builder import (
    build_markdown_body,
    digest_date_today,
    item_ids_from_rows,
)
from ddo_pulse_core.notifier.feishu import (
    FEISHU_SETTING_KEY,
    build_feishu_post_payload,
    send_feishu_webhook,
)
from ddo_pulse_db.repository import Database

logger = logging.getLogger(__name__)

DEFAULT_TOP_N = 8


def build_and_push_digest(
    db: Database,
    *,
    job_id: int,
    date: str | None = None,
    top_n: int = DEFAULT_TOP_N,
    score_threshold: int = 7,
    source_ids: list[int] | None = None,
    push: bool = True,
    force_push: bool = False,
    feishu_webhook_url: str | None = None,
) -> dict[str, Any]:
    """
    Upsert digest for (date, job_id) and optionally send Feishu notification.
    """
    digest_date = date or digest_date_today()
    stats: dict[str, Any] = {
        "digest_date": digest_date,
        "digest_id": None,
        "digest_items": 0,
        "pushed": False,
        "push_skipped": False,
        "push_skip_reason": None,
        "push_error": None,
    }

    rows = db.list_digest_candidates(
        score_threshold=score_threshold,
        limit=top_n,
        source_ids=source_ids,
    )
    stats["digest_items"] = len(rows)

    item_ids = item_ids_from_rows(rows)
    markdown = build_markdown_body(digest_date, rows)
    digest_id = db.upsert_digest(
        job_id,
        digest_date,
        item_ids_json=json.dumps(item_ids, ensure_ascii=False),
        markdown_body=markdown,
    )
    stats["digest_id"] = digest_id

    if not push:
        stats["push_skipped"] = True
        stats["push_skip_reason"] = "push_disabled"
        return stats

    # Pipeline passes enabled-only source ids; empty means no fetch scope for this run — do not spam Feishu.
    # CLI `digest push` uses `source_ids=None` when the job has no rows, so this guard does not apply there.
    if source_ids is not None and len(source_ids) == 0:
        stats["push_skipped"] = True
        stats["push_skip_reason"] = "no_enabled_sources"
        return stats

    webhook = (feishu_webhook_url or "").strip()
    if not webhook:
        webhook = (db.get_app_setting(FEISHU_SETTING_KEY) or "").strip()
    if not webhook:
        stats["push_skipped"] = True
        stats["push_skip_reason"] = "no_webhook"
        return stats

    if not force_push and db.has_successful_push(digest_id):
        stats["push_skipped"] = True
        stats["push_skip_reason"] = "already_pushed"
        return stats

    payload = build_feishu_post_payload(digest_date, rows)
    ok, response = send_feishu_webhook(webhook, payload)
    db.insert_push_log(
        digest_id=digest_id,
        status="ok" if ok else "failed",
        response=response[:2000] if response else None,
    )
    stats["pushed"] = ok
    if not ok:
        stats["push_error"] = response
    return stats
