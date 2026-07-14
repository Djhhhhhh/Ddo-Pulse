# Task 16: Docker 配置

## 关联验收点
- G9: Docker 数据卷挂载

## 任务描述
更新 Docker 配置以支持报告目录挂载。

## 具体步骤

1. 更新 `docker-compose.yml`：
   - 添加 `~/.ddo_pulse/reports/` 卷挂载
   - 确保容器内可写入

2. 更新 `Dockerfile`：
   - 确保 Playwright 依赖安装（可选）

## 输出文件
- 修改 `docker-compose.yml`
- 修改 `Dockerfile`（如需要）

## docker-compose.yml 变更
```yaml
version: '3.8'

services:
  ddo-pulse:
    build: .
    volumes:
      - ~/.ddo_pulse:/root/.ddo_pulse
      - ~/.ddo_pulse/reports:/root/.ddo_pulse/reports  # 明确挂载报告目录
    ports:
      - "8765:8765"
    environment:
      - TZ=Asia/Shanghai
```

## 验证命令
```bash
grep -q "reports" docker-compose.yml && echo "Volume mount configured"
docker-compose config 2>/dev/null | grep -q "reports" && echo "Docker config OK" || echo "Docker not available"
```
