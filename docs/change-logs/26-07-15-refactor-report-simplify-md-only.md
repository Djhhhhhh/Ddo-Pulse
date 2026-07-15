# 变更日志

**提交信息**: refactor(report): 简化报告生成流程，仅保留 MD 输出；优化深度解读文风；评分改为 Tags 格式
**分支**: feat/2026-07-15-wechat-cover-digest-style
**日期**: 2026-07-15
**作者**: Djhhh

## 变更文件
- docs/feat/2026-07-15-report-simplify-md-only/.state.json (added)
- docs/feat/2026-07-15-report-simplify-md-only/execution-report.md (added)
- services/backend/agents/reporter.py (modified)
- services/backend/api/ddo_pulse_api/routes/reports.py (modified)
- services/backend/core/ddo_pulse_core/pipeline.py (modified)
- services/backend/prompts/reporter.py (modified)
- services/backend/tools/publishers/__init__.py (modified)
- services/backend/tools/publishers/html_report.py (deleted)
- services/backend/tools/publishers/markdown.py (modified)
- services/backend/tools/publishers/report_dir.py (modified)
- services/backend/tools/publishers/screenshot.py (deleted)

## 统计
- 新增文件: 2
- 修改文件: 7
- 删除文件: 2
- 代码行数: +130 / -519

## 描述
1. 删除 HTML 报告、截图、封面图生成逻辑，仅保留 MD 输出
2. 优化深度解读 prompt，将「技术博主」改为「技术编辑」，禁止口语化表达
3. 将文章评分（📌 XX 分）改为 Tags 格式，新增「🎯 着重看」阅读重点段落
4. 精简 API 路由，移除 HTML 预览和图片端点
