# Ddo-Pulse 报告增强 Plan

> 基于已确认的 spec.md 做技术决策。

---

## 1. 决策原则

| # | 原则 | 落地体现 |
|---|------|----------|
| P-1 | Agent 优先 | 重构为 Agent 项目标准结构，职责清晰 |
| P-2 | 前后端解耦 | HTML 报告为静态文件，不依赖后端服务 |
| P-3 | 向后兼容 | 深度解读为可选字段，不影响现有流程 |
| P-4 | Docker 友好 | 报告输出到数据卷挂载路径 |

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Pipeline 流程                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Fetch   │───▶│ Analyze  │───▶│  Digest  │───▶│  Output  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                       │                │               │        │
│                       ▼                ▼               ▼        │
│                  深度解读字段      飞书 + MD + HTML    截图生成    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

输出产物：
~/.ddo_pulse/reports/<timestamp>/
├── digest.md          # 公众号用 MD
├── digest.html        # PPT 式 HTML
└── images/            # 截图
    ├── page-01.png
    └── page-02.png
```

关键事实：
- 复用现有 `analyzed_items` 表，添加 `deep_analysis_json` 字段
- HTML 报告使用纯 HTML/CSS/JS，无需框架
- 截图使用 Playwright（项目已有可选依赖）

---

## 3. 目录与命名（最终定版）

### 3.1 Agent 项目标准结构

```
services/backend/
├── agents/                          # Agent 定义与配置
│   ├── __init__.py
│   ├── base.py                      # Agent 基类
│   ├── curator.py                   # 内容策展 Agent（原 analyzer）
│   └── reporter.py                  # 报告生成 Agent（新增）
├── tools/                           # Agent 可用工具
│   ├── __init__.py
│   ├── fetchers/                    # 数据抓取工具
│   │   ├── __init__.py
│   │   ├── rss.py
│   │   ├── html_list.py
│   │   └── browser_session.py
│   ├── analyzers/                   # 分析工具
│   │   ├── __init__.py
│   │   └── llm_analyzer.py
│   └── publishers/                  # 发布工具
│       ├── __init__.py
│       ├── feishu.py
│       ├── markdown.py              # MD 报告生成
│       ├── html_report.py           # HTML 报告生成
│       └── screenshot.py            # 截图工具
├── prompts/                         # 提示词模板
│   ├── __init__.py
│   ├── curator.py                   # 策展提示词
│   └── reporter.py                  # 报告提示词（含深度解读）
├── workflows/                       # 工作流定义
│   ├── __init__.py
│   └── daily_digest.py              # 每日精选工作流
├── core/                            # 核心业务逻辑（保留）
│   └── ddo_pulse_core/
│       ├── models.py
│       ├── config_yaml.py
│       └── web_config.py
├── db/                              # 数据库（保留）
├── api/                             # REST API（扩展）
│   └── ddo_pulse_api/
│       ├── routes/
│       │   └── reports.py           # 新增：报告 API
│       └── ...
├── cli/                             # CLI（保留）
└── mcp/                             # MCP Server（保留）

services/web/frontend/
├── src/
│   ├── views/
│   │   └── Reports.vue              # 新增：报告预览页面
│   ├── components/
│   │   └── ReportViewer.vue         # 新增：报告查看组件
│   └── ...
└── ...
```

### 3.2 报告输出结构

```
~/.ddo_pulse/
└── reports/
    └── <yyyy-mm-dd-HHmmss>/
        ├── digest.md
        ├── digest.html
        └── images/
            └── page-XX.png
```

---

## 4. 核心 Schema

### 4.1 analyzed_items 表扩展

```sql
ALTER TABLE analyzed_items ADD COLUMN deep_analysis_json TEXT;
```

字段语义约束：
- `deep_analysis_json`：JSON 字符串，包含深度解读结果
- 格式：`{"core_content": "...", "key_points": [...], "insights": "..."}`

### 4.2 深度解读 JSON Schema

```jsonc
{
  "core_content": "文章核心内容的 200-300 字总结",
  "key_points": [
    "关键观点1",
    "关键观点2",
    "关键观点3"
  ],
  "insights": "文章的思路梳理和启发性内容"
}
```

---

## 5. 关键算法 / 流程

### 5.1 深度解读生成

1. 在现有 `analyzer.analyze()` 调用后，追加深度解读请求
2. 使用相同的 LLM 配置，发送深度解读 prompt
3. 解析返回的 JSON，存储到 `deep_analysis_json`

### 5.2 时间戳目录生成

```python
from datetime import datetime

def generate_report_dir() -> str:
    return datetime.now().strftime("%Y-%m-%d-%H%M%S")
