# ============================================================
# Ddo-Pulse — 单文件容器化部署
# ============================================================
# 构建：docker build -f scripts/Dockerfile -t ddo-pulse .
# 运行：docker run -d -p 8765:8765 -v ddo-pulse-data:/root/.ddo_pulse ddo-pulse
# Docker Desktop：Build Image 选择此文件，上下文设为项目根目录
# ============================================================

# ---- Stage 1: 前端构建 ----
FROM node:20-alpine AS frontend-builder

WORKDIR /app
COPY services/web/frontend/ ./
RUN npm ci && npm run build

# ---- Stage 2: 运行时 ----
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# 拷贝项目文件
COPY . .

# 拷贝前端构建产物
COPY --from=frontend-builder /app/dist ./services/web/frontend/dist

# 安装 Python 依赖
RUN pip install --no-cache-dir .

# 修复安装后路径问题：
# 1. main.py 中 _SERVICES_ROOT = parents[3]，pip 安装后解析到 /usr/local/lib/
#    需要把前端 dist 放到 /usr/local/lib/web/frontend/dist/
# 2. repository.py 中 _SCHEMA_FILE = parent.parent / "schema.sql"，
#    pip 安装后解析到 site-packages/schema.sql
RUN SITE_PKG=$(python -c "import ddo_pulse_api.main, pathlib; print(pathlib.Path(ddo_pulse_api.main.__file__).resolve().parents[3])") && \
    mkdir -p "${SITE_PKG}/web/frontend" && \
    cp -r /app/services/web/frontend/dist "${SITE_PKG}/web/frontend/dist" && \
    DB_SITE=$(python -c "import ddo_pulse_db.repository, pathlib; print(pathlib.Path(ddo_pulse_db.repository.__file__).resolve().parent.parent)") && \
    cp /app/services/backend/db/schema.sql "${DB_SITE}/schema.sql"

# 数据持久化目录
VOLUME /root/.ddo_pulse

# 暴露 API 端口
EXPOSE 8765

# 拷贝并设置入口脚本
COPY scripts/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
