# Task 08: 创建 Reporter Agent

## 关联验收点
- G2: 深度解读功能
- G4: 本地 MD 报告
- G5: HTML PPT 式报告

## 任务描述
创建 Reporter Agent，负责报告生成。

## 具体步骤

1. 创建 `agents/reporter.py`：
   - 继承 `Agent` 基类
   - 实现深度解读调用
   - 实现报告生成调度

2. 注册工具：
   - `deep_analysis` - 深度解读
   - `generate_md` - MD 报告生成
   - `generate_html` - HTML 报告生成
   - `generate_screenshots` - 截图生成

## 输出文件
- `services/backend/agents/reporter.py`

## Agent 设计
```python
from ddo_pulse_agents.base import Agent

class ReporterAgent(Agent):
    """报告生成 Agent"""
    
    def __init__(self, profile: dict):
        super().__init__("reporter", {"profile": profile})
    
    def run(self, context: dict) -> dict:
        """生成报告"""
        articles = context.get("articles", [])
        timestamp = context.get("timestamp")
        
        # 1. 深度解读
        analyzed = self._deep_analyze(articles)
        
        # 2. 生成报告
        md_path = self._generate_md(analyzed, timestamp)
        html_path = self._generate_html(analyzed, timestamp)
        
        # 3. 截图
        screenshots = self._generate_screenshots(html_path, timestamp)
        
        return {
            "md_path": md_path,
            "html_path": html_path,
            "screenshots": screenshots
        }
```

## 验证命令
```bash
python -c "from ddo_pulse_agents.reporter import ReporterAgent; print('OK')"
```
