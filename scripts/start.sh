#!/usr/bin/env bash
# Ddo-Pulse 启动脚本（前后端一体）
# 用法: ./scripts/start.sh [--api-only] [--frontend-only]

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.env"
VENV_PYTHON="${VENV_DIR}/bin/python3"
FRONTEND_DIR="${PROJECT_ROOT}/services/web/frontend"
PID_FILE="${PROJECT_ROOT}/.ddo_pulse.pid"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
tag()   { echo -e "${CYAN}[$1]${NC} $*"; }

# ── 参数解析 ──────────────────────────────────────────────────────────

RUN_API=true
RUN_FRONTEND=true

for arg in "$@"; do
    case "$arg" in
        --api-only)      RUN_FRONTEND=false ;;
        --frontend-only) RUN_API=false ;;
        --help|-h)
            echo "用法: $(basename "$0") [--api-only] [--frontend-only]"
            echo ""
            echo "选项:"
            echo "  --api-only        仅启动后端 API 服务"
            echo "  --frontend-only   仅启动前端 Vite 开发服务器"
            echo "  (无参数)          同时启动前后端"
            exit 0
            ;;
        *) error "未知参数: $arg" ;;
    esac
done

# ── 环境检查 ──────────────────────────────────────────────────────────

if [[ ! -d "${VENV_DIR}" ]]; then
    error "虚拟环境不存在，请先运行: ./scripts/install.sh"
fi

if [[ "${RUN_FRONTEND}" == true ]]; then
    if [[ ! -d "${FRONTEND_DIR}/node_modules" ]]; then
        error "前端依赖未安装，请先运行: ./scripts/install.sh --with-frontend"
    fi
    # Vite 6 需要 Node.js 18+
    if command -v node &>/dev/null; then
        NODE_MAJOR=$(node -p 'process.version.split(".")[0].replace("v","")' 2>/dev/null || echo "0")
        if [[ "${NODE_MAJOR}" -lt 18 ]]; then
            error "Vite 6 需要 Node.js 18+，当前版本: $(node -v)\n请升级: nvm install 22 && nvm use 22"
        fi
    else
        error "未找到 Node.js，请先安装"
    fi
fi

# ── 清理函数 ──────────────────────────────────────────────────────────

PIDS=()

cleanup() {
    echo ""
    info "正在停止服务..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "${pid}" 2>/dev/null; then
            kill "${pid}" 2>/dev/null || true
        fi
    done
    rm -f "${PID_FILE}"
    info "已停止"
}

trap cleanup EXIT INT TERM

# ── 启动后端 API ─────────────────────────────────────────────────────

if [[ "${RUN_API}" == true ]]; then
    info "启动 Ddo-Pulse API 服务..."
    cd "${PROJECT_ROOT}"
    "${VENV_PYTHON}" -m ddo_pulse_api.main &
    API_PID=$!
    PIDS+=("${API_PID}")
    echo "${API_PID}" > "${PID_FILE}"
    tag "API" "PID: ${API_PID}"
fi

# ── 启动前端 Vite ────────────────────────────────────────────────────

if [[ "${RUN_FRONTEND}" == true ]]; then
    info "启动前端开发服务器..."
    cd "${FRONTEND_DIR}"
    npx vite --host &
    VITE_PID=$!
    PIDS+=("${VITE_PID}")
    tag "Vite" "PID: ${VITE_PID}"
fi

# ── 等待 ──────────────────────────────────────────────────────────────

echo ""
info "✅ 服务已启动"
[[ "${RUN_API}" == true ]]      && echo "  API:    http://localhost:8765"
[[ "${RUN_FRONTEND}" == true ]] && echo "  前端:   http://localhost:5173"
echo ""
info "按 Ctrl+C 停止所有服务"
echo ""

wait
