# task-05 — 更新任务详情卡片与摘要

## 目标
更新定时任务列表中的任务摘要卡片，移除阈值展示，保持其他信息。

## 范围
- `services/web/frontend/src/views/SettingsView.vue`（Job Summary card 部分）

## 依赖
- task-04

## 关联验收点（test-plan.md）
- G2: 阈值删除（摘要卡片）
- G9: 多任务与其他保留功能

## 步骤
1. 在任务摘要卡片的 `<dl class="summary-dl">` 中，移除「精选阈值」行
2. 保留 Cron、Webhook、Digest 推送等摘要行
3. 更新页面顶部的介绍文字，移除「阈值与评分」描述

## 产物
- `services/web/frontend/src/views/SettingsView.vue`（修改）

---

<!--
task-group.json schema reminder (must live at tasks/task-group.json):
-->
