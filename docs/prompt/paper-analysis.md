# 论文分析 Prompt 设计

## 概述

论文分析 prompt 用于评估学术论文的质量与价值，生成结构化摘要。支持两种参数输入方式：

| 模式 | 适用场景 | 原理 |
|------|----------|------|
| **参数配置** | 精确控制、批量任务 | 直接传入结构化参数 |
| **自然语言** | 快速定义、灵活调整 | LLM 从描述中自动提取参数 |

两种模式最终都会生成相同的 prompt 结果，区别仅在于参数的来源方式。

---

## 参数清单

以下是论文分析 prompt 支持的全部参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `domain_focus` | string | 否 | `"计算机科学与人工智能"` | 研究领域，影响评审视角和分类标签 |
| `paper_type` | string | 否 | `"预印本论文"` | 论文类型（预印本/会议论文/期刊论文/综述等） |
| `categories_hint` | string[] | 否 | `["AI", "LLM", "NLP", "CV", "ML", "系统", "安全", "数据库", "其他"]` | 可选分类标签列表 |
| `interest_keywords` | string[] | 否 | `[]` | 读者关注的关键词，引导摘要侧重方向 |
| `scoring_rubric` | string | 否 | 见下方默认值 | 自定义评分标准描述 |
| `score_threshold` | int | 否 | `7` | `is_quality = true` 的最低分（1-10） |

### 默认评分标准

```
评分标准：1-10 分；9-10 里程碑式工作，7-8 高质量论文，5-6 一般质量，3-4 质量较低。
is_quality 为 true 表示 score >= 阈值（默认 7），值得收录。
评分维度参考：创新性(30%)、方法论(25%)、实验质量(20%)、实用价值(15%)、写作质量(10%)。
```

---

## 模式一：参数配置

通过 pipeline_jobs 的字段直接传入结构化参数。系统在构建 prompt 时，将这些参数注入模板的对应占位符。

### 配置途径

#### API（推荐）

```json
POST /api/jobs
{
  "name": "arxiv-ai-papers",
  "prompt_template": "<PAPER_PROMPT_TEMPLATE>",
  "system_prompt": "<PAPER_SYSTEM_PROMPT>",
  "scoring_rubric": "<PAPER_SCORING_RUBRIC>",
  "interest_keywords_json": "[\"大语言模型\", \"多模态\", \"Agent\"]",
  "score_threshold": 7,
  "llm_profile_id": 1
}
```

