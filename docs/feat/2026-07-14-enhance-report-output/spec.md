# Ddo-Pulse 报告增强 Specification

> AI 基于用户原始需求与 context-summary.md 对需求的规约化理解。
> 仅描述 What / Why 与验收标准；技术方案见 plan.md。

---

## 1. 项目概述

### 1.1 项目名称
Ddo-Pulse 报告增强

### 1.2 一句话定义
增强报告输出功能：添加文章深度解读、本地 MD 报告（公众号用）、HTML PPT 式报告及自动截图。

### 1.3 设计意图
- 提供更深入的文章内容分析，帮助用户快速理解核心思路
- 支持本地生成公众号友好的 MD 格式报告
- 生成类似 PPT 的 HTML 报告，每页一篇文章解读
- 自动将 HTML 报告转为图片，方便公众号配图使用

---

## 2. 术语表（Glossary）

| 术语 | 定义 |
|---|---|
| 深度解读 | 对文章全文进行分析，提取核心内容、思路和关键观点 |
| Digest | 每日精选报告，包含筛选后的高质量文章 |
| 飞书富文本 | 飞书 Webhook 支持的 post 消息格式 |
| HTML PPT 式报告 | 类似幻灯片展示的 HTML 页面，每页一篇文章解读 |

---

## 3. 功能需求（Functional Requirements）

### 3.1 文章深度解读

- **FR-ANALYSIS-1**：在现有文章分析（标题、摘要、分类、评分）基础上，新增深度解读字段
- **FR-ANALYSIS-2**：深度解读应包含：核心内容总结、文章思路梳理、关键观点提取
- **FR-ANALYSIS-3**：深度解读结果存储在数据库中，供报告生成使用

### 3.2 本地 MD 报告

- **FR-MD-1**：生成本地 Markdown 格式的每日报告文件
- **FR-MD-2**：报告按时间戳目录隔离，格式为 `yyyy-mm-dd-HHmmss`
- **FR-MD-3**：报告存储在用户数据目录 `~/.ddo_pulse/reports/<timestamp>/` 下
- **FR-MD-4**：MD 格式需适配微信公众号排版要求（标题层级、段落间距等）

### 3.3 HTML PPT 式报告

- **FR-HTML-1**：生成类似 PPT 展示的 HTML 报告
- **FR-HTML-2**：每页展示一篇文章的深度解读
- **FR-HTML-3**：HTML 支持幻灯片式浏览（翻页交互）
- **FR-HTML-4**：报告样式美观，适合截图分享

### 3.4 自动截图

- **FR-IMG-1**：HTML 报告生成后，自动将每页转换为图片
- **FR-IMG-2**：图片存储在 `~/.ddo_pulse/reports/<timestamp>/images/` 目录下
- **FR-IMG-3**：图片文件名包含序号，如 `page-01.png`
- **FR-IMG-4**：图片分辨率适合公众号使用

### 3.5 Docker 环境报告访问

- **FR-DOCKER-1**：通过 docker-compose 数据卷挂载 `~/.ddo_pulse/reports/` 到宿主机

---

## 4. 产物与目录结构（What gets created）

```
~/.ddo_pulse/
└── reports/
    ├── 2026-07-14-083000/                     # 时间戳目录（yyyy-mm-dd-HHmmss）
    │   ├── digest.md                          # 本地 MD 报告
    │   ├── digest.html                        # HTML PPT 式报告
    │   └── images/
    │       ├── page-01.png                    # 文章1解读图片
    │       ├── page-02.png                    # 文章2解读图片
    │       └── ...
    ├── 2026-07-14-143000/                     # 同一天多次运行
    │   └── ...
    └── ...
```

---

## 5. 关键流程

```
1. 获取待分析文章
   ↓
2. LLM 深度解读（核心内容 + 思路 + 观点）
   ↓
3. 存储解读结果到数据库
   ↓
4. 生成报告：
   ├── 飞书富文本（现有）
   ├── 本地 MD 文件（新增）
   └── HTML PPT 式报告（新增）
       ↓
   5. 自动截图生成图片（新增）
```

---

## 6. 约束与原则

- **C-1**：深度解读不应替换现有的摘要和分类，而是补充
- **C-2**：本地 MD 报告需保持与飞书推送内容的一致性
- **C-3**：HTML 报告应使用纯前端技术，无需后端服务
- **C-4**：截图功能应使用浏览器自动化工具（如 Playwright）

---

## 7. 验收标准（Acceptance Criteria）

- **AC-1**：文章分析结果包含深度解读字段（核心内容、思路、观点）
- **AC-2**：运行 pipeline 后，`~/.ddo_pulse/reports/<yyyy-mm-dd-HHmmss>/` 目录下生成 MD 文件
- **AC-3**：运行 pipeline 后，`~/.ddo_pulse/reports/<yyyy-mm-dd-HHmmss>/` 目录下生成 HTML 文件
- **AC-4**：HTML 文件可在浏览器中打开，支持翻页浏览
- **AC-5**：`~/.ddo_pulse/reports/<yyyy-mm-dd-HHmmss>/images/` 目录下生成对应文章的 PNG 图片
- **AC-6**：飞书推送功能正常工作（不受影响）
- **AC-7**：Docker 环境下可通过选定方案访问报告文件

---

## 8. 非功能需求（Non-Functional）

- **NFR-1**：深度解读不应显著增加 LLM API 调用时间（<2x 现有耗时）
- **NFR-2**：HTML 报告页面加载流畅，无明显卡顿
- **NFR-3**：截图生成时间 < 30秒/页

---

## 9. 范围说明（In / Out of Scope）

### In Scope
- 文章深度解读功能
- 本地 MD 报告生成（按时间戳目录隔离）
- HTML PPT 式报告生成
- 自动截图功能
- Docker 环境报告访问方案

### Out of Scope
- 图片上传到云存储
- 微信公众号自动发布
- 报告模板自定义 UI

---

## 10. 开放问题（Open Questions，待 Plan 阶段决策）

- **Q-1**：深度解读的 LLM 提示词如何设计？需要哪些字段？
- **Q-2**：HTML 报告使用什么前端框架或库？纯 HTML/CSS/JS 还是 Vue？
- **Q-3**：截图使用 Playwright 还是 Puppeteer？
- **Q-4**：MD 报告的格式是否需要支持微信公众号的特殊语法（如脚注）？
- **Q-5**：Docker 环境下报告访问方式选择（请选择一项）：
  - **方案A：数据卷挂载** - 在 docker-compose.yml 中挂载 `~/.ddo_pulse/reports/` 到宿主机，用户直接访问宿主机目录
  - **方案B：Web API 下载** - 新增 API 端点 `/api/reports/{timestamp}/download/{filename}`，通过浏览器下载
  - **方案C：Web UI 查看** - 在现有 Vue 前端中添加报告列表和预览页面

---

## 11. 用户确认

请确认以下任一选项：

- ✅ **同意**：本 spec 符合预期，可进入 **Planning** 阶段生成 `plan.md`。
- ❌ **修改**：请在下方/对话中列出需要调整的条款编号与意见，AI 将基于反馈重新生成本文档。
