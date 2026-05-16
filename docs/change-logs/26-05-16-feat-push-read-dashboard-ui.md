# 变更日志

**提交信息**: feat: 增量推送、文章已读与仪表盘/配置优化
**分支**: main
**日期**: 2026-05-16

## 变更文件

### 后端
- `services/backend/db/schema.sql` (modified) — analyzed_items 增加 pushed_at、read_at
- `services/backend/db/ddo_pulse_db/repository.py` (modified) — 已读统计、推送去重候选、删除任务清理 job_runs、文章已读/未读
- `services/backend/core/ddo_pulse_core/digest/runner.py` (modified) — 按评分增量推送，合并当日 Digest
- `services/backend/core/ddo_pulse_core/pipeline.py` (modified) — push_items 统计
- `services/backend/core/ddo_pulse_core/notifier/feishu.py` (modified) — 推送标题「新增 N 篇」
- `services/backend/api/ddo_pulse_api/api_routes.py` (modified) — dashboard 已读数、文章未读 API、手动运行 force_push、任务详情 preview
- `services/backend/api/ddo_pulse_api/schemas.py` (modified) — Article/Dashboard/JobRunDetail 字段扩展

### 前端
- `services/web/frontend/src/views/ArticlesView.vue` (modified) — 列表状态列、弹窗去标签、已读切换、列宽
- `services/web/frontend/src/views/DashboardView.vue` (modified) — 已读统计卡、六列单行布局、运行摘要 preview
- `services/web/frontend/src/views/SettingsView.vue` (modified) — Cron 说明、推送篇数、运行任务 force_push
- `services/web/frontend/src/api/client.ts` (modified) — 文章已读 API、Dashboard 类型

### 根目录
- `LICENSE` (added) — MIT License
- `README.md` (modified) — 许可证说明与项目结构

## 统计

- 新增文件: 1
- 修改文件: 12+
- 删除文件: 0

## 描述

- 每轮从**未推送**精选中按评分取 Top N 推送飞书，不重复发送；推送成功写入 pushed_at/read_at
- 文章页支持已读/未读切换（含已推送文章）；列表默认按评分排序
- 删除定时任务时同步删除运行记录；仪表盘展示已读数量且状态卡单行排列
- 配置页 Cron 提示、手动运行按任务配置推送；新增 MIT LICENSE
