# Prompt 模板库

本目录存放 ddo-pulse 项目使用的 LLM 分析 prompt 模板。

---

## 目录结构

```
docs/prompt/
├── paper-analysis.md          # 通用论文分析 prompt（主模板）
├── paper-analysis-variants/   # 论文分析变体（按领域/类型定制）
│   ├── ai-research.md         # AI/CS 研究论文变体（待创建）
│   ├── survey-paper.md        # 综述论文变体（待创建）
│   └── tech-report.md         # 技术报告变体（待创建）
├── arxiv-rss-setup.md         # arXiv RSS 论文抓取快速配置指南
└── README.md                  # 本文件
```

---

## 快速开始

如果你的目标是抓取和分析 arXiv 论文，请直接查看 **[arXiv RSS 快速配置指南](arxiv-rss-setup.md)**，包含：
- arXiv RSS 源列表（AI、ML、NLP、CV 等方向）
- CLI/API/Web 三种添加源的方式
- 论文分析 Prompt 配置步骤
- 验证方法

---

## 使用指南

### 1. 集成到 ddo-pulse pipeline

在 pipeline job 或 LLM profile 中配置以下字段：

| 字段 | 说明 |
|------|------|
| `prompt_template` | 用户消息模板，包含 `{placeholder}` 占位符 |
| `system_prompt` | 系统消息，定义 LLM 角色和行为 |
| `scoring_rubric` | 评分标准文本 |

配置路径：
- **Pipeline Job**: `POST /api/pipeline-jobs` 或 Web Dashboard → Pipeline 管理
- **LLM Profile**: `PUT /api/profiles/{id}` 或 Web Dashboard → 配置管理

### 2. 手动使用

1. 从模板文件中复制 System Prompt 和 User Prompt
2. 替换所有 `{placeholder}` 为实际值
3. 粘贴到任意 LLM 对话中使用

### 3. 创建自定义变体

基于 `paper-analysis.md` 创建变体时：
- 修改 `{domain_focus}` 和 `{paper_type}` 适配目标领域
- 调整评分标准侧重点
- 增减来源列表
- 保持 JSON 输出格式不变，确保兼容性

---

## 占位符参考

| 占位符 | 必填 | 说明 |
|--------|------|------|
| `{title}` | 是 | 论文标题 |
| `{content}` | 是 | 摘要或正文内容 |
| `{categories_hint}` | 是 | 可选分类标签列表 |
| `{interest_keywords}` | 是 | 读者关注的关键词/主题 |
| `{scoring_rubric}` | 是 | 评分标准描述 |
| `{domain_focus}` | 是 | 研究领域描述 |
| `{paper_type}` | 是 | 论文类型（研究论文/综述/技术报告等） |
| `{sources}` | 否 | 可用论文来源列表 |

> **注意**：`format_prompt_template()` 函数会自动忽略模板中不存在的占位符，因此自定义模板可以省略不需要的字段。

---

## 输出 Schema

### 核心字段（兼容 AnalysisOutput）

| 字段 | 类型 | 说明 |
|------|------|------|
| `is_quality` | bool | 是否值得收录 |
| `score` | int (1-10) | 综合质量评分 |
| `categories` | string[] | 分类标签（0-3个） |
| `summary_zh` | string | 50-120字中文摘要 |
| `reason` | string | 一句话评分理由 |

### 论文专属扩展字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `novelty` | "high"/"medium"/"low" | 创新性评级 |
| `methodology` | string | 研究方法概述 |
| `key_findings` | string[] | 核心发现（1-3条） |
| `limitations` | string[] | 主要局限（1-2条） |
| `practical_value` | "high"/"medium"/"low" | 实用价值评级 |
| `source` | string | 论文来源 |
| `source_url` | string | 原文链接 |
| `source_type` | string | 来源类型 |

> 扩展字段不影响现有 pipeline 的 JSON 解析，可安全忽略。

---

## 评分标准参考

### 默认论文评分标准

```
评分标准：1-10 分
- 9-10: 里程碑式工作，必读
- 7-8:  高质量论文，值得深入阅读
- 5-6:  一般质量，可选择性阅读
- 3-4:  质量较低，不推荐
- 1-2:  质量很差，不收录
is_quality 为 true 表示 score >= 7，值得收录。
```

### 各维度权重建议

| 维度 | 权重 | 说明 |
|------|------|------|
| 创新性 | 30% | 新方法/新发现/新视角 |
| 方法论 | 25% | 研究设计的严谨性 |
| 实验质量 | 20% | 实验充分性与可复现性 |
| 实用价值 | 15% | 落地潜力与应用场景 |
| 写作质量 | 10% | 表达清晰度与组织性 |
