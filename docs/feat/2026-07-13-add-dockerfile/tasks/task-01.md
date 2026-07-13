# Task 01: 创建 scripts/Dockerfile

## 目标

在 `scripts/` 目录下创建一个多阶段构建的 Dockerfile，使项目可通过 Docker Desktop 一键部署。

## 关联验收点

- G1（Dockerfile 文件规范）
- G2（构建验证）
- G3（运行时验证）
- G4（Docker Desktop 兼容性）

## 实现要点

1. **Stage 1 — frontend-builder**：
   - 基础镜像 `node:20-alpine`
   - 拷贝 `services/web/frontend/` 到工作目录
   - 执行 `npm ci && npm run build`

2. **Stage 2 — runtime**：
   - 基础镜像 `python:3.11-slim`
   - 拷贝整个项目
   - 拷贝 Stage 1 的前端产物到 `services/web/frontend/dist/`
   - `pip install --no-cache-dir .`
   - `VOLUME /root/.ddo_pulse`
   - `EXPOSE 8765`
   - `ENTRYPOINT ["ddo-pulse-api"]`

## 约束

- 仅新增 `scripts/Dockerfile` 一个文件
- 不修改项目已有代码
- 构建上下文为项目根目录
