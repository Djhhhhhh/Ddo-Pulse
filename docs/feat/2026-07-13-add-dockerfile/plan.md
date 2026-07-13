# Ddo-Pulse Dockerfile Plan

> 基于已确认的 spec.md 做技术决策。

---

## 1. 决策原则

| # | 原则 | 落地体现 |
|---|------|----------|
| P-1 | 单文件自包含 | 一个 Dockerfile 完成前端构建 + 后端打包 + 运行时配置 |
| P-2 | Docker Desktop 友好 | EXPOSE 声明端口，ENTRYPOINT 直接启动，无需额外参数 |
| P-3 | 镜像体积最小化 | 多阶段构建，运行时仅包含 Python 依赖和前端产物 |
| P-4 | 数据可持久化 | 通过 VOLUME 声明数据目录，Docker Desktop 可直接挂载 |

---

## 2. 整体架构

```
┌───────────────────────────────────────────────┐
│  Stage 1: frontend-builder (node:20-alpine)   │
│  ┌─────────────┐                              │
│  │ npm install  │──▶ npm run build ──▶ /dist  │
│  └─────────────┘                              │
└───────────────────────────────────────────────┘
                        │
                        │ COPY /dist
                        ▼
┌───────────────────────────────────────────────┐
│  Stage 2: runtime (python:3.11-slim)          │
│  ┌─────────────────────────────────────────┐  │
│  │ pip install .  (backend + dependencies) │  │
│  │ COPY frontend dist → services/web/...   │  │
│  │ VOLUME ~/.ddo_pulse (data persistence)  │  │
│  │ EXPOSE 8765                             │  │
│  │ ENTRYPOINT: ddo-pulse-api               │  │
│  └─────────────────────────────────────────┘  │
└───────────────────────────────────────────────┘
```

关键事实：
- 采用两阶段构建：Stage 1 构建前端，Stage 2 安装后端并合并前端产物
- 运行时仅需 python:3.11-slim 基础镜像，不包含 Node.js
- 后端 API 的 `_mount_frontend()` 会自动检测 `services/web/frontend/dist/` 目录并挂载静态文件
- 默认端口 8765，通过 EXPOSE 声明后 Docker Desktop 会自动提示端口映射

---

## 3. 目录与命名（最终定版）

```
scripts/
└── Dockerfile          # 唯一新增文件
```

Dockerfile 构建上下文为项目根目录（`docker build -f scripts/Dockerfile .`），Docker Desktop 默认以 Dockerfile 所在目录的父目录为上下文。为兼容 Docker Desktop 的 Build 功能，Dockerfile 中使用相对路径引用项目文件。

---

## 4. 核心 Schema

不适用——本次变更为 Dockerfile 文件，无数据 Schema。

---

## 5. 关键算法 / 流程

### 5.1 多阶段构建流程

**Stage 1 — frontend-builder**：
1. 基础镜像：`node:20-alpine`
2. 工作目录：`/app`
3. 拷贝 `services/web/frontend/` 到工作目录
4. 执行 `npm ci && npm run build`，产物输出到 `/app/dist`

**Stage 2 — runtime**：
1. 基础镜像：`python:3.11-slim`
2. 工作目录：`/app`
3. 拷贝整个项目到 `/app`
4. 拷贝 Stage 1 的 `/app/dist` 到 `/app/services/web/frontend/dist/`
5. 执行 `pip install --no-cache-dir .` 安装后端依赖
6. 声明 `VOLUME /root/.ddo_pulse` 用于数据持久化
7. 声明 `EXPOSE 8765`
8. `ENTRYPOINT ["ddo-pulse-api"]` 直接启动 API 服务

### 5.2 Docker Desktop 交互流程

1. 用户在 Docker Desktop 中选择「Build Image」→ 选择 `scripts/Dockerfile` → 构建上下文设为项目根目录
2. 构建完成后，在 Images 列表中找到镜像 → 点击「Run」
3. 在 Run 对话框中配置：
   - Optional Settings → Ports: `8765:8765`
   - Optional Settings → Volumes: 宿主机路径 → `/root/.ddo_pulse`
4. 容器启动后，浏览器访问 `http://localhost:8765`

---

## 6. 错误处理与回退

| 触发条件 | 行为 |
|---|---|
| 前端构建失败 | Stage 1 报错，构建终止。用户需检查前端代码 |
| pip install 失败 | Stage 2 报错，构建终止。检查 pyproject.toml 依赖 |
| 容器启动后端口冲突 | Docker Desktop 提示端口占用，用户更换映射端口 |
| 数据目录未挂载 | 容器内自动创建 `/root/.ddo_pulse/`，数据存在容器内，容器删除后丢失 |

---

## 7. 风险与权衡

| # | 风险 | 描述 | 处置 |
|---|------|------|------|
| R-1 | Docker Desktop Build 上下文 | Docker Desktop 默认以 Dockerfile 所在目录为上下文，而 Dockerfile 在 scripts/ 子目录中 | Dockerfile 中使用相对路径 `COPY . /app`，构建时需指定上下文为项目根目录；或在 scripts/ 中放一个说明 |
| R-2 | 数据持久化 | 用户可能忘记挂载 volume，数据随容器删除丢失 | 在 Dockerfile 中用 VOLUME 声明，Docker Desktop 会提示；容器内数据仍可用，只是不持久 |
| R-3 | 镜像体积 | Python 依赖 + 系统库可能使镜像较大 | 使用 python:3.11-slim 而非 full；pip 使用 --no-cache-dir |
| R-4 | 首次启动初始化 | 用户首次运行需要 `ddo-pulse init` 创建数据目录 | 容器启动时自动检测并执行 init（在 ENTRYPOINT 中处理） |

---

## 8. 实施次序（高层路线，供 Tasking 拆分参考）

1. 创建 `scripts/Dockerfile`，包含两阶段构建逻辑
2. 编写 ENTRYPOINT 脚本或调整启动逻辑，确保首次运行自动 init
3. 验证：`docker build -f scripts/Dockerfile .` 构建成功
4. 验证：`docker run -p 8765:8765 <image>` 启动后可访问

---

## 9. 与 spec 的开放问题对应表

| spec Open Question | plan 中的落地 |
|---|---|
| Q-1 基础镜像选择什么？ | python:3.11-slim（后端）+ node:20-alpine（前端构建） |
| Q-2 前端构建产物如何集成？ | 多阶段构建，Stage 1 构建前端，Stage 2 COPY dist 到 `services/web/frontend/dist/`，后端自动检测并挂载 |
| Q-3 是否需要多阶段构建？ | 是。前端需要 Node.js 构建，运行时只需 Python，多阶段可显著减小镜像体积 |
| Q-4 容器运行时以什么用户身份运行？ | 默认 root（简化权限管理）；数据目录为 `/root/.ddo_pulse/` |

---

## 10. 用户确认

请确认以下任一选项：

- ✅ **同意**：本 plan 符合预期，可进入 **Test-Planning** 阶段生成 `test-plan.md`。
- ❌ **修改**：请在下方/对话中列出需要调整的章节与意见，AI 将基于反馈重新生成本文档。
