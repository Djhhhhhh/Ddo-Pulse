#!/bin/bash
# Ddo-Pulse Docker 停止脚本 (macOS)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CONTAINER_NAME="ddo-pulse"

echo "🐳 Ddo-Pulse Docker 停止脚本 (macOS)"
echo "===================================="
echo ""

# 检测 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi

# 检测 Docker daemon 是否运行
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker daemon 未运行${NC}"
    echo "容器可能已经停止"
    exit 0
fi

# 停止并删除容器
if docker ps -q -f "name=${CONTAINER_NAME}" | grep -q .; then
    echo "⏹️  正在停止容器 ${CONTAINER_NAME} ..."
    docker stop "${CONTAINER_NAME}"
    docker rm "${CONTAINER_NAME}"
    echo ""
    echo -e "${GREEN}✅ Ddo-Pulse 已停止${NC}"
elif docker ps -aq -f "name=${CONTAINER_NAME}" | grep -q .; then
    docker rm "${CONTAINER_NAME}"
    echo ""
    echo -e "${GREEN}✅ 已清理停止的容器 ${CONTAINER_NAME}${NC}"
else
    echo -e "${YELLOW}ℹ️  容器 ${CONTAINER_NAME} 不存在${NC}"
fi

echo ""
