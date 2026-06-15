#!/usr/bin/env bash
# Ddo-Pulse 快速启动脚本
# 用法: ./scripts/start.sh [install|api|cli|mcp]

set -euo pipefail

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.env"
VENV_PYTHON="${VENV_DIR}/bin/python3"
VENV_PIP="${VENV_DIR}/bin/pip"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# 检查虚拟环境
check_venv() {
    if [[ ! -d "${VENV_DIR}" ]]; then
        warn "虚拟环境不存在，正在创建..."
        python3 -m venv "${VENV_DIR}"
        info "虚拟环境已创建: ${VENV_DIR}"
    fi
}

# 安装依赖
install_deps() {
    check_venv
    info "正在安装项目依赖..."
    "${VENV_PIP}" install --upgrade pip
    "${VENV_PIP}" install -e "${PROJECT_ROOT}[dev]"
    info "依赖安装完成"
}

# 启动 API 服务
start_api() {
    check_venv
    info "正在启动 Ddo-Pulse API 服务..."
    cd "${PROJECT_ROOT}"
    exec "${VENV_PYTHON}" -m ddo_pulse_api.main
}

# 启动 CLI
start_cli() {
    check_venv
    cd "${PROJECT_ROOT}"
    exec "${VENV_PYTHON}" -m ddo_pulse_cli.main "$@"
}

# 启动 MCP 服务
start_mcp() {
    check_venv
    info "正在启动 Ddo-Pulse MCP 服务..."
    cd "${PROJECT_ROOT}"
    exec "${VENV_PYTHON}" -m ddo_pulse_mcp.server
}

# 显示帮助
show_help() {
    cat << EOF
Ddo-Pulse 快速启动脚本

用法: $(basename "$0") <command> [args...]

命令:
    install     安装/更新项目依赖
    api         启动 API 服务 (默认端口 8765)
    cli         运行 CLI 命令 (后续参数传递给 CLI)
    mcp         启动 MCP 服务
    help        显示此帮助信息

示例:
    $(basename "$0") install        # 首次安装依赖
    $(basename "$0") api            # 启动 API 服务
    $(basename "$0") cli --help     # 查看 CLI 帮助
    $(basename "$0") mcp            # 启动 MCP 服务

EOF
}

# 主函数
main() {
    local command="${1:-help}"
    shift || true

    case "${command}" in
        install)
            install_deps
            ;;
        api)
            start_api
            ;;
        cli)
            start_cli "$@"
            ;;
        mcp)
            start_mcp
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "未知命令: ${command}\n运行 '$(basename "$0") help' 查看帮助"
            ;;
    esac
}

main "$@"
