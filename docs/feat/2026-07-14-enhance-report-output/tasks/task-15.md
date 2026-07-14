# Task 15: 定义工作流

## 关联验收点
- G7: 飞书推送（回归测试）

## 任务描述
创建每日精选工作流，整合所有功能。

## 具体步骤

1. 创建 `workflows/daily_digest.py`：
   - 定义 `DailyDigestWorkflow` 类
   - 整合 Curator Agent 和 Reporter Agent
   - 串联 fetch → analyze → digest → output 流程

2. 更新 `pipeline.py`：
   - 使用新的工作流

## 输出文件
- `services/backend/workflows/daily_digest.py`

## 工作流设计
```python
from typing import Dict, Any
from ddo_pulse_agents.curator import CuratorAgent
from ddo_pulse_agents.reporter import ReporterAgent
from ddo_pulse_tools.publishers.report_dir import create_report_dir
from ddo_pulse_tools.publishers.feishu import build_feishu_post_payload, send_feishu_webhook

class DailyDigestWorkflow:
    """每日精选工作流"""
    
    def __init__(self, db, profile: dict, job_config: dict):
        self.db = db
        self.profile = profile
        self.job_config = job_config
        self.curator = CuratorAgent(profile)
        self.reporter = ReporterAgent(profile)
    
    def run(self) -> Dict[str, Any]:
        """执行工作流"""
        stats = {"fetch": 0, "analyze": 0, "digest": 0, "output": 0}
        
        # 1. Fetch
        # ... fetch logic ...
        
        # 2. Analyze with Curator Agent
        articles = self.db.list_analyzed_items(limit=self.job_config["digest_top_n"])
        stats["analyze"] = len(articles)
        
        # 3. Generate output with Reporter Agent
        timestamp = create_report_dir().name
        result = self.reporter.run({
            "articles": articles,
            "timestamp": timestamp
        })
        
        # 4. Push to Feishu
        if self.job_config.get("push_digest"):
            webhook = self.job_config.get("feishu_webhook_url")
            if webhook:
                payload = build_feishu_post_payload(timestamp, articles)
                ok, _ = send_feishu_webhook(webhook, payload)
                stats["feishu_pushed"] = ok
        
        stats["output"] = 1
        return stats
```

## 验证命令
```bash
python -c "from ddo_pulse_workflows.daily_digest import DailyDigestWorkflow; print('OK')"
```
