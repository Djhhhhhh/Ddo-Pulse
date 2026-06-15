# Ddo-Pulse 快速启动脚本

## 目录结构

```
Ddo-Pulse/
├── .env/                    # Python 虚拟环境
├── scripts/
│   ├── start.sh            # 快速启动脚本
│   └── README.md           # 本文档
└── ...
```

## 快速开始

### 1. 初始化项目

首次使用时，需要初始化项目：

```bash
./scripts/start.sh install   # 安装依赖
./scripts/start.sh cli init  # 初始化数据库和配置
```

### 2. 启动服务

```bash
# 启动 API 服务
./scripts/start.sh api

# 运行 CLI 命令
./scripts/start.sh cli --help
./scripts/start.sh cli run-once
./scripts/start.sh cli source list

# 启动 MCP 服务
./scripts/start.sh mcp
```

## 使用 lazyctl 管理服务

服务已注册到 lazyctl，可以使用 TUI 界面管理：

```bash
lazyctl
```

在 lazyctl 中：
- 按 `a` 添加新服务
- 按 `s` 启动/停止选中的服务
- 按 `r` 重启服务
- 按 `d` 删除服务
- 按 `enter` 查看服务详情

### 已注册的服务

- **com.ddo-pulse.api**: Ddo-Pulse API 服务

服务配置文件位置：`~/Library/LaunchAgents/com.ddo-pulse.api.plist`

## 手动管理服务

如果不使用 lazyctl，也可以手动管理：

```bash
# 启动服务
launchctl load ~/Library/LaunchAgents/com.ddo-pulse.api.plist

# 停止服务
launchctl unload ~/Library/LaunchAgents/com.ddo-pulse.api.plist

# 查看服务状态
launchctl list | grep ddo-pulse

# 查看日志
log show --predicate 'process == "start.sh"' --last 1m
```

## 配置文件

- **主配置**: `~/.ddo_pulse/config.yaml`
- **Web 配置**: `~/.ddo_pulse/web.yaml`
- **数据库**: `~/.ddo_pulse/ddo_pulse.db`

## 端口配置

默认端口：
- API 服务: `127.0.0.1:8765`
- 前端开发服务器: `127.0.0.1:5173`

可以在 `~/.ddo_pulse/web.yaml` 中修改端口配置。

## 故障排除

### 端口被占用

```bash
# 查看占用端口的进程
lsof -i :8765

# 停止占用端口的进程
kill -9 <PID>
```

### 数据库错误

```bash
# 重新初始化数据库
./scripts/start.sh cli init
```

### 查看日志

```bash
# API 服务日志
./scripts/start.sh api 2>&1 | tee api.log

# launchd 服务日志
log show --predicate 'process == "start.sh"' --last 5m
```
