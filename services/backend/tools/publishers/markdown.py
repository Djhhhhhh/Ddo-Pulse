"""Markdown 报告生成器。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List


def _parse_categories(raw: str | None) -> List[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x) for x in data]
    except json.JSONDecodeError:
        pass
    return []


def generate_digest_md(
    date: str,
    articles: List[Any],
    output_path: Path
) -> Path:
    """生成公众号友好的 MD 报告"""
    lines = [f"# Ddo-Pulse 每日资讯速递 · {date}", ""]

    if not articles:
        lines.append("_今日暂无达到阈值的精选文章。_")
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    lines.append(f"> 共 {len(articles)} 篇精选")
    lines.append("")

    for idx, row in enumerate(articles, 1):
        title = row.get("title") or row.get("url", "")
        url = row.get("url", "")
        categories = row.get("categories", [])
        if isinstance(categories, str):
            categories = _parse_categories(categories)
        cats = "、".join(categories) or "未分类"
        summary = (row.get("summary_zh") or "").strip()
        reason = (row.get("reason") or "").strip()
        deep_analysis = row.get("deep_analysis", {})

        # 标题与元信息
        lines.append(f"## {idx}. [{title}]({url})")
        lines.append("")
        lines.append(f"Tags：{cats}")
        lines.append("")

        # 摘要
        if summary:
            lines.append(summary)
            lines.append("")

        # 推荐理由
        if reason:
            lines.append(f"> 💬 {reason}")
            lines.append("")

        # 深度解读
        if deep_analysis:
            core_content = deep_analysis.get("core_content", "")
            key_points = deep_analysis.get("key_points", [])
            insights = deep_analysis.get("insights", "")

            if core_content or key_points or insights:
                lines.append("**📖 深度解读**")
                lines.append("")

            if core_content:
                lines.append(core_content)
                lines.append("")

            if key_points:
                for point in key_points:
                    lines.append(f"- {point}")
                lines.append("")

            if insights:
                lines.append(f"💡 {insights}")
                lines.append("")

        if idx < len(articles):
            lines.append("---")
            lines.append("")

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output_path
