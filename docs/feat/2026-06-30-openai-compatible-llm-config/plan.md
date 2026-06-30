# Ddo-Pulse Plan

> 基于已确认的 spec.md 做技术决策：定 schema、定通信方式、定运行时模型、定关键算法、定取舍。

---

## 1. 决策原则

| # | 原则 | 落地体现 |
|---|------|----------|
| P-1 | 最小改动 | 仅修改已有的文件，不新增模块或依赖 |
| P-2 | 全链路贯通 | 数据库已有 base_url 列，需确保 API 全链路暴露该字段 |
| P-3 | 向后兼容 | base_url 有默认值，现有用户无需任何操作 |

---

## 2. 整体架构

```
┌─────────────────────┐         ┌──────────────────────────┐
│  前端 SettingsView   │  PATCH  │  后端 API routes          │
│                     │────────▶│  /api/profiles/{id}       │
│  base_url input     │         │  → ProfileUpdate schema   │
│  model input        │         │  → db.update_llm_profile  │
│  api_key input      │         │  → SQLite llm_profiles    │
└─────────────────────┘         └──────────────────────────┘
```

关键事实：
- 数据库 `llm_profiles` 表已有 `base_url` 列（默认 `'https://openrouter.ai/api/v1'`），**无需 schema 变更**
- 后端使用 OpenAI SDK（`openai.OpenAI(base_url=..., api_key=...)`），**已原生支持任意 base_url**
- 改动链路：前端 UI → 前端 API 类型 → 后端 Pydantic schema → 后端 DB 方法

---

## 3. 目录与命名（最终定版）

```
services/
├── backend/
│   └── api/ddo_pulse_api/
│       ├── schemas.py          # 修改：ProfileOut + ProfileUpdate 增加 base_url
│       └── api_routes.py       # 修改：_profile_from_row + update_profile 传递 base_url
│   └── db/ddo_pulse_db/
│       └── repository.py       # 修改：update_llm_profile 增加 base_url 参数
└── web/frontend/src/
    ├── api/client.ts           # 修改：Profile 接口增加 base_url
    └── views/SettingsView.vue  # 修改：LLM section 增加 base_url 输入框
```

---

## 4. 核心 Schema

### 4.1 ProfileOut（后端响应，FR-API-2）

```jsonc
{
  "id": 1,
  "name": "default",
  "base_url": "https://openrouter.ai/api/v1",  // 新增
  "model": "gpt-4o-mini",
  "is_default": true,
  "score_threshold": 7,
  "api_key_set": true,
  "temperature": 0.3,
  "max_tokens": 1024,
  "prompt_template": null,
  "system_prompt": null,
  "category_hints": []
}
```

### 4.2 ProfileUpdate（后端请求，FR-API-1）

```jsonc
{
  "base_url": "http://localhost:11434/v1",  // 新增，可选
  "model": "llama3",
  "api_key": "sk-xxx"
}
```

### 4.3 Frontend Profile 接口（FR-UI-4）

```typescript
export interface Profile {
  id: number;
  name: string;
  base_url: string;  // 新增
  model: string;
  // ... 其余字段不变
}
```

字段语义约束：
- **base_url**：必须是有效的 URL，以 `/v1` 或类似路径结尾；空字符串时使用数据库默认值

校验：
- 后端 Pydantic 无额外校验（信任数据库默认值）
- 前端 input type="text"，用户自行确保格式正确

---

## 5. 关键算法 / 流程

### 5.1 保存 Profile 流程（saveProfile）

1. 从 `profileDraft[p.id]` 读取 `base_url` 和 `model`
2. 从 `profileKey[p.id]` 读取 `api_key`（可选）
3. 构造 body：`{ base_url, model, ...(api_key && { api_key }) }`
4. PATCH `/api/profiles/{id}`
5. 后端 `update_llm_profile` 将 base_url 写入 SQLite
6. 刷新 profiles 列表

### 5.2 加载 Profile 流程（refresh）

1. GET `/api/profiles` 返回包含 `base_url` 的 ProfileOut 列表
2. 前端 `profileDraft[p.id]` 初始化为 `{ base_url: p.base_url, model: p.model }`
3. 输入框 v-model 绑定到 `profileDraft[p.id].base_url`

---

## 6. 错误处理与回退

| 触发条件 | 行为 |
|---|---|
| 用户输入无效 URL | 后端 OpenAI SDK 会在实际调用时报错；不影响保存 |
| base_url 为空 | 使用数据库默认值 `https://openrouter.ai/api/v1` |
| API PATCH 失败 | 前端 catch 显示错误消息（已有逻辑） |

---

## 7. 风险与权衡

| # | 风险 | 描述 | 处置 |
|---|------|------|------|
| R-1 | 用户输入错误的 base_url | 导致 LLM 调用失败 | 保存时不做 URL 校验，依赖运行时错误反馈；后续可加"测试连接"按钮 |
| R-2 | ProfileUpdate 的 base_url 为 null | 可能覆盖为 null | 后端 update_llm_profile 逻辑：仅当参数非 None 时更新，否则保留原值 |

---

## 8. 实施次序（高层路线，供 Tasking 拆分参考）

1. **后端 DB 层**：`repository.py` — `update_llm_profile` 增加 `base_url` 参数
2. **后端 API 层**：`schemas.py` — ProfileOut + ProfileUpdate 增加 `base_url` 字段；`api_routes.py` — `_profile_from_row` + `update_profile` 传递 `base_url`
3. **前端 API 类型**：`client.ts` — Profile 接口增加 `base_url`
4. **前端 UI**：`SettingsView.vue` — LLM section 增加 base_url 输入框 + profileDraft + saveProfile

---

## 9. 与 spec 的开放问题对应表

| spec Open Question | plan 中的落地 |
|---|---|
| Q-1 是否需要"重置为默认"按钮？ | 不需要。base_url 输入框的 placeholder 已显示默认值 `https://openrouter.ai/api/v1`，用户清空后保存即恢复默认（后端逻辑：空值不覆盖）。 |

---

## 10. 用户确认

请确认以下任一选项：

- ✅ **同意**：本 plan 符合预期，可进入 **Test-Planning** 阶段生成 `test-plan.md`。
- ❌ **修改**：请在下方/对话中列出需要调整的章节与意见，AI 将基于反馈重新生成本文档。
