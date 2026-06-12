# 变更日志

**提交信息**: feat(frontend): 简化前端配置页面，集成 RSS 源库
**分支**: main
**日期**: 2026-06-12
**作者**: Djhhh

## 变更文件
- services/web/frontend/src/components/ScoringRubricPreview.vue (added)
- services/web/frontend/src/components/PromptTemplateSelector.vue (added)
- services/web/frontend/src/views/SettingsView.vue (modified)
- services/web/frontend/src/api/client.ts (modified)
- services/backend/api/ddo_pulse_api/api_routes.py (modified)
- services/backend/api/ddo_pulse_api/schemas.py (modified)
- services/backend/cli/ddo_pulse_cli/main.py (modified)
- services/backend/core/ddo_pulse_core/analyzer/prompt.py (modified)
- services/backend/db/ddo_pulse_db/repository.py (modified)
- docs/ddo_pulse_rss_seed_library.csv (added)
- docs/feat/2026-06-12-simplify-frontend/ (added - 流水线产物)
- docs/prompt/ (added)

## 统计
- 新增文件: 16
- 修改文件: 7
- 删除文件: 0
- 代码行数: +2879 / -261

## 描述
简化前端 SettingsView 配置页面：
- 模型与密钥仅保留 model + api_key
- 移除阈值和模型 Profile 选择
- 评分侧重点改为只读预览（ScoringRubricPreview 组件）
- 提示词改为系统模板 + 用户需求组合（PromptTemplateSelector 组件）
- 抓取与 Digest 提升为必填
- 集成 RSS 源库（后端解析 CSV，前端选择）
- 任务运行状态基于后端实际状态判断，防止重复运行
