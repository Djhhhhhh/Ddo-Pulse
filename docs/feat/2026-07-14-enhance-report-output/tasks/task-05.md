# Task 05: 创建 Curator Agent

## 关联验收点
- G1: 项目结构 Agent 化

## 任务描述
将现有的分析逻辑封装为 Curator Agent。

## 具体步骤

1. 创建 `agents/curator.py`：
   - 继承 `Agent` 基类
   - 封装 `analyze_pending_chunk()` 逻辑
   - 注册 LLM 分析工具
   - 支持批量处理

2. 更新 `pipeline.py` 使用 Curator Agent

## 输出文件
- `services/backend/agents/curator.py`

## Agent 设计
```python
from ddo_pulse_agents.base import Agent

class CuratorAgent(Agent):
    """内容策展 Agent"""
    
    def __init__(self, profile: dict):
        super().__init__("curator", {"profile": profile})
        self.analyzer = OpenRouterAnalyzer(profile)
    
    def run(self, context: dict) -> dict:
        """分析文章"""
        rows = context.get("rows", [])
        results = []
        for row in rows:
            result = self.analyzer.analyze(row["title"], row["content"])
            results.append(result)
        return {"results": results}
```

## 验证命令
```bash
python -c "from ddo_pulse_agents.curator import CuratorAgent; print('OK')"
```
