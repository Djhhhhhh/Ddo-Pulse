"""Default LLM analysis prompt template."""

from __future__ import annotations

from string import Formatter

DEFAULT_PROMPT_TEMPLATE = """你是一位中文技术博客策展编辑。请阅读以下文章信息，判断是否值得推荐给中文读者，并输出**仅包含一个合法 JSON 对象**（不要用 markdown 代码块；字符串内若有双引号须写成 \\"）。

可选分类标签（从中选择 0-3 个最贴切的）：{categories_hint}

读者关注的关键词或主题（可参考，不必逐字命中）：{interest_keywords}

文章标题：{title}

正文摘要：
{content}

输出 JSON 格式（字段名必须一致）：
{{
  "is_quality": true,
  "score": 8,
  "categories": ["AI"],
  "summary_zh": "50-120 字中文摘要（严禁超过 120 字，宁可短）",
  "reason": "一句话说明评分理由（简短）"
}}

{scoring_rubric}"""

DEFAULT_SCORING_RUBRIC = (
    "评分标准：1-10 分；7 分及以上表示质量较好。is_quality 为 true 表示值得收录。"
)


def format_prompt_template(template: str, **fields: str) -> str:
    """Only substitute placeholders present in *template* (custom templates may omit some)."""
    used = {fn for _, fn, _, _ in Formatter().parse(template) if fn is not None}
    args = {k: v for k, v in fields.items() if k in used}
    return template.format(**args)
