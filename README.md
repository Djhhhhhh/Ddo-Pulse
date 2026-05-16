# Ddo-Pulse

[![Vue](https://img.shields.io/badge/Vue-0A0A0A?style=flat-square&logo=vue.js&logoColor=FFD700)](https://vuejs.org/)
[![Python](https://img.shields.io/badge/Python-0A0A0A?style=flat-square&logo=python&logoColor=FFD700)](https://www.python.org/)

> **Ddo-Pulse** 是一款轻量化的**本机信息聚合**工具：按配置定时抓取博客与订阅源，经 **OpenRouter** 等大模型筛选、分类与中文摘要后，支持**飞书推送日报**，并在**本地 Web** 浏览 Dashboard、文章与配置。

## ✨ 项目亮点

- **本机优先、数据可控**：默认数据目录 `~/.ddo_pulse`，SQLite + 可编辑 `config.yaml`，**不依赖 `.env` 存密钥**
- **触达与阅读**：飞书 Webhook + 本地 Web（设置页、运行日志、文章列表等）
- **可扩展交互**：可选 **MCP Server**（`pip install -e ".[mcp]"`），便于与 Cursor 等工具集成

## 🚀 核心能力

- **初始化与配置**：`ddo-pulse init` 创建数据目录、默认配置与数据库结构；配置可通过 **Web `/settings`**、**CLI** 或编辑 `**~/.ddo_pulse/config.yaml`** 同步
- **订阅与抓取**：RSS / JSON Feed / HTML 列表等（详见 [docs/mvp.md](docs/mvp.md)）；可选 Playwright 相关能力（`pip install -e ".[browser]"`）
- **LLM 分析流水线**：基于 Profile 的质量分、分类、中文摘要；支持按任务配置提示词与精选阈值
- **Digest 与飞书**：生成每日 Digest；按任务配置推送至飞书
- **HTTP API**：FastAPI 提供 REST 接口，默认见 `~/.ddo_pulse/web.yaml` 中 `api` 段（常见默认端口 **8765**）
- **本地 Web UI**：Vue 3 + Vite 开发态代理 `/api`；生产可由 API 托管 `frontend/dist` 静态资源
- **MCP**：`ddo-pulse mcp` 以 stdio 方式暴露薄封装能力（需可选依赖）

## 🎯 适用场景

- 个人技术阅读聚合与「每日精选」
- 需要 LLM 降噪、打分与中文短摘要后再推送
- 希望配置与数据集中在用户目录、便于备份与迁移

## 📦 发版与文档


| 版本    | 说明                                           |
| ----- | -------------------------------------------- |
| 1.0.0 | 当前发布版本； |

## 🛠 技术栈


| 模块        | 技术                          |
| --------- | --------------------------- |
| CLI / 领域层 | Python 3.11+、Typer          |
| API       | FastAPI、Uvicorn             |
| 存储        | SQLite                      |
| 前端        | Vue 3、Vite、TypeScript       |
| LLM 接入    | OpenAI 兼容客户端（默认 OpenRouter） |


## ⚡ 快速开始

按顺序完成下面四步即可在本机跑起来（日常只用 `**init` → `dev` → `stop`**；其他用法见 `ddo-pulse --help` 与 [docs/mvp.md](docs/mvp.md)）。

### 1. 安装

- **Python 3.11+**、**Node.js**（安装前端依赖并运行 Vite）
- 在仓库根目录：

```bash
pip install -e .
```

### 2. 通过 ddo-pulse 初始化

```bash
ddo-pulse init
```

会在用户目录创建 `**~/.ddo_pulse**`（Windows 为 `**%USERPROFILE%\.ddo_pulse**`），包含配置、数据库与 `web.yaml` 等。

### 3. 通过 ddo-pulse dev 启动

```bash
ddo-pulse dev
```

同时启动 **FastAPI** 与 **Vite**。首次若缺少 `node_modules`，可执行：

```bash
ddo-pulse dev --install
```

端口和代理以 `**~/.ddo_pulse/web.yaml**` 为准（`dev` 会同步前端侧 Vite 配置）；浏览器访问终端里 Vite 提示的本地地址即可打开 Web UI。

### 4. 通过 ddo-pulse stop 停止

在**另一个终端**执行（用于结束由 `dev` 拉起的进程；若在运行 `dev` 的窗口已 `Ctrl+C`，一般也会一并退出）：

```bash
ddo-pulse stop
```

说明：`stop` 依赖 `**~/.ddo_pulse/dev_state.json**`（由 `dev` 写入）。若文件不存在，请先使用 `dev` 启动，或表示开发进程已结束。

## ⚙️ 配置说明

### 根目录与用户数据

- **数据目录**：默认 `~/.ddo_pulse`
- **主配置**：`~/.ddo_pulse/config.yaml`（可与 Web / CLI 互相导入导出）
- **Web 前后端开发/端口**：`~/.ddo_pulse/web.yaml`，修改后若在用的不是 `ddo-pulse dev` 的自动同步，可执行 `**ddo-pulse web sync`** 更新前端本地 env（见 `ddo-pulse web --help`）
- `**dev_state.json**`：由 `**ddo-pulse dev**` 写入，供 `**ddo-pulse stop**` 结束子进程；勿手改

### 凭证与模型

- **OpenRouter API Key、飞书 Webhook** 等通过 **Web 设置页** 或 **CLI / YAML** 写入数据库与配置，**不使用 `.env` 作为配置来源**（与产品规格一致）。

详细字段与边界见 **[docs/mvp.md](docs/mvp.md)**（项目 readme 在 `pyproject.toml` 中亦指向该文档）。

## 📁 项目结构

```text
ddo_pulse/
├── docs/
│   ├── mvp.md                 # 产品与技术规格（权威）
│   └── change-logs/           # 变更记录
├── scripts/                   # 启动/停止等辅助脚本
├── services/
│   ├── backend/               # Python：cli / core / api / db / mcp
│   └── web/
│       └── frontend/          # Vue 3 + Vite
├── pyproject.toml
├── LICENSE
└── README.md
```

## 🔧 开发与调试

- **本地联调**：与「快速开始」一致，使用 `**ddo-pulse dev`**；需要结束进程时 `**ddo-pulse stop**`（或运行 `dev` 的终端内 `Ctrl+C`）
- **自动化测试**：`pip install -e ".[dev]"` 后执行 `pytest`（配置见 `pyproject.toml`）
- **前端**：`services/web/frontend`，设计说明见 [services/web/DESIGN.md](services/web/DESIGN.md)
- **路径约定**：用户数据在 `Path.home() / ".ddo_pulse"`，勿硬编码盘符（详见 `docs/mvp.md`）

## ❓ 常见问题

### `ddo-pulse stop` 提示没有会话文件？

`stop` 只适用于通过 `**ddo-pulse dev`** 启动、并写入了 `**~/.ddo_pulse/dev_state.json**` 的场景。若你曾单独运行 `ddo-pulse api` 或脚本启动服务，请自行结束对应进程，或统一改用 `dev` / `stop`。

### 前端连不上 API？

检查 API 是否监听 `web.yaml` 中 `api` 地址；开发环境下确认 Vite 代理与 `.ddo-pulse.env.json` / `web.yaml` 中 `dev_server.api_proxy` 一致。修改 `web.yaml` 后可执行 `**ddo-pulse web sync**`（见 `ddo-pulse --help`）再重启 `dev`。

## 🤝 贡献

欢迎提交 Issue 与 PR。建议提交前：

- 遵守各端 AGENTS.md 中的约束
- 对应更新文档或变更记录（如适用）

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。