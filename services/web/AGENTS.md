# web

## 📌 作用

一句话描述：Ddo-Pulse **Web 端**，Vue 3 + Vite 单页应用，提供 Dashboard、过往文章列表、文章详情与配置管理。

- 边界：仅前端 UI 与对后端的 HTTP 调用；不直连 SQLite、不实现抓取/LLM
- 调用关系：请求 `backend` 暴露的 REST API（开发时 Vite 代理 `/api`）

## 📂 目录结构

```text
services/web/
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.ts
│       ├── router/
│       ├── views/         # Dashboard, ArticleList, ArticleDetail, Settings
│       ├── api/           # 请求封装
│       └── components/
└── AGENTS.md
```

## 🧠 Rules 自维护

**此章节指导 AI 如何自动维护本服务的规则。**

### Rules 文件位置
- 本服务规则：[.claude/rules/rules.md](.claude/rules/rules.md)

### 何时更新 Rules
- 🆕 新增页面或路由
- 📋 改变组件/状态管理约定

### 如何更新 Rules
1. 打开 [.claude/rules/rules.md](.claude/rules/rules.md)
2. 追加新规则（不要覆盖）

## ✅ 开发检查清单

提交前检查：
- [ ] 本次修改只在 `services/web` 内
- [ ] 新页面已注册路由
- [ ] 与 `backend/api` 接口字段一致

## 🚫 禁止

硬性红线：
- ❌ 在前端存储 OpenRouter API Key 或飞书 Webhook
- ❌ 绕过 backend 直接抓取外部站点
- ❌ 修改 `services/backend` 内 Python 代码

## 🕒 最后更新时间

2026-05-16 12:00:00
