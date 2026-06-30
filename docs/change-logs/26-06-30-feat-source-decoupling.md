# 变更日志

**提交信息**: feat: 信息源与定时任务解耦，支持 CSV 全量覆盖和 per-source 关注点配置
**分支**: main
**日期**: 2026-06-30
**作者**: djhhh

## 变更文件
- services/backend/db/schema.sql (modified)
- services/backend/db/ddo_pulse_db/repository.py (modified)
- services/backend/api/ddo_pulse_api/api_routes.py (modified)
- services/backend/api/ddo_pulse_api/schemas.py (modified)
- services/backend/core/ddo_pulse_core/pipeline.py (modified)
- services/backend/core/ddo_pulse_core/analyzer/runner.py (modified)
- services/backend/core/ddo_pulse_core/mcp_tools.py (modified)
- services/backend/cli/ddo_pulse_cli/main.py (modified)
- services/web/frontend/src/api/client.ts (modified)
- services/web/frontend/src/views/SettingsView.vue (modified)
- docs/feat/2026-06-30-source-decoupling/ (added - 流水线产物)

## 统计
- 新增文件: 19
- 修改文件: 10
- 删除文件: 1
- 代码行数: +1650 / -96

## 描述
信息源（sources）从 pipeline_jobs 的子表变为全局独立实体，通过 job_sources 关联表实现多对多关系。新增 CSV 全量覆盖同步 API 和 per-source 关注点配置（interest_keywords、need_llm_analysis、analyze_limit 等）。包含自动数据迁移脚本。