```

### 5.3 HTML 报告生成

1. 获取当日精选文章列表
2. 遍历文章，每篇生成一个"幻灯片" div
3. 嵌入 CSS 实现翻页效果
4. 输出为单个 HTML 文件

### 5.4 前端报告预览

**API 端点：**
```
GET /api/reports                    # 获取报告列表
GET /api/reports/{timestamp}        # 获取单个报告详情
GET /api/reports/{timestamp}/html   # 获取 HTML 内容（用于 iframe 预览）
```

**前端路由：**
```
/reports              # 报告列表页
/reports/:timestamp   # 报告预览页
```

**ReportViewer 组件：**
- 使用 `<iframe>` 加载 HTML 报告
- 支持全屏预览
- 提供下载按钮（MD/HTML/PNG）

### 5.5 截图流程

1. 使用 Playwright 打开 HTML 文件
2. 设置 viewport 为公众号推荐宽度（1080px）
3. 遍历每页，滚动到对应位置
4. 截取每页区域，保存为 PNG

---

## 6. 错误处理与回退

| 触发条件 | 行为 |
|----------|------|
| 深度解读 API 调用失败 | 记录错误，使用空值继续，不影响主流程 |
| HTML 模板渲染失败 | 跳过 HTML 生成，仅生成 MD |
| Playwright 未安装 | 跳过截图，记录警告 |
| 目录创建失败 | 使用临时目录，记录错误 |

---

## 7. 风险与权衡

| # | 风险 | 描述 | 处置 |
|---|------|------|------|
| R-1 | LLM 成本增加 | 深度解读增加 API 调用 | 可配置开关，复用同一 LLM 调用 |
| R-2 | 截图依赖 | Playwright 是可选依赖 | 检测安装状态，未安装则跳过 |
| R-3 | 文件系统权限 | Docker 内写入可能失败 | 确保数据卷权限正确 |
| R-4 | 重构影响范围 | 项目结构调整可能影响现有功能 | 分阶段迁移，保持向后兼容 |
| R-5 | 测试覆盖 | 重构需要充分测试 | 先写测试再迁移 |

---

## 8. 实施次序（高层路线，供 Tasking 拆分参考）

### Phase 1: 项目结构重构（Agent 化）
1. **创建 Agent 基础结构**：`agents/`、`tools/`、`prompts/`、`workflows/` 目录
2. **迁移现有逻辑**：将 `analyzer/` 移入 `tools/analyzers/`，将 `notifier/` 移入 `tools/publishers/`
3. **提取提示词**：将 prompt 模板移入 `prompts/` 目录
4. **定义 Agent 基类**：创建 `agents/base.py`，定义通用接口
5. **创建 Curator Agent**：封装现有分析逻辑为 Agent

### Phase 2: 报告增强功能
6. **数据库迁移**：添加 `deep_analysis_json` 字段
7. **深度解读 Prompt**：在 `prompts/reporter.py` 中设计
8. **创建 Reporter Agent**：封装报告生成逻辑
9. **报告目录结构**：实现时间戳目录生成
10. **本地 MD 报告**：创建 `tools/publishers/markdown.py`
11. **HTML 报告生成**：创建 `tools/publishers/html_report.py`
12. **截图功能**：创建 `tools/publishers/screenshot.py`

### Phase 3: 前端报告预览
13. **报告 API**：创建 `/api/reports` 端点
14. **报告列表页**：创建 `Reports.vue`
15. **报告查看组件**：创建 `ReportViewer.vue`（iframe 预览）
16. **路由配置**：添加 `/reports` 路由

### Phase 4: 集成与配置
17. **定义工作流**：创建 `workflows/daily_digest.py`
18. **Docker 配置**：更新 docker-compose.yml

---

## 9. 与 spec 的开放问题对应表

| spec Open Question | plan 中的落地 |
|---|---|
| Q-1：深度解读 LLM 提示词设计 | 第 5.1 节：复用现有 LLM 配置，新增深度解读 prompt 字段 |
| Q-2：HTML 报告技术选型 | 第 5.3 节：纯 HTML/CSS/JS，无框架依赖 |
| Q-3：截图工具选择 | 第 5.5 节：Playwright（项目已有可选依赖） |
| Q-4：MD 报告格式 | 第 5.2 节：标准 Markdown，适配公众号 |
| Q-5：Docker 访问方案 | 已选定方案 A：数据卷挂载 |
| *新增*：项目结构 Agent 化 | 第 3.1 节：重构为 agents/tools/prompts/workflows 标准结构 |
| *新增*：前端报告预览 | 第 5.4 节：Vue 页面 + iframe 预览 + 报告 API |

---

## 10. 用户确认

请确认以下任一选项：

- ✅ **同意**：本 plan 符合预期，可进入 **Test-Planning** 阶段生成 `test-plan.md`。
- ❌ **修改**：请在下方/对话中列出需要调整的章节与意见，AI 将基于反馈重新生成本文档。
