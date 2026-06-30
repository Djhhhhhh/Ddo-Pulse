# 执行报告 — Ddo-Pulse 信息源逻辑重构

> 基于 Ddo-Code-Flow 流水线自动生成。

---

## 1. 运行元数据

| 字段 | 值 |
|------|-----|
| Run ID | 2026-06-30-source-decoupling |
| 创建时间 | 2026-06-30T19:10:00Z |
| 当前阶段 | reporting |
| 分支 | feat/2026-06-30-source-decoupling |
| 工作树 | /Users/djhhh/work_area/Ddo-Pulse-feat-2026-06-30-source-decoupling |

---

## 2. 阶段完成状态

| 阶段 | 状态 | 完成时间 |
|------|------|---------|
| context | ✅ done | 2026-06-30T19:12:00Z |
| requirement | ✅ done | 2026-06-30T19:13:00Z |
| specification | ✅ done | 2026-06-30T19:16:00Z |
| planning | ✅ done | 2026-06-30T19:18:00Z |
| test-planning | ✅ done | 2026-06-30T19:20:00Z |
| tasking | ✅ done | 2026-06-30T19:22:00Z |
| coding | ✅ done | 2026-06-30T19:30:00Z |
| verification | ✅ done | 2026-06-30T19:35:00Z |
| reporting | ✅ done | 2026-06-30T19:40:00Z |

---

## 3. 验证摘要

| 分组 | 内容 | 状态 |
|------|------|------|
| G1 | DB Schema 变更与数据迁移 | ✅ PASSED (4/4) |
| G2 | CSV 全量覆盖同步 API | ⏭️ SKIPPED (需运行服务器) |
| G3 | 信息源与定时任务解耦 | ✅ PASSED (2/2) |
| G4 | Per-Source 关注点配置 | ✅ PASSED (1/1) |
| G5 | 前端 CSV 同步按钮 | ⏭️ SKIPPED (human 测试) |
| G6 | 前端 Per-Source 关注点配置 | ⏭️ SKIPPED (human 测试) |
| G7 | Pipeline 执行适配 | ✅ PASSED (2/2) |

**总计**：9 项自动化测试通过，3 组跳过（需服务器或人工验证）。

---

## 4. 产物清单

| 文件 | 阶段 | 说明 |
|------|------|------|
| context-summary.md | context | 项目上下文汇总 |
| requirement.md | requirement | 用户需求原文 |
| spec.md | specification | 功能需求规格 |
| plan.md | planning | 技术决策方案 |
| test-plan.md | test-planning | 验收测试清单 |
| tasks/task-01~08.md | tasking | 任务拆分 |
| tasks/task-group.json | tasking | 任务依赖与批次 |
| verification.log | verification | 测试执行结果 |
| execution-report.md | reporting | 本文件 |

---

## 5. 代码变更摘要

### 5.1 数据库层（`services/backend/db/`）

- **schema.sql**：移除 `sources.job_id`，`sources.url` 加 UNIQUE 约束，新增 `job_sources` 关联表
- **repository.py**：新增 `_migrate_sources_to_global()` 迁移方法；修改 `add_source`、`list_sources`、`update_source`、`upsert_source_by_url` 等方法移除 `job_id` 参数；新增 `add_job_source`、`remove_job_source`、`list_job_sources`、`update_job_source_focus`、`set_job_source_enabled`、`get_job_source` 方法

### 5.2 后端 API（`services/backend/api/`）

- **schemas.py**：`SourceOut`/`SourceCreate`/`SourceUpdate` 移除 `job_id`；新增 `JobSourceOut`、`JobSourceCreate`、`JobSourceUpdate`、`SyncFromCsvResult`
- **api_routes.py**：修改 source 端点移除 `job_id`；新增 `POST /api/sources/sync-from-csv`、`GET/POST/PATCH/DELETE /api/pipeline-jobs/{job_id}/sources` 端点

### 5.3 Pipeline（`services/backend/core/`）

- **pipeline.py**：`run_pipeline_job()` 通过 `list_job_sources()` 加载源，读取 `focus_config_json` 进行差异化处理
- **analyzer/runner.py**：`analyze_job_sources()` 新增 `per_source_interest_keywords` 参数支持 per-source 关键词覆盖
- **mcp_tools.py**：`_source_row_to_dict()` 移除 `job_id` 字段

### 5.4 CLI（`services/backend/cli/`）

- **main.py**：修改 `config_export`、`seed import`、`digest build`、`digest push` 命令适配新表结构

### 5.5 前端（`services/web/frontend/`）

- **client.ts**：移除 `Source.job_id`，新增 `JobSource` 接口和 `syncSourcesFromCsv`、`listJobSources`、`addJobSource`、`updateJobSourceFocus`、`removeJobSource` API 方法
- **SettingsView.vue**：源列表改用 `listJobSources`；`addSource` 先创建源再关联到 job；`patchSourceEnabled` 和 `removeSource` 改用 job_sources API；`onImportCsv` 改为全量覆盖同步；新增 `getFocusConfig` 和 `getAnalyzeLimit` 辅助函数

---

## 6. 决策日志

| 时间 | 事件 |
|------|------|
| 2026-06-30T19:10:00Z | 流水线创建 |
| 2026-06-30T19:12:00Z | context 阶段完成 |
| 2026-06-30T19:13:00Z | requirement 阶段完成 |
| 2026-06-30T19:15:00Z | git-worktree 完成，创建分支 feat/2026-06-30-source-decoupling |
| 2026-06-30T19:16:00Z | spec 用户确认通过 |
| 2026-06-30T19:18:00Z | plan 用户确认通过 |
| 2026-06-30T19:20:00Z | test-plan 用户确认通过 |
| 2026-06-30T19:22:00Z | tasking 阶段完成，拆分为 8 个任务 |
| 2026-06-30T19:30:00Z | coding 阶段完成，所有 8 个任务已实现 |
| 2026-06-30T19:35:00Z | verification 通过（9/9 自动化测试 PASS） |

---

## 7. 待人工验证项

以下测试需要在运行环境中手动执行：

1. **G2**：启动后端服务，调用 `POST /api/sources/sync-from-csv`，验证返回 added/updated/skipped
2. **G5**：在前端设置页点击「全量覆盖信息源」按钮，验证同步结果
3. **G6**：在定时任务源列表中编辑 per-source 关注点配置，验证持久化和执行效果
