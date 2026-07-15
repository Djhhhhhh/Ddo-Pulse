# Task 03: 优化 digest.md 排版模板

## 目标

修改 `services/backend/tools/publishers/markdown.py` 中的 `generate_digest_md()`，优化排版。

## 关联验收点

- G2 cmd1: 空文章生成正确
- G2 cmd2: 有文章生成正确，格式清晰

## 实现要求

1. 重新设计排版模板，使结构更清晰、层次更分明
2. 标题区：日期 + 统计信息
3. 每篇文章：标题 → 元信息（分数/分类） → 摘要 → 推荐理由 → 深度解读
4. 深度解读区：核心内容 → 要点列表 → 启发
5. 减少多余的空行和分隔线
6. 使用更自然的中文标点和排版

## 文件清单

- 修改：`services/backend/tools/publishers/markdown.py`
