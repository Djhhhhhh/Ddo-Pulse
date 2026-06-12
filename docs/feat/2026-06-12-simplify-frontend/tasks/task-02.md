# task-02 — 创建 PromptTemplateSelector 组件

## 目标
创建提示词模板选择组件，支持系统模板选择、用户需求输入、最终组合预览。

## 范围
- `services/web/frontend/src/components/PromptTemplateSelector.vue`（新建）

## 依赖
- 无

## 关联验收点（test-plan.md）
- G7: 提示词模板选择与组合

## 步骤
1. 创建 `PromptTemplateSelector.vue` 单文件组件
2. 定义 `PROMPT_TEMPLATES` 常量（default 通用精选、paper 论文分析），内容从 `prompt.py` 的 `DEFAULT_PROMPT_TEMPLATE` 和 `PAPER_PROMPT_TEMPLATE` 提取
3. 实现 props: `systemTemplate` (选中模板 body), `userPrompt` (用户需求文本)
4. 实现 emits: `update:systemTemplate`, `update:userPrompt`
5. 下拉框选择模板后更新 systemTemplate 并显示只读预览
6. 用户需求文本框支持自由输入
7. 底部实时预览最终提示词 = systemTemplate + "\n\n用户补充需求：" + userPrompt（若 userPrompt 非空）
8. 若 userPrompt 为空，最终预览仅显示 systemTemplate

## 产物
- `services/web/frontend/src/components/PromptTemplateSelector.vue`

---

<!--
task-group.json schema reminder (must live at tasks/task-group.json):
-->
