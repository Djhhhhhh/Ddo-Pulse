# Task 04: 定义 Agent 基类

## 关联验收点
- G1: 项目结构 Agent 化

## 任务描述
创建 Agent 基类，定义通用接口和工具调用机制。

## 具体步骤

1. 创建 `agents/base.py`：
   - 定义 `Agent` 抽象基类
   - 实现 `run()` 方法接口
   - 实现工具注册机制
   - 实现上下文管理

2. 定义 Agent 配置 schema

## 输出文件
- `services/backend/agents/base.py`

## 基类设计
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class Agent(ABC):
    """Agent 基类"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self._tools = {}
    
    def register_tool(self, name: str, tool_func):
        """注册工具"""
        self._tools[name] = tool_func
    
    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Agent 任务"""
        pass
```

## 验证命令
```bash
python -c "from ddo_pulse_agents.base import Agent; print('OK')"
```
