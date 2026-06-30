#!/usr/bin/env bash
# Ddo-Pulse 卸载脚本
# 用法: ./scripts/uninstall.sh [--keep-data]

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.env"
DATA_DIR="${HOME}/.ddo_pulse"
FRONTEND_DIR="${PROJECT_ROOT}/services/web/frontend"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

KEEP_DATA=false
for arg in "$@"; do
    case "$arg" in
        --keep-data) KEEP_DATA=true ;;
        --help|-h)
            echo "用法: $(basename "$0") [--keep-data]"
            echo ""
            echo "选项:"
            echo "  --keep-data  保留 ~/.ddo_pulse 数据目录和数据库"
            exit 0
            ;;
        *) error "未知参数: $arg" ;;
    esac
done

# ── 停止运行中的服务 ─────────────────────────────────────────────────

info "检查并停止运行中的服务..."
if [[ -f "${PROJECT_ROOT}/.ddo_pulse.pid" ]]; then
    PID=$(cat "${PROJECT_ROOT}/.ddo_pulse.pid")
    if kill -0 "${PID}" 2>/dev/null; then
        info "停止 Ddo-Pulse 服务 (PID: ${PID})..."
        kill "${PID}" 2>/dev/null || true
        sleep 1
    fi
    rm -f "${PROJECT_ROOT}/.ddo_pulse.pid"
fi

# ── 删除虚拟环境 ─────────────────────────────────────────────────────

if [[ -d "${VENV_DIR}" ]]; then
    info "删除 Python 虚拟环境..."
    rm -rf "${VENV_DIR}"
    info "虚拟环境已删除"
else
    info "虚拟环境不存在，跳过"
fi

# ── 删除前端 node_modules ────────────────────────────────────────────

if [[ -d "${FRONTEND_DIR}/node_modules" ]]; then
    info "删除前端 node_modules..."
    rm -rf "${FRONTEND_DIR}/node_modules"
    info "node_modules 已删除"
fi

# ── 删除构建产物 ─────────────────────────────────────────────────────

if [[ -d "${FRONTEND_DIR}/dist" ]]; then
    info "删除前端构建产物..."
    rm -rf "${FRONTEND_DIR}/dist"
fi

# ── 处理数据目录 ─────────────────────────────────────────────────────

if [[ "${KEEP_DATA}" == true ]]; then
    warn "保留数据目录: ${DATA_DIR}"
else
    if [[ -d "${DATA_DIR}" ]]; then
        warn "即将删除数据目录: ${DATA_DIR}"
        read -p "确认删除？(y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "${DATA_DIR}"
            info "数据目录已删除"
        else
            warn "保留数据目录"
        fi
    fi
fi

# ── 清理临时文件 ─────────────────────────────────────────────────────

rm -f "${PROJECT_ROOT}/.ddo_pulse.pid"

echo ""
info "✅ 卸载完成！"
if [[ "${KEEP_DATA}" == true ]]; then
    echo "  数据目录保留于: ${DATA_DIR}"
fi
echo "  项目源码未删除，可手动删除: ${PROJECT_ROOT}"
