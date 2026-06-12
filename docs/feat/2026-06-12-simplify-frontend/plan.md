# Ddo-Pulse 前端简化 Plan

> 基于已确认的 `spec.md` 做技术决策：定 schema、定通信方式、定运行时模型、定关键算法、定取舍。
> 不写代码，但对每个开放问题给出唯一确定答案。
> 用户确认后方可进入 Test-Planning。

---

## 1. 决策原则

| # | 原则 | 落地体现 |
|---|------|----------|
| P-1 | 前端简化优先，后端最小改动 | 后端 schema 保留所有字段不变（向后兼容），前端隐藏/替换字段交互方式 |
| P-2 | 不破坏已有数据 | 不做 DB schema 迁移；被前端隐藏的字段在后端仍正常存储 |
| P-3 | 系统预设硬编码在前端 | 评分模板、提示词模板均以 JS 常量形式存在于前端，不新增后端 API |

---

## 2. 整体架构

```
┌─────────────────────────────────────────────┐
│                Frontend (Vue 3)              │
│                                              │
│  SettingsView.vue (主修改)                    │
│  ├── LLM Tab: 仅 model + api_key            │
│  └── Pipeline Tab:                           │
│      ├── Job List (保留)                     │
│      └── Job Form (简化)                     │
│          ├── name, cron, webhook (保留)      │
│          ├── score_threshold → 移除           │
│          ├── scoring_rubric → 只读预览        │
│          ├── fetch & digest → 必填展开        │
│          ├── model profile → 移除            │
│          ├── keywords → 保留                 │
│          └── prompts → 模板+用户需求组合      │
│                                              │
│  新增组件:                                    │
│  ├── ScoringRubricPreview.vue                │
│  └── PromptTemplateSelector.vue              │
└──────────────────┬───────────────────────────┘
                   │ API (不变)
┌──────────────────┴───────────────────────────┐
│              Backend (FastAPI)                │
│                                              │
│  schemas.py: 保持不变 (向后兼容)               │
│  api_routes.py: 保持不变                      │
│  pipeline.py: 保持不变                        │
│  prompt.py: 保持不变                          │
└──────────────────────────────────────────────┘
```

关键事实：
- **后端零改动**：所有 schema、路由、pipeline 逻辑保持不变
- **前端单文件主改**：SettingsView.vue 是唯一需要大量修改的文件
- **新增 2 个小组件**：评分预览和提示词选择器

---

## 3. 目录与命名（最终定版）

```
services/web/frontend/src/
  views/
    SettingsView.vue              # 主要修改
  components/
    ScoringRubricPreview.vue      # 新增：评分侧重点只读预览
    PromptTemplateSelector.vue    # 新增：提示词模板选择+用户需求+预览
  api/
    client.ts                     # 无需修改（后端接口不变）
```

---

## 4. 核心 Schema（前端数据模型）

### 4.1 Job Modal 表单数据（前端 ref）

```typescript
// 修改后的 jobModal — 移除 score_threshold 和 llm_profile_id
const jobModal = ref({
  name: "",
  schedule_cron: "0 8 * * *",
  enabled: true,
  feishu_webhook_url: "",
  push_digest: true,            // 默认改为 true（必填）
  analyze_limit: 50,
  digest_top_n: 10,             // 默认改为 10
  // score_threshold: 移除       // FR-FORM-3
  keywordsText: "",
  keyword_prefilter: false,
  prompt_template: "",           // 组合后的最终提示词
  scoring_rubric: "",            // 自动设为选中模板的 body，只读
  system_prompt: "",             // 用户需求文本（与系统模板组合）
  // llm_profile_id: 移除        // FR-FORM-10
});
```

### 4.2 提示词模板数据结构

```typescript
// 新增常量 — 系统提示词模板
const PROMPT_TEMPLATES = [
  {
    id: "default",
    label: "通用精选",
    description: "适用于大多数 RSS 订阅场景",
    body: DEFAULT_PROMPT_TEMPLATE,  // 来自后端已有的默认模板内容
  },
  {
    id: "paper",
    label: "论文分析",
    description: "适用于学术论文、预印本等场景",
    body: PAPER_PROMPT_TEMPLATE,
  },
  // 可扩展更多模板
];
```

### 4.3 字段语义约束

