# Task 04: 集成封面图拼合到 ReporterAgent

## 目标

修改 `services/backend/agents/reporter.py`，在报告生成流程中集成封面图拼合。

## 关联验收点

- G1 cmd2: 拼合后尺寸正确 (1283×383)
- G1 human: 微信公众号上传验证

## 实现要求

1. 在 `ReporterAgent` 中新增 `_generate_cover()` 方法
2. 调用 `tools.publishers.cover_merger.merge_cover_images()`
3. 在 `run()` 方法中，生成 MD/HTML 之后调用 `_generate_cover()`
4. 返回值中新增 `cover_path` 字段
5. 封面图保存到 report_dir/cover.png
6. 封面图生成失败时不阻断主流程（记录 warning）

## 依赖

- task-01（需要 cover_merger.py）

## 文件清单

- 修改：`services/backend/agents/reporter.py`
