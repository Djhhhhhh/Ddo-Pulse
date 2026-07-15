# Task 02: 修改 reporter.py 调用封面图生成

## 任务描述

修改 `services/backend/agents/reporter.py` 文件，在报告生成流程中调用 `generate_covers()` 函数生成封面图。

## 关联验收点

- G2: 头条封面图
- G3: 次条封面图

## 具体修改

### 1. 导入 generate_covers

```python
from services.backend.tools.publishers.screenshot import generate_screenshots, generate_covers
```

### 2. 在 run() 方法中调用封面图生成

在生成幻灯片截图之前或之后，调用 `generate_covers()` 生成封面图。

### 3. 将封面图路径加入返回结果

```python
result["cover_main"] = covers.get("main")
result["cover_sub"] = covers.get("sub")
```

## 输出产物

- 修改后的 `reporter.py` 文件
- 返回结果中包含封面图路径

## 依赖

- task-01