- **`scoring_rubric`**：提交时自动填充为当前选中模板的 body 值，前端只读不可编辑
- **`system_prompt`**：前端作为「用户需求」输入框，提交时存入 system_prompt 字段
- **`prompt_template`**：提交时 = 系统模板 body + 用户需求拼接，存入 prompt_template 字段
- **`score_threshold`**：前端不发送此字段，后端使用默认值 7（PipelineJobCreate 默认值）
- **`llm_profile_id`**：前端不发送此字段，后端使用默认 profile

### 4.4 校验

- cron 表达式：保留现有的前端格式帮助提示
- feishu_webhook_url：创建时必填
- analyze_limit：必填，默认 50，最小 0
- digest_top_n：必填，默认 10，最小 1

---

## 5. 关键算法 / 流程

### 5.1 提示词组合逻辑

```
用户操作流程:
1. 用户从「系统模板」下拉框选择一个预设模板
2. 系统显示该模板的预览内容（只读）
3. 用户在「用户需求描述」文本框输入自己的需求（如 "关注 AI 和大模型领域"）
4. 系统实时预览最终提示词 = 模板 body + "\n\n用户补充需求：" + 用户需求
5. 提交时：
   - prompt_template = 选中模板的 body + 用户需求组合
   - system_prompt = 用户需求文本
   - scoring_rubric = 选中评分模板的 body
```

### 5.2 评分预览逻辑

```
用户操作流程:
1. 评分侧重点区域默认显示 balanced 模板内容（只读 textarea）
2. 用户可通过下拉框切换查看不同模板（balanced / tech_depth / timely）
3. 切换时只更新预览内容，不允许编辑
4. 提交时 scoring_rubric 自动使用当前选中模板的 body
```

---

## 6. 错误处理与回退

| 触发条件 | 行为 |
|---|---|
| 用户未填 webhook（创建时） | 前端阻止提交，显示错误提示 |
| 用户未选提示词模板 | 使用 default 模板作为默认 |
| 用户需求文本为空 | 仅使用系统模板，不拼接用户需求部分 |
| 后端返回 score_threshold 相关错误 | 不应发生（后端有默认值），若发生则显示通用错误 |

---

## 7. 风险与权衡

| # | 风险 | 描述 | 处置 |
|---|---|------|------|
| R-1 | 向后兼容 | 前端不发送 score_threshold 和 llm_profile_id，后端需要有合理默认值 | 后端 PipelineJobCreate 的 score_threshold 默认值为 7，llm_profile_id 默认为 None（使用默认 profile）— **已满足** |
| R-2 | 已有任务的 score_threshold | 已创建的任务仍保存了 score_threshold，但前端不再展示编辑 | 保持不变，已有任务的阈值继续生效；新任务使用后端默认值 |
| R-3 | 提示词模板硬编码 | 模板内容在前端 JS 中，更新需要发版 | 可接受，模板变更频率低；后续可改为后端 API |
| R-4 | 模型 Profile 移除 | 移除前端选择后，所有任务使用默认 profile | 如用户有多个 profile 需求，后续可扩展 |

---

## 8. 实施次序（高层路线，供 Tasking 拆分参考）

1. **前端组件开发**：创建 ScoringRubricPreview.vue 和 PromptTemplateSelector.vue
2. **SettingsView 修改 — LLM Tab**：简化为仅 model + api_key
3. **SettingsView 修改 — Job Form**：移除阈值/模型 Profile，改造评分预览/提示词/抓取Digest
4. **SettingsView 修改 — Job Summary**：更新任务详情卡片，移除阈值展示
5. **验证与联调**：确保前后端数据流正确

---

## 9. 与 spec 的开放问题对应表

| spec Open Question | plan 中的落地 |
|---|---|
| Q-1：评分侧重点预设模板来源 | Section 4.2 — 硬编码在前端 `RUBRIC_PRESETS` 常量中（已有代码） |
| Q-2：提示词系统模板来源 | Section 4.2 — 硬编码在前端 `PROMPT_TEMPLATES` 常量中，内容来自 `prompt.py` 的现有模板 |
| Q-3：移除 llm_profile_id 后如何确定模型 | Section 4.3 — 前端不发送此字段，后端 PipelineJobCreate 默认 None → 使用默认 profile |
| Q-4：定时任务并发控制 | Section 4.3 — 后端 APScheduler 已有同 job 不重叠机制；前端运行按钮在 jobRunning 期间 disabled |

---

## 10. 用户确认

请确认以下任一选项：

- ✅ **同意**：本 plan 符合预期，可进入 **Test-Planning** 阶段生成 `test-plan.md`。
- ❌ **修改**：请在下方/对话中列出需要调整的章节与意见，AI 将基于反馈重新生成本文档。
