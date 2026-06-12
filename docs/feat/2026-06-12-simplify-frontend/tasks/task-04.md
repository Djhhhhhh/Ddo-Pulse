# task-04 — 简化定时任务表单

## 目标
重构定时任务创建/编辑表单：移除阈值和模型 Profile，改造评分预览和提示词，将抓取 Digest 提升为必填。

## 范围
- `services/web/frontend/src/views/SettingsView.vue`（Job Form dialog 部分）
- `jobModal` ref 类型定义
- `submitJobModal` 函数
- `openCreateJobModal` / `populateJobModalFromJob` 函数

## 依赖
- task-01 (ScoringRubricPreview 组件)
- task-02 (PromptTemplateSelector 组件)

## 关联验收点（test-plan.md）
- G2: 阈值删除
- G3: 评分侧重点只读预览
- G4: 抓取与 Digest 必填
- G5: 模型 Profile 移除
- G6: 关键词与预过滤保留
- G7: 提示词模板选择与组合

## 步骤
1. **移除阈值字段**：从 `jobModal` ref 中删除 `score_threshold`，从表单 HTML 中删除阈值输入和提示
2. **改造评分侧重点**：
   - 引入 `ScoringRubricPreview` 组件
   - 将现有的评分下拉+textarea 替换为 `<ScoringRubricPreview>` 组件
   - `jobModal.scoring_rubric` 由组件自动根据选中模板填充
3. **改造抓取与 Digest**：
   - 将 `<details class="adv-details">` 折叠区改为普通 `<div>`（默认展开）
   - 将 `push_digest` 默认值改为 `true`
   - 将 `digest_top_n` 默认值改为 `10`
   - 添加必填标记
4. **移除模型 Profile**：
   - 删除「模型 Profile」折叠区（select 下拉框）
   - 从 `jobModal` 中删除 `llm_profile_id`
5. **改造提示词**：
   - 引入 `PromptTemplateSelector` 组件
   - 将「高级提示词」折叠区替换为 `<PromptTemplateSelector>` 组件
   - 删除原有的 prompt_template 和 system_prompt textarea
6. **保留关键词与预过滤**：保持现有折叠区不变
7. **更新 `submitJobModal`**：
   - 移除 `score_threshold` 和 `llm_profile_id` 字段
   - 确保 `scoring_rubric`、`prompt_template`、`system_prompt` 正确提交
8. **更新 `openCreateJobModal`**：移除 score_threshold 和 llm_profile_id 默认值
9. **更新 `populateJobModalFromJob`**：移除 score_threshold 和 llm_profile_id 映射
10. **清理 watch**：移除 `scoring_rubric` 相关的 watch（由组件管理）

## 产物
- `services/web/frontend/src/views/SettingsView.vue`（修改）

---

<!--
task-group.json schema reminder (must live at tasks/task-group.json):
-->