> `prompt_template` 和 `system_prompt` 的完整内容见下方 [Prompt 模板](#prompt-模板) 章节。

#### YAML 配置

```yaml
# ~/.ddo_pulse/config.yaml
llm:
  profiles:
    - name: paper-analyzer
      model: anthropic/claude-sonnet-4-20250514
      prompt_template: |
        <完整 PAPER_PROMPT_TEMPLATE 内容>
      system_prompt: |
        <完整 PAPER_SYSTEM_PROMPT 内容>
```

#### 数据库直接修改

```sql
UPDATE pipeline_jobs
SET
  prompt_template = '<PAPER_PROMPT_TEMPLATE>',
  system_prompt = '<PAPER_SYSTEM_PROMPT>',
  scoring_rubric = '<PAPER_SCORING_RUBRIC>',
  interest_keywords_json = '["大语言模型", "多模态"]'
WHERE name = 'arxiv-ai-papers';
```

### 参数注入流程

```
pipeline_jobs / llm_profiles 配置
        ↓
build_effective_profile()  ← 合并 job 级覆盖 + profile 默认值
        ↓
OpenRouterAnalyzer._build_prompt()
        ↓
format_prompt_template(template, **fields)  ← 仅替换模板中存在的占位符
        ↓
最终 prompt → LLM
```

`format_prompt_template()` 使用 Python `string.Formatter`，自动跳过模板中不存在的占位符，因此自定义模板可以省略任意参数。

---

## 模式二：自然语言自动解析

用户用一段自然语言描述分析需求，系统通过 LLM 自动提取结构化参数，再注入 prompt 模板。

### 使用方式

在 pipeline_jobs 中配置 `natural_language_prompt` 字段（待实现）：

```json
{
  "name": "arxiv-ai-papers",
  "natural_language_prompt": "分析 AI 领域的预印本论文，重点关注大语言模型和多模态方向，对工程实践类论文适当加分",
  "score_threshold": 7
}
```

### 参数提取 Prompt

系统使用以下 prompt 将自然语言描述解析为结构化参数：

```
你是一个配置解析器。请从用户的分析需求描述中提取以下参数，输出一个合法 JSON 对象。

## 可提取参数

| 参数 | 类型 | 说明 | 缺省值 |
|------|------|------|--------|
| domain_focus | string | 研究领域 | "计算机科学与人工智能" |
| paper_type | string | 论文类型 | "预印本论文" |
| categories_hint | string[] | 分类标签 | ["AI","LLM","NLP","CV","ML","系统","安全","数据库","其他"] |
| interest_keywords | string[] | 关注的关键词/主题 | [] |
| scoring_rubric | string | 评分标准描述（仅在用户有特殊要求时生成） | null |

## 输出格式

仅输出 JSON，不要有其他文字：
{
  "domain_focus": "...",
  "paper_type": "...",
  "categories_hint": ["..."],
  "interest_keywords": ["..."],
  "scoring_rubric": "..." 或 null
}

## 用户描述

{user_description}
```

### 解析示例

**输入**：`"分析 AI 领域的预印本论文，重点关注大语言模型和多模态方向，对工程实践类论文适当加分"`

**输出**：
```json
{
  "domain_focus": "人工智能",
  "paper_type": "预印本论文",
  "categories_hint": ["AI", "LLM", "NLP", "CV"],
  "interest_keywords": ["大语言模型", "多模态", "工程实践"],
  "scoring_rubric": null
}
```

**输入**：`"我关注数据库和分布式系统方向的顶会论文，希望看到 Raft/Paxos 一致性协议相关的工作"`

**输出**：
```json
{
  "domain_focus": "数据库与分布式系统",
  "paper_type": "会议论文",
  "categories_hint": ["数据库", "分布式", "系统"],
  "interest_keywords": ["Raft", "Paxos", "一致性协议", "分布式共识"],
  "scoring_rubric": null
}
```

### 集成流程（待实现）

```
natural_language_prompt
        ↓
PAPER_PARAM_EXTRACT_PROMPT  ← LLM 调用（低温度、短输出）
        ↓
解析出的结构化参数 JSON
        ↓
合并到 build_effective_profile() 的 profile dict
        ↓
后续流程与模式一相同
```

代码层面的改动点：
- `pipeline_jobs` 表新增 `natural_language_prompt` 字段
- `pipeline.py` 的 `build_effective_profile()` 中新增参数提取逻辑
- 参数提取结果缓存（同一 job 只需提取一次，直到 `natural_language_prompt` 变更）

---

## Prompt 模板

### System Prompt

```
你是一位资深学术论文评审专家，擅长快速评估论文的研究价值与创新贡献。

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
- 字符串内若有双引号须写成 \"
- 所有中文字段使用中文
```

### User Prompt

```
请分析以下论文信息，判断其学术价值。

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

{
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
}

## 字段说明

### 核心字段
- `is_quality` (bool): score >= 阈值时为 true
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
```

### 评分标准

```
评分标准：1-10 分；9-10 里程碑式工作，7-8 高质量论文，5-6 一般质量，3-4 质量较低。
is_quality 为 true 表示 score >= 阈值（默认 7），值得收录。
评分维度参考：创新性(30%)、方法论(25%)、实验质量(20%)、实用价值(15%)、写作质量(10%)。
```

---

## 数据来源参考

LLM 会根据论文内容推断来源，以下为参考：

| 来源 | 类型 | 覆盖领域 |
|------|------|----------|
| arXiv | 预印本 | AI/CS/数学/物理等 |
| Semantic Scholar | 聚合 | 跨学科 |
| Papers With Code | 聚合 | AI/ML（带代码） |
| ACL Anthology | 会议/期刊 | NLP/计算语言学 |
| IEEE Xplore | 期刊/会议 | 电子/计算机/通信 |
| PubMed | 期刊 | 生物医学 |
| SSRN | 预印本 | 社科/经济/法律 |

---

## 与现有 Pipeline 的兼容性

- 论文专属字段（novelty、methodology 等）是**扩展字段**，不影响现有 `AnalysisOutput` 的 JSON 解析
- `parse_analysis_json()` 通过 `AnalysisOutput.model_validate(data)` 只读取 5 个核心字段，扩展字段被安全忽略
- 如果后续需要持久化扩展字段，需在 `analyzed_items` 表新增列并扩展 `AnalysisOutput` 模型
