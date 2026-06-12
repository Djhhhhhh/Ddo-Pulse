# Ddo-Pulse 前端简化 Specification

> AI 基于 `requirement.md` 与 `context-summary.md` 对需求的规约化理解。
> 仅描述 What / Why 与验收标准；技术方案见 `plan.md`。
> 用户确认本 spec 是否符合预期后，方可进入下一阶段（Planning）。

---

## 1. 项目概述

### 1.1 项目名称
Ddo-Pulse 前端配置简化

### 1.2 一句话定义
简化 SettingsView 中「模型与密钥」和「定时任务创建/编辑」表单，去除冗余字段，提升可用性。

### 1.3 设计意图
- 降低用户配置门槛：去除不常用或易混淆的字段（阈值、模型 Profile）
- 强化必填项引导：抓取与 Digest 从可选折叠区提升为必填默认配置
- 提升提示词体验：从自由文本编辑改为「系统模板 + 用户需求」的组合模式
- 保持灵活性：保留多定时任务、cron、Webhook、关键词预过滤等核心能力

---

## 2. 术语表（Glossary）

| 术语 | 定义 |
|---|---|
| pipeline_job | 定时任务实体，包含 cron、webhook、抓取配置、提示词等 |
| llm_profile | LLM 模型配置，包含 model、api_key 等 |
| scoring_rubric | 评分侧重点，系统预设的评分标准模板 |
| prompt_template | 分析文章时使用的提示词模板 |
| system_prompt | LLM 系统级提示词 |
| user_prompt | 用户自定义的需求描述文本，与系统 prompt 组合使用 |

---

## 3. 功能需求（Functional Requirements）

### 3.1 模型与密钥（LLM Profiles）

- **FR-LLM-1**：LLM 配置页面仅展示和编辑 `model` 字段和 `api_key` 字段
- **FR-LLM-2**：移除 temperature、max_tokens、score_threshold、category_hints、prompt_template、system_prompt 等高级字段的前端编辑入口
- **FR-LLM-3**：model 和 api_key 仍为可编辑状态，api_key 使用密码输入框

### 3.2 定时任务管理

- **FR-JOB-1**：保留定时任务列表页面，支持创建多个定时任务
- **FR-JOB-2**：每个定时任务同一时间只允许运行一个任务（并发控制）
- **FR-JOB-3**：保留定时任务的启用/禁用开关

### 3.3 定时任务创建/编辑表单

#### 3.3.1 保留字段
- **FR-FORM-1**：保留 cron 表达式输入，含格式帮助提示
- **FR-FORM-2**：保留飞书 Webhook URL 输入（必填）

#### 3.3.2 删除字段
- **FR-FORM-3**：删除「阈值（score_threshold）」字段的前端输入

#### 3.3.3 评分侧重点（scoring_rubric）
- **FR-FORM-4**：评分侧重点改为只读预览模式，不允许用户修改
- **FR-FORM-5**：系统提供预设的评分模板（balanced、tech_depth、timely），用户可切换查看不同模板的预览内容
- **FR-FORM-6**：默认使用 `balanced` 模板

#### 3.3.4 抓取与 Digest（必填）
- **FR-FORM-7**：「抓取与 Digest」从可选折叠区提升为**必填区域**，默认展开
- **FR-FORM-8**：包含字段：analyze_limit（分析数量上限）、digest_top_n（Digest 精选数量）、push_digest（是否推送）
- **FR-FORM-9**：提供合理默认值（analyze_limit=50, digest_top_n=10, push_digest=true）

#### 3.3.5 模型 Profile
- **FR-FORM-10**：移除「模型 Profile」选择区域，定时任务不再关联 llm_profile_id

#### 3.3.6 关键词与预过滤
- **FR-FORM-11**：保留「关键词与预过滤」可选折叠区
- **FR-FORM-12**：保留 keyword_prefilter 开关和 interest_keywords 文本输入

#### 3.3.7 高级提示词
- **FR-FORM-13**：「高级提示词」改为「提示词配置」区域
- **FR-FORM-14**：提供系统预设的提示词模板列表，用户可选择并预览
- **FR-FORM-15**：提供「用户需求」文本输入框，让用户用自然语言描述自己的需求
- **FR-FORM-16**：最终提示词 = 系统 prompt 模板 + 用户需求 prompt，组合后发送给 LLM
- **FR-FORM-17**：用户可预览最终组合后的完整提示词

