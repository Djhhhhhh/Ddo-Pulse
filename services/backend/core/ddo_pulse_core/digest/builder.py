"""Build daily digest markdown from analyzed_items."""

from __future__ import annotations

import json
from typing import Any

from ddo_pulse_db.datetime_util import digest_calendar_date_today


def digest_date_today() -> str:
    return digest_calendar_date_today()


def _parse_categories(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x) for x in data]
    except json.JSONDecodeError:
        pass
    return []


def build_markdown_body(date: str, rows: list[Any]) -> str:
    lines = [f"# Ddo-Pulse 精选 · {date}", ""]
    if not rows:
        lines.append("_今日暂无达到阈值的精选文章。_")
        return "\n".join(lines)

    for idx, row in enumerate(rows, start=1):
        title = row["title"] or row["url"]
        url = row["url"]
        score = row["score"]
        cats = "、".join(_parse_categories(row["categories_json"])) or "未分类"
        summary = (row["summary_zh"] or "").strip()
        reason = (row["reason"] or "").strip()
        lines.append(f"## {idx}. [{title}]({url})")
        lines.append(f"**{score} 分** · {cats}")
        if summary:
            lines.append("")
            lines.append(summary)
        if reason:
            lines.append("")
            lines.append(f"> {reason}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def item_ids_from_rows(rows: list[Any]) -> list[int]:
    return [int(r["id"]) for r in rows]
