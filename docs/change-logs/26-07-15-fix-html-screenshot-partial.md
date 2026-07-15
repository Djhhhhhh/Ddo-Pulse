# 变更日志

**提交信息**: fix(screenshot): 修复 HTML 截图截断问题，新增公众号封面图生成
**分支**: fix/2026-07-15-fix-html-screenshot-partial
**日期**: 2026-07-15
**作者**: Djhhh

## 变更文件
- services/backend/tools/publishers/screenshot.py (modified)
- services/backend/agents/reporter.py (modified)
- services/backend/tools/publishers/__init__.py (modified)
- docs/fix/ (added)

## 统计
- 新增文件: 15
- 修改文件: 3
- 删除文件: 0
- 代码行数: +822 / -3

## 描述
修复 HTML 报告截图只能捕获部分内容的 bug，使用 Playwright 的 full_page=True 参数确保截图完整。新增公众号封面图生成功能，支持头条封面（900×383）和次条封面（200×200）两种尺寸。
