# task-01 — 创建 ScoringRubricPreview 组件

## 目标
创建评分侧重点只读预览组件，支持切换查看不同预设模板，不可编辑。

## 范围
- `services/web/frontend/src/components/ScoringRubricPreview.vue`（新建）

## 依赖
- 无

## 关联验收点（test-plan.md）
- G3: 评分侧重点只读预览

## 步骤
1. 创建 `ScoringRubricPreview.vue` 单文件组件
2. 将现有 SettingsView.vue 中的 `RUBRIC_PRESETS` 常量迁移到此组件中
3. 实现 props: `modelValue` (当前选中的模板 id)
4. 实现 emits: `update:modelValue` (模板切换事件)
5. 模板区域使用 readonly textarea 或只读 div 展示当前模板 body
6. 下拉框切换模板时 emit 事件，预览内容自动更新
7. 默认选中 `balanced` 模板

## 产物
- `services/web/frontend/src/components/ScoringRubricPreview.vue`

---

<!--
task-group.json schema reminder (must live at tasks/task-group.json):
-->
