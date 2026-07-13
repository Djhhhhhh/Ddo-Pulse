#!/bin/sh
set -e

DATA_DIR="${HOME}/.ddo_pulse"
API_PORT="${DDO_PULSE_API_PORT:-8765}"

# 初始化数据目录并确保 schema 完整（idempotent）
echo "[entrypoint] Ensuring data directory and schema at $DATA_DIR ..."
ddo-pulse init --force

# 确保 web.yaml 使用 0.0.0.0 以便容器外可访问，并使用指定端口
WEB_CONFIG="$DATA_DIR/web.yaml"
echo "[entrypoint] Writing web config with host=0.0.0.0, port=${API_PORT} ..."
mkdir -p "$DATA_DIR"
cat > "$WEB_CONFIG" << EOF
api:
  host: 0.0.0.0
  port: ${API_PORT}
dev_server:
  port: 5173
  api_proxy: http://0.0.0.0:${API_PORT}
app:
  title: Ddo-Pulse
  api_base: /api
EOF

echo "[entrypoint] Starting Ddo-Pulse API on 0.0.0.0:${API_PORT} ..."
exec ddo-pulse-api
