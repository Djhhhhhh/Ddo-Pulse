#!/bin/sh
set -e

# 错误捕获：失败时保持窗口打开
trap 'echo ""; echo "❌ 启动失败，请检查上方错误信息"; read -rp "按回车键关闭..." _' ERR

IMAGE_NAME="ddo-pulse"
CONTAINER_NAME="ddo-pulse"

# HOST_PORT: 宿主机端口（浏览器访问）
# API_PORT: 容器内部 API 端口
HOST_PORT="${DDO_PULSE_PORT:-8765}"
API_PORT="${DDO_PULSE_API_PORT:-8765}"

cd "$(dirname "$0")/.."

# 如果容器已在运行，先停止
if docker ps -q -f "name=${CONTAINER_NAME}" | grep -q .; then
    echo "容器 ${CONTAINER_NAME} 已在运行，正在重启..."
    docker stop "${CONTAINER_NAME}" >/dev/null 2>&1
    docker rm "${CONTAINER_NAME}" >/dev/null 2>&1
elif docker ps -aq -f "name=${CONTAINER_NAME}" | grep -q .; then
    docker rm "${CONTAINER_NAME}" >/dev/null 2>&1
fi

# 构建镜像
echo "正在构建镜像 ${IMAGE_NAME} ..."
docker build -f scripts/Dockerfile -t "${IMAGE_NAME}" .

# 启动容器
echo "正在启动容器 (宿主机端口: ${HOST_PORT}, 容器端口: ${API_PORT}) ..."
docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${HOST_PORT}:${API_PORT}" \
    -e DDO_PULSE_API_PORT="${API_PORT}" \
    -v ddo-pulse-data:/root/.ddo_pulse \
    "${IMAGE_NAME}"

echo ""
echo "✅ Ddo-Pulse 已启动"
echo "   访问地址: http://localhost:${HOST_PORT}"
echo "   查看日志: docker logs -f ${CONTAINER_NAME}"

# 保持窗口打开，方便查看输出
read -rp "按回车键关闭..." _
