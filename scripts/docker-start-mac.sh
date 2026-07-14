#!/bin/bash
# Ddo-Pulse Docker 启动脚本 (macOS)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 错误处理
trap 'echo -e "\n${RED}❌ 启动失败，请检查上方错误信息${NC}"; exit 1' ERR

IMAGE_NAME="ddo-pulse"
CONTAINER_NAME="ddo-pulse"

# HOST_PORT: 宿主机端口（浏览器访问）
# API_PORT: 容器内部 API 端口
HOST_PORT="${DDO_PULSE_PORT:-8765}"
API_PORT="${DDO_PULSE_API_PORT:-8765}"

cd "$(dirname "$0")/.."

echo "🐳 Ddo-Pulse Docker 启动脚本 (macOS)"
echo "===================================="
echo ""

# 检测 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    echo ""
    echo "请先安装 Docker Desktop for Mac:"
    echo "  https://docs.docker.com/desktop/install/mac-install/"
    echo ""
    echo "或者使用 Homebrew 安装:"
    echo "  brew install --cask docker"
    exit 1
fi

# 检测 Docker daemon 是否运行
echo "🔍 检测 Docker daemon..."
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker daemon 未运行${NC}"
    echo ""

    # 尝试启动 Docker Desktop
    if [ -d "/Applications/Docker.app" ]; then
        echo "🚀 正在启动 Docker Desktop..."
        open -a Docker

        # 等待 Docker daemon 启动
        echo "⏳ 等待 Docker daemon 启动..."
        RETRIES=0
        MAX_RETRIES=30
        while ! docker info &> /dev/null; do
            RETRIES=$((RETRIES + 1))
            if [ $RETRIES -ge $MAX_RETRIES ]; then
                echo -e "${RED}❌ Docker daemon 启动超时${NC}"
                echo ""
                echo "请手动启动 Docker Desktop，然后重试"
                exit 1
            fi
            sleep 2
        done
        echo -e "${GREEN}✅ Docker daemon 已启动${NC}"
    else
        echo -e "${RED}❌ 未找到 Docker Desktop${NC}"
        echo ""
        echo "请安装 Docker Desktop for Mac:"
        echo "  https://docs.docker.com/desktop/install/mac-install/"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Docker daemon 正在运行${NC}"
fi

echo ""

# 如果容器已在运行，先停止
if docker ps -q -f "name=${CONTAINER_NAME}" | grep -q .; then
    echo "⚠️  容器 ${CONTAINER_NAME} 已在运行，正在重启..."
    docker stop "${CONTAINER_NAME}" >/dev/null 2>&1
    docker rm "${CONTAINER_NAME}" >/dev/null 2>&1
elif docker ps -aq -f "name=${CONTAINER_NAME}" | grep -q .; then
    docker rm "${CONTAINER_NAME}" >/dev/null 2>&1
fi

# 构建镜像
echo "🔨 正在构建镜像 ${IMAGE_NAME} ..."
docker build -f scripts/Dockerfile -t "${IMAGE_NAME}" .

# 创建报告目录
REPORTS_DIR="$HOME/.ddo_pulse/reports"
mkdir -p "${REPORTS_DIR}"

# 启动容器
echo "🚀 正在启动容器 (宿主机端口: ${HOST_PORT}, 容器端口: ${API_PORT}) ..."
docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${HOST_PORT}:${API_PORT}" \
    -e DDO_PULSE_API_PORT="${API_PORT}" \
    -v ddo-pulse-data:/root/.ddo_pulse \
    -v "${REPORTS_DIR}:/root/.ddo_pulse/reports" \
    "${IMAGE_NAME}"

echo ""
echo -e "${GREEN}✅ Ddo-Pulse 已启动${NC}"
echo ""
echo "📌 访问地址: http://localhost:${HOST_PORT}"
echo "📊 报告目录: ${REPORTS_DIR}"
echo "📝 查看日志: docker logs -f ${CONTAINER_NAME}"
echo ""
echo "常用命令:"
echo "  停止服务: ./scripts/docker-stop-mac.sh"
echo "  查看日志: docker logs -f ${CONTAINER_NAME}"
echo "  进入容器: docker exec -it ${CONTAINER_NAME} /bin/bash"
echo ""