### 3.4 定时任务运行约束

- **FR-RUN-1**：每个定时任务同一时刻只允许运行一个实例，若上一次运行未结束则跳过或排队

---

## 4. 产物与目录结构（What gets created）

```
services/web/frontend/src/
  views/
    SettingsView.vue          # 主要修改：简化表单
  api/
    client.ts                 # 更新 PipelineJob 接口（移除 llm_profile_id 等）
  components/
    PromptTemplateSelector.vue  # 新增：提示词模板选择与预览组件
    ScoringRubricPreview.vue    # 新增：评分侧重点只读预览组件
services/backend/
  api/ddo_pulse_api/
    schemas.py                # 更新 Pydantic schema
    api_routes.py             # 更新 API 路由（如有需要）
  core/ddo_pulse_core/
    analyzer/prompt.py        # 更新：系统提示词模板管理
```

---

## 5. 关键流程

```
用户打开 Settings 页面
├── 「模型与密钥」Tab
│   └── 仅显示 model + api_key 编辑
│
└── 「定时任务」Tab
    ├── 任务列表（可创建多个）
    └── 新建/编辑任务
        ├── [必填] 任务名称
        ├── [必填] Cron 表达式
        ├── [必填] 飞书 Webhook URL
        ├── [必填] 抓取与 Digest 配置（默认值已填）
        ├── [预览] 评分侧重点（只读，可切换模板查看）
        ├── [可选] 关键词与预过滤
        └── [配置] 提示词
            ├── 选择系统模板（可预览）
            ├── 输入用户需求描述
            └── 预览最终组合提示词
```

---

## 6. 约束与原则

- **C-1**：不修改数据库 schema，仅调整前端展示逻辑（后端字段保留但前端不暴露）
- **C-2**：评分侧重点的预设模板硬编码在前端或后端常量中，不允许用户自由编辑
- **C-3**：每个定时任务同一时刻只能运行一个实例
- **C-4**：提示词组合逻辑在后端 pipeline 中实现，前端仅负责展示和输入

---

## 7. 验收标准（Acceptance Criteria）

> spec 层的高层验收点，后续在 `test-plan.md` 中细化为 checklist。

- **AC-1**：模型与密钥页面仅展示 model 和 api_key 两个可编辑字段
- **AC-2**：定时任务创建表单中无「阈值」字段
- **AC-3**：评分侧重点区域为只读预览，用户可切换查看不同模板但不能编辑
- **AC-4**：抓取与 Digest 区域默认展开且字段有默认值
- **AC-5**：无「模型 Profile」选择区域
- **AC-6**：提示词区域提供系统模板选择 + 用户需求输入 + 最终预览
- **AC-7**：每个定时任务同一时刻只运行一个实例
- **AC-8**：所有原有功能（多任务创建、cron、webhook、关键词预过滤）正常保留

---

## 8. 非功能需求（Non-Functional）

- **NFR-1**：前端改动不影响已有 API 的向后兼容性
- **NFR-2**：表单简化后，新建任务的操作步骤不超过 5 步

---

## 9. 范围说明（In / Out of Scope）

### In Scope
- SettingsView 前端表单简化
- 提示词模板选择与预览组件
- 评分侧重点只读预览组件
- 定时任务并发运行控制
- API client 类型更新

### Out of Scope
- 数据库 schema 迁移
- Dashboard / Articles 页面改动
- 后端 pipeline 核心逻辑重构
- 用户认证系统

---

## 10. 开放问题（Open Questions，待 Plan 阶段决策）

- **Q-1**：评分侧重点的预设模板是硬编码在前端 JS 中还是后端提供 API？—— 留给 `plan.md`。
- **Q-2**：提示词系统模板列表从哪里获取（前端硬编码 vs 后端 API）？—— 留给 `plan.md`。
- **Q-3**：移除 llm_profile_id 关联后，pipeline 如何确定使用哪个模型？是否使用默认 profile？—— 留给 `plan.md`。
- **Q-4**：定时任务并发控制的实现方式（前端按钮禁用 vs 后端拒绝 vs APScheduler 配置）？—— 留给 `plan.md`。

---

## 11. 用户确认

请确认以下任一选项：

- ✅ **同意**：本 spec 符合预期，可进入 **Planning** 阶段生成 `plan.md`。
- ❌ **修改**：请在下方/对话中列出需要调整的条款编号与意见，AI 将基于反馈重新生成本文档。
