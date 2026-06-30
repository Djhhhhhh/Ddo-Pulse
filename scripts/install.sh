#!/usr/bin/env bash
# Ddo-Pulse 安装脚本
# 用法: ./scripts/install.sh [--with-frontend]

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.env"
VENV_PYTHON="${VENV_DIR}/bin/python3"
VENV_PIP="${VENV_DIR}/bin/pip"
FRONTEND_DIR="${PROJECT_ROOT}/services/web/frontend"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

WITH_FRONTEND=false
for arg in "$@"; do
    case "$arg" in
        --with-frontend) WITH_FRONTEND=true ;;
        --help|-h)
            echo "用法: $(basename "$0") [--with-frontend]"
            echo ""
            echo "选项:"
            echo "  --with-frontend  同时安装前端依赖 (npm install)"
            exit 0
            ;;
        *) error "未知参数: $arg" ;;
    esac
done

# ── Python 版本检查 ──────────────────────────────────────────────────

PYTHON_CMD=""
for cmd in python3.14 python3.13 python3.12 python3.11 python3; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [[ "$major" -ge 3 && "$minor" -ge 11 ]]; then
            PYTHON_CMD="$cmd"
            info "使用 Python: $cmd ($ver)"
            break
        fi
    fi
done

if [[ -z "${PYTHON_CMD}" ]]; then
    error "需要 Python 3.11+，当前未找到。请安装 Python 3.11 或更高版本。"
fi

# ── Python 虚拟环境 ──────────────────────────────────────────────────

if [[ ! -d "${VENV_DIR}" ]]; then
    info "创建 Python 虚拟环境..."
    "${PYTHON_CMD}" -m venv "${VENV_DIR}"
    info "虚拟环境已创建: ${VENV_DIR}"
else
    info "虚拟环境已存在: ${VENV_DIR}"
fi

info "安装 Python 依赖..."
"${VENV_PIP}" install --upgrade pip
info "pip 已升级，开始安装项目依赖（可能需要几分钟）..."
"${VENV_PIP}" install -e "${PROJECT_ROOT}[dev]"
info "Python 依赖安装完成"

# ── 前端依赖（可选）──────────────────────────────────────────────────

if [[ "${WITH_FRONTEND}" == true ]]; then
    if [[ ! -d "${FRONTEND_DIR}" ]]; then
        error "前端目录不存在: ${FRONTEND_DIR}"
    fi
    if ! command -v npm &>/dev/null; then
        error "未找到 npm，请先安装 Node.js"
    fi
    # Vite 6 需要 Node.js 18+
    NODE_MAJOR=$(node -p 'process.version.split(".")[0].replace("v","")' 2>/dev/null || echo "0")
    if [[ "${NODE_MAJOR}" -lt 18 ]]; then
        error "Vite 6 需要 Node.js 18+，当前版本: $(node -v)\n请升级: nvm install 22 && nvm use 22"
    fi
    info "安装前端依赖..."
    cd "${FRONTEND_DIR}"
    npm install --silent
    info "前端依赖安装完成"
fi

# ── 初始化数据目录 ────────────────────────────────────────────────────

info "初始化数据目录..."
"${VENV_PYTHON}" -m ddo_pulse_cli.main init || warn "初始化跳过（可稍后运行 ddo-pulse init）"

echo ""
info "✅ 安装完成！"
echo ""
echo "  启动服务:  ./scripts/start.sh"
echo "  卸载项目:  ./scripts/uninstall.sh"
