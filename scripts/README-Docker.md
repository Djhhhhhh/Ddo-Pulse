# Ddo-Pulse Docker 脚本说明

## 📁 脚本列表

| 脚本 | 平台 | 说明 |
|------|------|------|
| `docker-start-mac.sh` | macOS | 启动服务 |
| `docker-stop-mac.sh` | macOS | 停止服务 |
| `docker-start-win.bat` | Windows | 启动服务 |
| `docker-stop-win.bat` | Windows | 停止服务 |
| `Dockerfile` | 通用 | Docker 镜像构建文件 |
| `docker-entrypoint.sh` | 通用 | 容器入口脚本 |

## 🚀 使用方法

### macOS

```bash
# 启动服务
./scripts/docker-start-mac.sh

# 停止服务
./scripts/docker-stop-mac.sh
```

### Windows

```cmd
:: 启动服务
scripts\docker-start-win.bat

:: 停止服务
scripts\docker-stop-win.bat
```

## 🔧 功能特性

### Docker Daemon 自动检测

脚本会自动检测 Docker daemon 是否运行：

1. **检测 Docker 是否安装**
   - 如果未安装，提示安装链接

2. **检测 Docker daemon 是否运行**
   - 如果未运行，尝试自动启动 Docker Desktop
   - 等待最多 60 秒启动完成

3. **自动重启容器**
   - 如果容器已在运行，自动停止并重启

### 报告目录挂载

脚本会自动创建并挂载报告目录：

- **macOS:** `~/.ddo_pulse/reports/`
- **Windows:** `%USERPROFILE%\.ddo_pulse\reports\`

## 📋 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DDO_PULSE_PORT` | 8765 | 宿主机端口（浏览器访问） |
| `DDO_PULSE_API_PORT` | 8765 | 容器内部 API 端口 |

**使用示例：**

```bash
# 自定义端口
DDO_PULSE_PORT=9000 ./scripts/docker-start-mac.sh

# Windows
set DDO_PULSE_PORT=9000
scripts\docker-start-win.bat
```

## 📝 常用命令

```bash
# 查看容器日志
docker logs -f ddo-pulse

# 进入容器
docker exec -it ddo-pulse /bin/bash

# 查看容器状态
docker ps -f "name=ddo-pulse"

# 重启容器
docker restart ddo-pulse
```

## 🐛 常见问题

### 1. Docker daemon 未运行

**macOS:**
```bash
# 手动启动 Docker Desktop
open -a Docker
```

**Windows:**
```cmd
:: 手动启动 Docker Desktop
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

### 2. 端口被占用

```bash
# 查看端口占用
lsof -i :8765  # macOS
netstat -ano | findstr :8765  # Windows

# 使用其他端口
DDO_PULSE_PORT=9000 ./scripts/docker-start-mac.sh
```

### 3. 权限问题

**macOS:**
```bash
# 给脚本添加执行权限
chmod +x scripts/docker-start-mac.sh
chmod +x scripts/docker-stop-mac.sh
```

**Windows:**
- 以管理员身份运行命令提示符

### 4. 报告目录无法访问

```bash
# 检查报告目录
ls -la ~/.ddo_pulse/reports/  # macOS
dir %USERPROFILE%\.ddo_pulse\reports  # Windows

# 检查容器内报告目录
docker exec -it ddo-pulse ls -la /root/.ddo_pulse/reports/
```

## 📊 报告访问

启动服务后，可以通过以下方式访问报告：

### Web UI

```
http://localhost:8765/reports
```

### 本地文件

**macOS:**
```bash
open ~/.ddo_pulse/reports/
```

**Windows:**
```cmd
explorer %USERPROFILE%\.ddo_pulse\reports
```

### API

```bash
# 获取报告列表
curl http://localhost:8765/api/reports

# 获取报告详情
curl http://localhost:8765/api/reports/2026-07-14-083000
```
