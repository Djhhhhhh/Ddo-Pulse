# Context Summary

## 已加载来源

| 文件路径 | 一行摘要 |
|---------|---------|
| `services/backend/AGENTS.md` | 后端架构说明：Python CLI + Core + API + MCP + DB，模块依赖 cli/mcp → core → db |
| `docs/mvp.md` | MVP 产品与技术规格：SQLite 存储、sources 表结构、pipeline_jobs 表、配置管理方式 |
| `docs/ddo_pulse_rss_seed_library.csv` | RSS 种子库（只读建议列表），含类别/源名称/源类型/rss_url/质量评级等字段 |
| `services/backend/db/schema.sql` | 数据库 schema：pipeline_jobs → sources（CASCADE）、raw_items、analyzed_items、digests、job_runs |
| `services/backend/core/ddo_pulse_core/pipeline.py` | Pipeline 核心：run_pipeline_job() 按 job_id 加载 enabled sources → fetch → analyze → digest |
| `services/backend/core/ddo_pulse_core/fetchers/` | Fetcher 架构：BaseFetcher 抽象，RssFetcher/HtmlListFetcher/BrowserSessionFetcher 实现 |
| `services/backend/api/ddo_pulse_api/api_routes.py` | REST API：sources CRUD（需 job_id）、pipeline-jobs CRUD、rss-library 只读接口 |
| `services/backend/api/ddo_pulse_api/scheduler.py` | APScheduler 调度：reload_pipeline_jobs_schedule() 全量重建定时任务 |
| `services/web/frontend/src/views/SettingsView.vue` | 前端配置页：左侧 pipeline_jobs 列表，右侧 sources 表格 + RSS 种子库选择器 |
| `services/web/frontend/src/api/client.ts` | 前端 API 客户端：sources/pipeline-jobs/rss-library 接口封装 |

## 上下文缺失

- `config.base.contextPaths` 为空，无额外上下文路径配置
- `AGENTS.md`（项目根级）不存在

## 关键架构发现

### 信息源存储现状
- **sources 表**：SQLite 中存储，`job_id` 外键关联 `pipeline_jobs`，ON DELETE CASCADE
- **RSS 种子库**：`docs/ddo_pulse_rss_seed_library.csv`，只读建议列表，前端"添加源"对话框使用
- **无 config.yaml**：项目当前没有 config.yaml 文件，sources 完全通过 DB 管理

### 信息源与定时任务的耦合关系
- **强耦合**：source 的 `job_id` 是 NOT NULL 外键，source 不能脱离 pipeline_job 存在
- **级联删除**：删除 pipeline_job → 删除其所有 sources → 删除 raw_items → 删除 analyzed_items
- **运行时解耦**：scheduler 只关心 pipeline_jobs 表，cron 触发时才查询 sources；删除 source 不影响 cron 执行

### 用户需求与现状的差距
1. **用户期望**：本地 docs 目录手动维护信息源表格 + 前端按钮全量覆盖
   - **现状**：sources 存在 DB 中，CSV 仅作只读建议库
2. **用户期望**：信息源与定时任务解耦，删源不影响定时任务
   - **现状**：source 必须属于某个 pipeline_job（job_id NOT NULL），但删除 source 不影响 cron
3. **用户期望**：同一定时任务可对不同信息源设定不同关注点
   - **现状**：每个 source 有 `config_json`（含 analyze_limit），pipeline_job 有 `interest_keywords_json`，但没有 per-source 的关注点配置
