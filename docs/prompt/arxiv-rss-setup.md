# arXiv RSS 论文抓取快速配置指南

> 通过现有 RSS 源类型 + 论文分析 Prompt，快速实现论文抓取与分析。

---

## 第一步：添加 arXiv RSS 源

### CLI 方式

```bash
# AI 领域
ddo-pulse source add "arXiv-AI" rss "http://export.arxiv.org/rss/cs.AI"

# 机器学习
ddo-pulse source add "arXiv-ML" rss "http://export.arxiv.org/rss/cs.LG"

# 自然语言处理
ddo-pulse source add "arXiv-NLP" rss "http://export.arxiv.org/rss/cs.CL"

# 计算机视觉
ddo-pulse source add "arXiv-CV" rss "http://export.arxiv.org/rss/cs.CV"

# 信息检索
ddo-pulse source add "arXiv-IR" rss "http://export.arxiv.org/rss/cs.IR"
```

### API 方式

```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "name": "arXiv-AI",
    "type": "rss",
    "url": "http://export.arxiv.org/rss/cs.AI"
  }'
```

### Web Dashboard

进入 **配置管理 → 订阅源 → 添加源**，填写：
- 名称：`arXiv-AI`
- 类型：`rss`
- URL：`http://export.arxiv.org/rss/cs.AI`

---

## 第二步：配置论文分析 Prompt

### 方式一：Web Dashboard（推荐）

进入 **配置管理 → 定时任务 → 编辑**，填写以下字段：

#### System Prompt

```
你是一位资深学术论文评审专家，擅长快速评估论文的研究价值与创新贡献。

你的职责：
1. 判断论文是否值得深入阅读
2. 评估论文的创新性、方法论严谨性和实用价值
3. 生成简洁准确的中文摘要

评审原则：
- 以客观、专业的学术标准评判
- 重点关注人工智能与机器学习领域的核心问题与前沿进展
- 兼顾理论贡献与实践意义

输出要求：
- 仅输出一个合法 JSON 对象（不要用 markdown 代码块）
- 字符串内若有双引号须写成 \"
- 所有中文字段使用中文
```

#### Prompt Template

```
请分析以下论文信息，判断其学术价值。

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
  "categories": ["标签1"],
  "summary_zh": "50-120字中文摘要（严禁超过120字）",
  "reason": "一句话评分理由",
  "novelty": "high",
  "methodology": "一句话概括研究方法",
  "key_findings": ["核心发现1"],
  "limitations": ["主要局限1"],
  "practical_value": "high",
  "source": "arXiv",
  "source_url": "",
  "source_type": "preprint"
}}

## 字段说明
- novelty: "high"/"medium"/"low"
- practical_value: "high"/"medium"/"low"
- key_findings: 1-3条
- limitations: 1-2条
```

#### Scoring Rubric

```
评分标准：1-10 分；9-10 里程碑式工作，7-8 高质量论文，5-6 一般质量，3-4 质量较低。
is_quality 为 true 表示 score >= 7，值得收录。
评分维度参考：创新性(30%)、方法论(25%)、实验质量(20%)、实用价值(15%)、写作质量(10%)。
```

### 方式二：API

```bash
curl -X PUT http://localhost:8000/api/pipeline-jobs/1 \
  -H "Content-Type: application/json" \
  -d '{
    "system_prompt": "...(上方 System Prompt 内容)...",
    "prompt_template": "...(上方 Prompt Template 内容)...",
    "scoring_rubric": "...(上方 Scoring Rubric 内容)..."
  }'
```

---

## 第三步：验证

### 测试抓取

```bash
# CLI
ddo-pulse run-once --skip-analyze --skip-push

# 或仅抓取并分析
ddo-pulse run-once --skip-push
```

### API 测试

```bash
curl -X POST http://localhost:8000/api/run-once \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_job_id": 1,
    "analyze_limit": 5,
    "skip_push": true
  }'
```

---

## arXiv RSS 源完整列表

### Computer Science

| 子领域 | RSS URL |
|--------|---------|
| 人工智能 | `http://export.arxiv.org/rss/cs.AI` |
| 计算语言学 | `http://export.arxiv.org/rss/cs.CL` |
| 计算机视觉 | `http://export.arxiv.org/rss/cs.CV` |
| 机器学习 | `http://export.arxiv.org/rss/cs.LG` |
| 信息检索 | `http://export.arxiv.org/rss/cs.IR` |
| 数据库 | `http://export.arxiv.org/rss/cs.DB` |
| 分布式计算 | `http://export.arxiv.org/rss/cs.DC` |
| 网络 | `http://export.arxiv.org/rss/cs.NI` |
| 编程语言 | `http://export.arxiv.org/rss/cs.PL` |
| 软件工程 | `http://export.arxiv.org/rss/cs.SE` |
| 系统 | `http://export.arxiv.org/rss/cs.OS` |
| 密码学 | `http://export.arxiv.org/rss/cs.CR` |

### 其他领域

| 领域 | RSS URL |
|------|---------|
| 统计学-机器学习 | `http://export.arxiv.org/rss/stat.ML` |
| 数学-优化 | `http://export.arxiv.org/rss/math.OC` |
| 物理-计算 | `http://export.arxiv.org/rss/physics.comp-ph` |
| 定量生物学 | `http://export.arxiv.org/rss/q-bio.QM` |

---

## 注意事项

1. **内容限制**：RSS 源只提供标题和摘要片段（约 200-500 字），不包含全文。对于论文分析来说，摘要通常足够评估质量和创新性。

2. **更新频率**：arXiv RSS 每天更新一次，建议将 pipeline cron 设置为每天运行一次（如 `0 9 * * *`）。

3. **分类标签**：建议在 pipeline job 的 `interest_keywords` 中配置你关注的研究方向，如 `["LLM", "transformer", "reinforcement learning"]`。

4. **扩展字段**：当前 `AnalysisOutput` 模型只解析 5 个核心字段，论文专属字段（`novelty`、`methodology` 等）会被忽略。如需持久化这些字段，需要扩展模型。
