# Ddo-Pulse Dockerfile Specification

> AI 基于用户原始需求与 context-summary.md 对需求的规约化理解。
> 仅描述 What / Why 与验收标准；技术方案见 plan.md。

---

## 1. 项目概述

### 1.1 项目名称
Ddo-Pulse Dockerfile

### 1.2 一句话定义
在 scripts/ 目录下创建一个单一 Dockerfile，使项目可通过一条命令完成容器化部署。

### 1.3 设计意图
- 降低部署门槛：用户无需手动安装 Python、Node.js 等运行时依赖
- 统一环境：容器化消除了"在我机器上能跑"的问题
- 一键启动：单文件即可构建并运行完整应用（后端 API + 前端静态资源）
- Docker Desktop 友好：支持通过 Docker Desktop 图形界面完成构建和运行，无需 CLI 操作

---

## 2. 术语表（Glossary）

| 术语 | 定义 |
|---|---|
| 容器化部署 | 将应用及其所有依赖打包为一个可移植的容器镜像，通过容器引擎运行 |
| 一键部署 | 用户执行单条命令即可完成构建并启动应用 |

---

## 3. 功能需求（Functional Requirements）

### 3.1 Dockerfile 文件

- **FR-DF-1**：在 scripts/ 目录下创建一个名为 `Dockerfile` 的文件
- **FR-DF-2**：该 Dockerfile 必须是自包含的——构建和运行不依赖项目外部的额外文件或配置

### 3.2 构建过程

- **FR-BUILD-1**：Dockerfile 构建过程应安装项目所需的全部后端依赖
- **FR-BUILD-2**：Dockerfile 构建过程应安装前端依赖并构建前端静态资源
- **FR-BUILD-3**：构建产物应包含可运行的完整应用

### 3.3 运行时

- **FR-RUN-1**：容器启动后应同时提供后端 API 服务和前端静态资源托管
- **FR-RUN-2**：容器应暴露一个可通过浏览器访问的 Web 入口
- **FR-RUN-3**：应用数据目录应可通过 Docker volume 挂载以实现数据持久化
- **FR-RUN-4**：容器应声明 EXPOSE 端口，使 Docker Desktop 能自动显示端口映射

### 3.4 Docker Desktop 兼容性

- **FR-DC-1**：Dockerfile 应支持通过 Docker Desktop 的「Build Image」功能直接构建
- **FR-DC-2**：构建完成后，镜像应可通过 Docker Desktop 的「Run」按钮直接启动
- **FR-DC-3**：容器启动后无需额外手动配置即可正常访问应用

---

## 7. 验收标准（Acceptance Criteria）

- **AC-1**：scripts/Dockerfile 文件存在且语法正确
- **AC-2**：使用该 Dockerfile 可成功构建容器镜像（`docker build` 不报错）
- **AC-3**：使用构建的镜像运行容器后，可通过浏览器访问 Web UI
- **AC-4**：容器内后端 API 正常响应
- **AC-5**：数据目录可通过 `-v` 参数挂载到宿主机
- **AC-6**：Dockerfile 可通过 Docker Desktop 图形界面直接构建
- **AC-7**：构建后的镜像可通过 Docker Desktop 的「Run」按钮启动并正常访问

---

## 8. 范围说明（In / Out of Scope）

### In Scope
- 创建 scripts/Dockerfile
- 编写必要的辅助文件（如 .dockerignore，如果需要）

### Out of Scope
- CI/CD 流水线配置
- 多容器编排（docker-compose）
- 生产环境部署指南文档
- 数据库迁移脚本

---

## 10. 开放问题（Open Questions，待 Plan 阶段决策）

- **Q-1**：基础镜像选择什么？——留给 plan.md 决策。
- **Q-2**：前端构建产物如何集成到后端服务中？——留给 plan.md 决策。
- **Q-3**：是否需要多阶段构建来减小镜像体积？——留给 plan.md 决策。
- **Q-4**：容器运行时以什么用户身份运行？——留给 plan.md 决策。

---

## 11. 用户确认

请确认以下任一选项：

- ✅ **同意**：本 spec 符合预期，可进入 **Planning** 阶段生成 `plan.md`。
- ❌ **修改**：请在下方/对话中列出需要调整的条款编号与意见，AI 将基于反馈重新生成本文档。
