"""报告提示词模板（含深度解读）。"""

from __future__ import annotations

DEEP_ANALYSIS_PROMPT = """你是一位资深技术内容分析师。请对以下文章进行深度解读。

文章标题：{title}
文章内容：{content}

请输出 JSON 格式（字段名必须一致）：
{{
  "core_content": "文章核心内容的 200-300 字总结",
  "key_points": [
    "关键观点1",
    "关键观点2",
    "关键观点3"
  ],
  "insights": "文章的思路梳理和启发性内容"
}}

要求：
- core_content：概括文章的主要内容和结论，让读者快速了解文章核心
- key_points：提取 3-5 个关键观点或技术要点，每个要点简洁明了
- insights：梳理文章的逻辑思路，提炼对读者有启发性的内容"""
