"""Agent 基类定义。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict


class Agent(ABC):
    """Agent 基类"""

    def __init__(self, name: str, config: Dict[str, Any] | None = None):
        self.name = name
        self.config = config or {}
        self._tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, tool_func: Callable) -> None:
        """注册工具"""
        self._tools[name] = tool_func

    def get_tool(self, name: str) -> Callable | None:
        """获取工具"""
        return self._tools.get(name)

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Agent 任务"""
        pass
