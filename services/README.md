# services

仓库按 **两端** 划分，与 `file-index` 维护的 `AGENTS.md` 一一对应：

| 目录 | 端 | 技术栈 |
|------|-----|--------|
| [web/](web/) | **Web 端** | Vue 3 + Vite |
| [backend/](backend/) | **后端**（原「Python 端」，不用 `py` 命名） | Python 3.11+：CLI、core、FastAPI、MCP、db |

`backend` 内部的 `cli` / `core` / `api` / `mcp` / `db` 是**模块分包**，不是独立的 file-index 服务。

详见 [SERVICES_INDEX.md](../SERVICES_INDEX.md)。
