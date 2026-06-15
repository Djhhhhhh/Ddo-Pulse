#!/usr/bin/env bash
# Ddo-Pulse 前端启动脚本

set -euo pipefail

# 设置 PATH（launchctl 环境 PATH 有限）
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="${PROJECT_ROOT}/services/web/frontend"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*"
    exit 1
}

# 检查 node_modules
check_deps() {
    if [[ ! -d "${WEB_DIR}/node_modules" ]]; then
        warn "node_modules 不存在，正在安装依赖..."
        cd "${WEB_DIR}"
        npm install
        info "依赖安装完成"
    fi
}

# 启动前端开发服务器
start_web() {
    check_deps
    info "正在启动 Ddo-Pulse 前端服务..."
    cd "${WEB_DIR}"
    exec npm run dev
}

start_web
