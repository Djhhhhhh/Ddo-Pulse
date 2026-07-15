# 任务分组

> 基于 plan.md 与 test-plan.md 拆分的任务清单、依赖关系与并行批次。

## 任务列表

| ID | 标题 | 文件 | 依赖 |
|---|---|---|---|
| task-01 | 修改 screenshot.py 实现完整截图 | task-01.md | — |
| task-02 | 修改 reporter.py 调用封面图生成 | task-02.md | task-01 |
| task-03 | 测试验证 | task-03.md | task-01, task-02 |

## 并行批次

### 批次 1

- task-01

### 批次 2

- task-02

### 批次 3

- task-03
