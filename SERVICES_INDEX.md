# Services 索引

> 由 file-index skill 自动生成
> 更新时间：2026-05-16

本仓库采用 **两端** 架构：Web 端 + 后端。

| 服务 | 职责 | 文档 |
|------|------|------|
| backend | Ddo-Pulse **后端**（Python），包含 CLI、业务核心、REST API、MCP、数据库访问；与 `web` 端并列。 | [services/backend/AGENTS.md](services/backend/AGENTS.md) |
| web | Ddo-Pulse **Web 端**，Vue 3 + Vite 单页应用，提供 Dashboard、过往文章列表、文章详情与配置管理。 | [services/web/AGENTS.md](services/web/AGENTS.md) |

## 快速导航

- **backend**: [services/backend/](services/backend/) — `cli/` `core/` `api/` `mcp/` `db/`
- **web**: [services/web/](services/web/) — `frontend/`

## 文档

- MVP：[docs/mvp.md](docs/mvp.md)
- 需求：[docs/feat/](docs/feat/)
- 修复：[docs/fix/](docs/fix/)
