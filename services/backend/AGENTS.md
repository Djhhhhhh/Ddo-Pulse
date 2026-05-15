# backend

## 📌 作用

一句话描述：Ddo-Pulse **后端**（Python），包含 CLI、业务核心、REST API、MCP、数据库访问；与 `web` 端并列，构成「前后端两端」架构。

- 边界：所有 Python 代码集中在本目录；不包含 Vue 资源
- 调用关系：被用户/任务计划/MCP 客户端调用；向 `web` 提供 HTTP API

## 📂 目录结构

```text
services/backend/
├── cli/                    # 命令行：init / start / stop / health / run-once
│   └── ddo_pulse_cli/
├── core/                   # 抓取、OpenRouter 分析、digest、飞书（无 HTTP）
│   └── ddo_pulse_core/
│       ├── pipeline.py
│       ├── fetchers/
│       ├── analyzer/
│       └── notifier/
├── api/                    # FastAPI REST（供 web 调用）
│   └── ddo_pulse_api/
│       ├── main.py
│       └── routes/
├── mcp/                    # MCP Server 薄封装
│   └── ddo_pulse_mcp/
├── db/                     # SQLite schema + repository
│   ├── schema.sql
│   └── ddo_pulse_db/
└── AGENTS.md
```

**模块依赖（backend 内部）：**

```text
cli / mcp  →  core  →  db
api        →  core, db
```

## 🧠 Rules 自维护

**此章节指导 AI 如何自动维护本服务的规则。**

### Rules 文件位置
- 本服务规则：[.claude/rules/rules.md](.claude/rules/rules.md)

### 何时更新 Rules
- 🆕 新模块或跨子包调用约定
- 📁 `core` / `api` 目录变更

### 如何更新 Rules
1. 打开 [.claude/rules/rules.md](.claude/rules/rules.md)
2. 追加新规则（不要覆盖）

## ✅ 开发检查清单

提交前检查：
- [ ] Python 改动只在 `services/backend` 内
- [ ] `api` 不重复实现 `core` 已有逻辑
- [ ] schema 变更已同步 `docs/mvp.md` 与 `db/schema.sql`

## 🚫 禁止

硬性红线：
- ❌ 在 `services/web` 下写 Python 或改 Vue 业务（除非明确全栈任务）
- ❌ `core` 依赖 FastAPI / Vue
- ❌ 将 `~/.ddo_pulse` 数据库文件提交到 git

## 🕒 最后更新时间

2026-05-16 — M1 已实现：db、CLI、RSS/json_feed、run-once
