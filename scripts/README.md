# Ddo-Pulse 脚本目录

## 脚本清单

| 脚本 | 用途 |
|------|------|
| `install.sh` | 安装项目依赖（Python 虚拟环境 + 可选前端） |
| `uninstall.sh` | 卸载项目（删除虚拟环境、node_modules、可选数据目录） |
| `start.sh` | 启动前后端服务 |

## 快速开始

### 1. 安装

```bash
# 仅安装 Python 依赖
./scripts/install.sh

# 同时安装前端依赖
./scripts/install.sh --with-frontend
```

### 2. 启动

```bash
# 同时启动前后端
./scripts/start.sh

# 仅启动后端 API
./scripts/start.sh --api-only

# 仅启动前端
./scripts/start.sh --frontend-only
```

### 3. 卸载

```bash
# 卸载（交互式确认是否删除数据）
./scripts/uninstall.sh

# 卸载但保留数据目录
./scripts/uninstall.sh --keep-data
```

## 端口配置

默认端口：
- API 服务: `http://localhost:8765`
- 前端开发服务器: `http://localhost:5173`

可以在 `~/.ddo_pulse/web.yaml` 中修改 API 端口配置。

## 配置文件

- **主配置**: `~/.ddo_pulse/config.yaml`
- **Web 配置**: `~/.ddo_pulse/web.yaml`
- **数据库**: `~/.ddo_pulse/ddo_pulse.db`

## 故障排除

### 端口被占用

```bash
lsof -i :8765
kill -9 <PID>
```

### 重新安装

```bash
./scripts/uninstall.sh --keep-data
./scripts/install.sh --with-frontend
```
