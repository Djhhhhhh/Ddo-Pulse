"""Format analyzed_items for CLI output."""

from __future__ import annotations

import json
from typing import Any

import typer


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


def analyzed_row_to_dict(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "raw_item_id": row["raw_item_id"],
        "title": row["title"],
        "url": row["url"],
        "source_id": row["source_id"],
        "is_quality": bool(row["is_quality"]),
        "score": row["score"],
        "categories": _parse_categories(row["categories_json"]),
        "summary_zh": row["summary_zh"],
        "reason": row["reason"],
        "analyzed_at": row["analyzed_at"],
        "published_at": row["published_at"],
    }


def print_analyzed_list(rows: list[Any], *, as_json: bool = False) -> None:
    if not rows:
        typer.echo("No analyzed items.")
        return
    if as_json:
        typer.echo(json.dumps([analyzed_row_to_dict(r) for r in rows], ensure_ascii=False, indent=2))
        return

    typer.echo(f"{'ID':<5} {'SC':<3} {'Q':<2} {'TITLE':<36} CATEGORIES")
    for r in rows:
        q = "Y" if r["is_quality"] else "N"
        cats = ",".join(_parse_categories(r["categories_json"]))[:24]
        title = (r["title"] or r["url"] or "")[:36]
        typer.echo(f"{r['id']:<5} {r['score']:<3} {q:<2} {title:<36} {cats}")


def print_analyzed_detail(row: Any, *, as_json: bool = False) -> None:
    if as_json:
        typer.echo(json.dumps(analyzed_row_to_dict(row), ensure_ascii=False, indent=2))
        return

    cats = ", ".join(_parse_categories(row["categories_json"])) or "(none)"
    quality = "是" if row["is_quality"] else "否"
    typer.echo(f"ID:          {row['id']} (raw_item_id={row['raw_item_id']})")
    typer.echo(f"标题:        {row['title']}")
    typer.echo(f"链接:        {row['url']}")
    typer.echo(f"评分:        {row['score']}/10  精选: {quality}")
    typer.echo(f"分类:        {cats}")
    typer.echo(f"分析时间:    {row['analyzed_at']}")
    if row["published_at"]:
        typer.echo(f"发布时间:    {row['published_at']}")
    typer.echo(f"中文摘要:\n  {row['summary_zh']}")
    typer.echo(f"理由:\n  {row['reason']}")
