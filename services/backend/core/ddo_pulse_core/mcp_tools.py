"""MCP tool implementations (core only, no HTTP)."""

from __future__ import annotations

import json
from typing import Any

from ddo_pulse_core.digest.builder import digest_date_today
from ddo_pulse_core.pipeline import run_fetch
from ddo_pulse_db.repository import Database


def _source_row_to_dict(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "type": row["type"],
        "url": row["url"],
        "enabled": bool(row["enabled"]),
    }


def _analyzed_row_to_summary(row: Any) -> dict[str, Any]:
    categories: list[str] = []
    try:
        categories = json.loads(row["categories_json"] or "[]")
    except json.JSONDecodeError:
        pass
    return {
        "id": row["id"],
        "score": row["score"],
        "is_quality": bool(row["is_quality"]),
        "title": row["title"],
        "url": row["url"],
        "summary_zh": row["summary_zh"],
        "categories": categories,
        "analyzed_at": row["analyzed_at"],
    }


def list_sources() -> list[dict[str, Any]]:
    db = Database()
    try:
        return [_source_row_to_dict(r) for r in db.list_sources()]
    finally:
        db.close()


def trigger_fetch(source_id: int | None = None) -> dict[str, Any]:
    db = Database()
    try:
        return run_fetch(db, source_id=source_id)
    finally:
        db.close()


def get_today_digest() -> str:
    db = Database()
    try:
        jid = db.get_first_pipeline_job_id()
        if jid is None:
            return (
                f"# Ddo-Pulse\n\n尚未创建定时任务。请先新建 pipeline job，再运行 `ddo-pulse run-once`。"
            )
        row = db.get_digest_by_date_and_job(digest_date_today(), jid)
        if row is None:
            return f"# Ddo-Pulse\n\n今日（{digest_date_today()}）尚无 digest，请先运行 `ddo-pulse run-once`。"
        return row["markdown_body"] or ""
    finally:
        db.close()


def get_recent_items(days: int = 7, min_score: int | None = None) -> list[dict[str, Any]]:
    db = Database()
    try:
        rows = db.list_analyzed_items_recent(days=days, min_score=min_score, limit=100)
        return [_analyzed_row_to_summary(r) for r in rows]
    finally:
        db.close()
