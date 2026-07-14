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
    lines = [f"# Ddo-Pulse 精选 · {date}", ""]

    if not articles:
        lines.append("_今日暂无达到阈值的精选文章。_")
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    for idx, row in enumerate(articles, 1):
        title = row.get("title") or row.get("url", "")
        url = row.get("url", "")
        score = row.get("score", 0)
        categories = row.get("categories", [])
        if isinstance(categories, str):
            categories = _parse_categories(categories)
        cats = "、".join(categories) or "未分类"
        summary = (row.get("summary_zh") or "").strip()
        reason = (row.get("reason") or "").strip()
        deep_analysis = row.get("deep_analysis", {})

        lines.append(f"## {idx}. [{title}]({url})")
        lines.append(f"**{score} 分** · {cats}")

        if summary:
            lines.append("")
            lines.append(summary)

        if reason:
            lines.append("")
            lines.append(f"> {reason}")

        # 深度解读
        if deep_analysis:
            lines.append("")
            lines.append("### 📖 深度解读")

            core_content = deep_analysis.get("core_content", "")
            if core_content:
                lines.append("")
                lines.append(core_content)

            key_points = deep_analysis.get("key_points", [])
            if key_points:
                lines.append("")
                lines.append("**核心要点：**")
                for point in key_points:
                    lines.append(f"- {point}")

            insights = deep_analysis.get("insights", "")
            if insights:
                lines.append("")
                lines.append(f"**💡 思路启发：** {insights}")

        lines.append("")
        lines.append("---")
        lines.append("")

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output_path
