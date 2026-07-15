# 上下文摘要

> 自动生成自项目上下文扫描。

## 已加载来源

| 文件路径 | 摘要 |
|---|---|
| services/backend/AGENTS.md | 后端架构规范：Python 代码集中在 backend 目录，cli/core/api/db/mcp 五层结构，禁止 core 依赖 FastAPI/Vue |
| services/web/AGENTS.md | Web 端规范：Vue 3 + Vite 单页应用，仅前端 UI，不直连 SQLite |
| README.md | 项目介绍：Ddo-Pulse 是本机信息聚合工具，支持 RSS/HTML 抓取、LLM 分析、飞书推送、本地 Web Dashboard |
| pyproject.toml | 项目配置：Python 3.11+，依赖 typer/httpx/feedparser/openai/fastapi/apscheduler 等 |
| services/backend/prompts/reporter.py | 报告提示词模板：DEEP_ANALYSIS_PROMPT 用于深度解读，输出 core_content/key_points/insights |
| services/backend/agents/reporter.py | 报告生成 Agent：调用 LLM 深度解读 → 生成 MD/HTML/截图三份产物 |
| services/backend/tools/publishers/markdown.py | MD 报告生成器：generate_digest_md() 逐篇文章拼接标题/摘要/要点/启发 |
| services/backend/tools/publishers/html_report.py | HTML 报告生成器：PPT 幻灯片式布局，含 CSS 样式和键盘导航 |
| services/backend/tools/publishers/screenshot.py | 截图工具：基于 Playwright 对 HTML 报告逐页截图 |
| services/backend/core/ddo_pulse_core/pipeline.py | 核心流水线：fetch → analyze → digest → push，含 _generate_local_reports() |

## 上下文缺失

- 项目根目录无 AGENTS.md（仅子目录有）
