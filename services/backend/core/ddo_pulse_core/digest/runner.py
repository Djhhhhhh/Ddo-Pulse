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


def _upsert_merged_digest(
    db: Database,
    *,
    job_id: int,
    digest_date: str,
    batch_rows: list[Any],
) -> tuple[int, int]:
    """Merge batch into daily digest markdown; returns (digest_id, total_items_in_digest)."""
    batch_ids = item_ids_from_rows(batch_rows)
    merged_ids = db.merged_digest_item_ids(job_id, digest_date, batch_ids)
    if not merged_ids:
        existing = db.get_digest_by_date_and_job(digest_date, job_id)
        if existing:
            return int(existing["id"]), 0
        digest_id = db.upsert_digest(
            job_id,
            digest_date,
            "[]",
            build_markdown_body(digest_date, []),
        )
        return digest_id, 0
    all_rows = db.list_analyzed_items_by_ids(merged_ids)
    ordered_ids = [int(r["id"]) for r in all_rows]
    markdown = build_markdown_body(digest_date, all_rows)
    digest_id = db.upsert_digest(
        job_id,
        digest_date,
        json.dumps(ordered_ids, ensure_ascii=False),
        markdown,
    )
    return digest_id, len(ordered_ids)


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
    Select up to top_n unpushed quality articles (score desc), push only that batch,
    and merge into the daily digest. Already-pushed articles are never sent again.
    """
    digest_date = date or digest_date_today()
    stats: dict[str, Any] = {
        "digest_date": digest_date,
        "digest_id": None,
        "digest_items": 0,
        "push_items": 0,
        "pushed": False,
        "push_skipped": False,
        "push_skip_reason": None,
        "push_error": None,
    }

    _ = force_push  # kept for API/CLI compat; per-article dedup is always enforced
    rows = db.list_digest_candidates(
        score_threshold=score_threshold,
        limit=top_n,
        source_ids=source_ids,
        exclude_pushed=True,
    )
    stats["push_items"] = len(rows)

    if not push:
        stats["push_skipped"] = True
        stats["push_skip_reason"] = "push_disabled"
        if rows:
            digest_id, total = _upsert_merged_digest(
                db, job_id=job_id, digest_date=digest_date, batch_rows=rows
            )
            stats["digest_id"] = digest_id
            stats["digest_items"] = total
        return stats

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

    if not rows:
        stats["push_skipped"] = True
        stats["push_skip_reason"] = "no_new_items"
        existing = db.get_digest_by_date_and_job(digest_date, job_id)
        if existing:
            stats["digest_id"] = int(existing["id"])
            try:
                stats["digest_items"] = len(
                    json.loads(existing["item_ids_json"] or "[]")
                )
            except (json.JSONDecodeError, TypeError):
                stats["digest_items"] = 0
        return stats

    batch_label = f"新增 {len(rows)} 篇" if rows else None
    payload = build_feishu_post_payload(
        digest_date, rows, batch_label=batch_label
    )
    ok, response = send_feishu_webhook(webhook, payload)
    existing = db.get_digest_by_date_and_job(digest_date, job_id)
    digest_id = int(existing["id"]) if existing else 0
    if ok:
        db.mark_articles_pushed(item_ids_from_rows(rows))
        digest_id, total = _upsert_merged_digest(
            db, job_id=job_id, digest_date=digest_date, batch_rows=rows
        )
        stats["digest_id"] = digest_id
        stats["digest_items"] = total
    elif existing:
        stats["digest_id"] = digest_id
        try:
            stats["digest_items"] = len(
                json.loads(existing["item_ids_json"] or "[]")
            )
        except (json.JSONDecodeError, TypeError):
            stats["digest_items"] = 0
    if digest_id:
        db.insert_push_log(
            digest_id=digest_id,
            status="ok" if ok else "failed",
            response=response[:2000] if response else None,
        )
    stats["pushed"] = ok
    if not ok:
        stats["push_error"] = response
    return stats
