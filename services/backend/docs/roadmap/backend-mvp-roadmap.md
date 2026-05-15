# Backend MVP Roadmap

> 与 [docs/mvp.md](../../../../docs/mvp.md) §15 对齐  
> 更新：2026-05-16

## 阶段总览

| 阶段 | 状态 | 交付 | 验收 |
|------|------|------|------|
| **M1** | done | db + CLI + RSS/json_feed + run-once | `raw_items` 有新行 |
| M2 | pending | OpenRouter 分析 → `analyzed_items` | 新文章有分析 JSON |
| M3 | pending | digest + 飞书推送 | 飞书收到日报 |
| M4 | pending | html_list + browser_session | 4 种 type 可抓取 |
| M5a | pending | MCP tools | Cursor 可调 4 tools |

Web 端 **M5b** 见 `services/web/`，依赖 backend `api`（M3 后契约稳定为宜）。

## M1 子任务

| ID | 任务 | 路径 |
|----|------|------|
| M1.1 | SQLite schema + repository | `services/backend/db/` |
| M1.2 | config.yaml 与 import/export | `~/.ddo_pulse/`, CLI `config` |
| M1.3 | CLI init / source | `services/backend/cli/` |
| M1.4 | RSS + json_feed fetcher | `services/backend/core/.../fetchers/` |
| M1.5 | pipeline run-once | `services/backend/core/.../pipeline.py` |

## 依赖关系

```text
M1 → M2 → M3
M1 → M4
M2 → M5a
M3 → M5b (web)
```
