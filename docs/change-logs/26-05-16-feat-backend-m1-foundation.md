# 变更日志

**提交信息**: feat(backend): 实现 M1 基础设施（db、CLI、RSS 抓取、run-once）
**分支**: （提交时自动填写）
**日期**: 2026-05-16
**作者**: （提交时自动填写）

## 变更文件

### 新增
- `pyproject.toml` — 项目依赖与 CLI 入口
- `docs/mvp.md` — MVP 产品与技术规格
- `docs/feat/`、`docs/fix/` — 需求与修复文档目录
- `docs/change-logs/` — 变更日志
- `services/backend/` — 后端：db、core、cli、api/mcp 占位
- `services/web/` — 前端：Vue 骨架、DESIGN.md
- `services/*/AGENTS.md`、`SERVICES_INDEX.md`
- `skills/` — file-index、check-todo、git-push
- `tests/` — 单元/集成测试

### 主要能力
- SQLite schema 与 repository（`~/.ddo_pulse`）
- CLI：`init`、`source`、`config`、`run-once`
- RSS/json_feed 抓取与 pipeline
- OpenRouter、飞书、Web 等规格写入 mvp.md

## 统计

- 新增文件: 50+（初版仓库）
- 修改文件: 0
- 删除文件: 0

## 描述

完成 Ddo-Pulse 仓库初始化与 Backend M1：配置本地化目录、订阅源管理、Feed 抓取落库；两端架构 `services/web` + `services/backend`。
