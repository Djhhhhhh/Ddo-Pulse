"""策展提示词模板。"""

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

# ---------------------------------------------------------------------------
# 论文分析 Prompt 模板
# ---------------------------------------------------------------------------

PAPER_SYSTEM_PROMPT = """你是一位资深学术论文评审专家，擅长快速评估论文的研究价值与创新贡献。

你的职责：
1. 判断论文是否值得深入阅读
2. 评估论文的创新性、方法论严谨性和实用价值
3. 生成简洁准确的中文摘要

评审原则：
- 以客观、专业的学术标准评判
- 重点关注{domain_focus}领域的核心问题与前沿进展
- 兼顾理论贡献与实践意义
- 对{paper_type}采用相应的评审侧重

输出要求：
- 仅输出一个合法 JSON 对象（不要用 markdown 代码块）
- 字符串内若有双引号须写成 \\"
- 所有中文字段使用中文"""

PAPER_PROMPT_TEMPLATE = """请分析以下论文信息，判断其学术价值。

## 研究领域
{domain_focus}

## 论文类型
{paper_type}

## 可用分类标签
{categories_hint}

## 读者研究兴趣
{interest_keywords}

## 论文信息

**标题**：{title}

**内容**：
{content}

## 评分标准
{scoring_rubric}

## 输出格式

请输出以下 JSON 结构（字段名必须一致）：

{{
  "is_quality": true,
  "score": 8,
  "categories": ["标签1", "标签2"],
  "summary_zh": "50-120字中文摘要（严禁超过120字，宁可短）",
  "reason": "一句话说明评分理由（简短）",
  "novelty": "high",
  "methodology": "一句话概括研究方法",
  "key_findings": [
    "核心发现1",
    "核心发现2"
  ],
  "limitations": [
    "主要局限1"
  ],
  "practical_value": "high",
  "source": "arXiv",
  "source_url": "",
  "source_type": "preprint"
}}

## 字段说明

### 核心字段
- `is_quality` (bool): score >= 7 时为 true
- `score` (int, 1-10): 综合质量评分
- `categories` (string[]): 从可用分类标签中选择 0-3 个
- `summary_zh` (string): 50-120字中文摘要
- `reason` (string): 一句话评分理由

### 论文专属字段
- `novelty`: "high"（全新方法/发现）/ "medium"（改进或新视角）/ "low"（增量改进）
- `methodology`: 一句话概括研究方法
- `key_findings`: 1-3条核心发现
- `limitations`: 1-2条主要局限
- `practical_value`: "high"（可直接落地）/ "medium"（有潜力）/ "low"（纯理论）
- `source`: 论文来源（如 "arXiv"、"Semantic Scholar"、"ACL Anthology"）
- `source_url`: 原文链接
- `source_type`: "preprint" / "journal" / "conference" / "tech_report" / "thesis"

## 数据来源参考

| 来源 | 类型 | 覆盖领域 |
|------|------|----------|
| arXiv | 预印本 | AI/CS/数学/物理等 |
| Semantic Scholar | 聚合 | 跨学科 |
| Papers With Code | 聚合 | AI/ML（带代码） |
| ACL Anthology | 会议/期刊 | NLP/计算语言学 |
| IEEE Xplore | 期刊/会议 | 电子/计算机/通信 |
| PubMed | 期刊 | 生物医学 |
| SSRN | 预印本 | 社科/经济/法律 |

根据论文内容判断其最可能的来源并标注。"""

PAPER_SCORING_RUBRIC = (
    "评分标准：1-10 分；9-10 里程碑式工作，7-8 高质量论文，5-6 一般质量，3-4 质量较低。"
    "is_quality 为 true 表示 score >= 7，值得收录。"
    "评分维度参考：创新性(30%)、方法论(25%)、实验质量(20%)、实用价值(15%)、写作质量(10%)。"
)


def format_prompt_template(template: str, **fields: str) -> str:
    """Only substitute placeholders present in *template*."""
    used = {fn for _, fn, _, _ in Formatter().parse(template) if fn is not None}
    args = {k: v for k, v in fields.items() if k in used}
    return template.format(**args)
