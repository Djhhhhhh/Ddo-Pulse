#!/bin/sh

CONTAINER_NAME="ddo-pulse"

# 停止并删除容器
if docker ps -q -f "name=${CONTAINER_NAME}" | grep -q .; then
    echo "正在停止容器 ${CONTAINER_NAME} ..."
    docker stop "${CONTAINER_NAME}"
    docker rm "${CONTAINER_NAME}"
    echo "✅ Ddo-Pulse 已停止"
elif docker ps -aq -f "name=${CONTAINER_NAME}" | grep -q .; then
    docker rm "${CONTAINER_NAME}"
    echo "✅ 已清理停止的容器 ${CONTAINER_NAME}"
else
    echo "容器 ${CONTAINER_NAME} 不存在"
fi
