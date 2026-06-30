# Ddo-Pulse Specification

> AI 基于用户原始需求与 context-summary.md 对需求的规约化理解。
> 仅描述 What / Why 与验收标准；技术方案见 plan.md。

---

## 1. 项目概述

### 1.1 项目名称
Ddo-Pulse — OpenAI 兼容协议 LLM 配置支持

### 1.2 一句话定义
将前端 LLM 设置页从仅支持 model/apiKey 扩展为支持 baseURL/apiKey/Model 三项配置，使用户可接入任意 OpenAI 兼容协议的 LLM 服务。

### 1.3 设计意图
- 当前 LLM 设置页仅暴露 model 和 apiKey，base_url 被硬编码为 OpenRouter 默认值
- 用户无法接入自部署模型（如 Ollama、vLLM、LocalAI）或其他 OpenAI 兼容服务（如 DeepSeek、Moonshot、硅基流动等）
- 后端已使用 OpenAI SDK 且数据库已有 base_url 字段，改动集中在前端暴露

---

## 2. 术语表（Glossary）

| 术语 | 定义 |
|---|---|
| OpenAI 兼容协议 | 遵循 OpenAI Chat Completions API 格式（`/v1/chat/completions`）的 HTTP 接口，被多数 LLM 服务商采用 |
| base_url | LLM API 的基础地址，如 `https://openrouter.ai/api/v1` 或 `http://localhost:11434/v1` |
| llm_profile | 数据库中存储的一组 LLM 配置（provider、base_url、model、api_key 等） |

---

## 3. 功能需求（Functional Requirements）

### 3.1 前端 LLM 设置页

- **FR-UI-1**：LLM 设置页（section "llm"）的每个 profile 卡片应新增 base_url 输入框，位于 model 输入框上方
- **FR-UI-2**：base_url 输入框应有 placeholder 提示，示例：`https://openrouter.ai/api/v1`
- **FR-UI-3**：保存 profile 时，PATCH 请求应同时提交 base_url、model、api_key 三个字段
- **FR-UI-4**：base_url 字段应显示当前值（从 API 获取的 profile 数据回填）

### 3.2 后端 API

- **FR-API-1**：PATCH `/api/profiles/{id}` 端点应接受 base_url 字段（当前已支持，无需改动）
- **FR-API-2**：GET `/api/profiles` 响应应包含 base_url 字段（当前已支持，无需改动）

### 3.3 数据库

- **FR-DB-1**：`llm_profiles` 表已包含 `base_url` 列（默认值 `'https://openrouter.ai/api/v1'`），无需 schema 变更

---

## 4. 产物与目录结构（What gets created）

```
services/web/frontend/src/views/SettingsView.vue   # 修改：LLM section 增加 base_url 输入框
```

仅涉及一个文件的修改。

---

## 5. 关键流程

```
用户打开设置页 → 选择 "模型与密钥" tab
  → 看到 profile 卡片：base_url / model / api_key 三行输入
  → 修改 base_url 为自部署地址（如 http://localhost:11434/v1）
  → 点击保存 → PATCH /api/profiles/{id} { base_url, model, api_key }
  → 后端写入 SQLite → 下次 pipeline 运行时使用新 base_url
```

---

## 6. 约束与原则

- **C-1**：不修改后端代码（后端已支持 base_url）
- **C-2**：不修改数据库 schema（base_url 字段已存在）
- **C-3**：保持现有 UI 风格一致（与其他输入框样式统一）
- **C-4**：base_url 输入框应为 text 类型（非 password），方便用户确认地址

---

## 7. 验收标准（Acceptance Criteria）

- **AC-1**：设置页 LLM section 每个 profile 卡片显示 base_url、model、apiKey 三个输入框
- **AC-2**：修改 base_url 并保存后，刷新页面 base_url 值保持不变
- **AC-3**：修改 base_url 后触发 pipeline 运行，LLM 调用使用新的 base_url
- **AC-4**：现有 OpenRouter 默认配置不受影响（base_url 默认值仍为 `https://openrouter.ai/api/v1`）

---

## 8. 非功能需求（Non-Functional）

- **NFR-1**：改动范围最小化，仅修改前端 SettingsView.vue 一个文件
- **NFR-2**：不引入新的前端依赖

---

## 9. 范围说明（In / Out of Scope）

### In Scope
- 前端 SettingsView.vue 的 LLM section 增加 base_url 输入框
- PATCH 请求增加 base_url 字段提交

### Out of Scope
- 后端代码修改（已支持）
- 数据库 schema 变更（已支持）
- LLM 连接测试功能（如"测试连接"按钮）
- 多 profile 管理 UI 优化
- provider 字段的前端暴露

---

## 10. 开放问题（Open Questions，待 Plan 阶段决策）

- **Q-1**：是否需要在 base_url 输入框旁添加"重置为默认"按钮（恢复为 OpenRouter 地址）？——留给 plan.md。

---

## 11. 用户确认

请确认以下任一选项：

- ✅ **同意**：本 spec 符合预期，可进入 **Planning** 阶段生成 `plan.md`。
- ❌ **修改**：请在下方/对话中列出需要调整的条款编号与意见，AI 将基于反馈重新生成本文档。
