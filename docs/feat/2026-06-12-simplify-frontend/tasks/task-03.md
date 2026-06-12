# task-03 — 简化 LLM Tab（模型与密钥）

## 目标
将 LLM 配置页面简化为仅显示 model 和 api_key 两个可编辑字段。

## 范围
- `services/web/frontend/src/views/SettingsView.vue`（LLM Tab 部分）

## 依赖
- 无

## 关联验收点（test-plan.md）
- G1: 模型与密钥简化

## 步骤
1. 在 LLM Tab 的 `form-grid` 中，移除 temperature 输入框
2. 移除 max_tokens 输入框
3. 移除 score_threshold 输入框
4. 移除 category_hints textarea 及其标签
5. 移除 `<details>` 高级兜底提示词区域（prompt_template、system_prompt）
6. 保留 model 输入框和 api_key 密码输入框
7. 保留「保存 Profile」按钮
8. 更新 LLM Tab 的介绍文字，移除关于温度、阈值、提示词的描述
9. 清理 `profileDraft` 类型定义，移除不再使用的字段（temperature, max_tokens, score_threshold, category_hints_text, prompt_template, system_prompt）
10. 清理 `saveProfile` 函数，仅发送 model 和 api_key（如有）

## 产物
- `services/web/frontend/src/views/SettingsView.vue`（修改）

---

<!--
task-group.json schema reminder (must live at tasks/task-group.json):
-->
