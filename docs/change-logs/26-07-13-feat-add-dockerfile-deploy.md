# 变更日志

**提交信息**: feat(docker): 添加 Dockerfile 支持容器化部署
**分支**: feat/2026-07-13-add-dockerfile
**日期**: 2026-07-13
**作者**: Djhhh

## 变更文件
- scripts/Dockerfile (added)
- scripts/docker-entrypoint.sh (added)
- scripts/docker-start.sh (added)
- scripts/docker-stop.sh (added)
- services/backend/api/ddo_pulse_api/main.py (modified)
- docs/feat/2026-07-13-add-dockerfile/ (added - 流水线产物)

## 统计
- 新增文件: 17
- 修改文件: 1
- 删除文件: 0
- 代码行数: +825 / -2

## 描述
在 scripts/ 目录下添加 Dockerfile 及辅助脚本，支持通过 Docker Desktop 一键部署项目。
- 多阶段构建：node:20-alpine 构建前端 + python:3.11-slim 运行后端
- 添加 SPA 路由兜底中间件，解决刷新 404 问题
- 支持自定义端口（DDO_PULSE_PORT / DDO_PULSE_API_PORT）
