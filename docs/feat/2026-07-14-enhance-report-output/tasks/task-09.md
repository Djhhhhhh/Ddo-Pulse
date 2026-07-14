# Task 09: 报告目录结构

## 关联验收点
- G3: 报告目录结构

## 任务描述
实现按时间戳创建报告目录的功能。

## 具体步骤

1. 创建 `tools/publishers/report_dir.py`：
   - `generate_timestamp()` - 生成时间戳字符串
   - `create_report_dir()` - 创建报告目录
   - `get_report_base_dir()` - 获取报告根目录

2. 目录结构：
   ```
   ~/.ddo_pulse/reports/
   └── <yyyy-mm-dd-HHmmss>/
       ├── digest.md
       ├── digest.html
       └── images/
   ```

## 输出文件
- `services/backend/tools/publishers/report_dir.py`

## 代码设计
```python
from datetime import datetime
from pathlib import Path
import os

def generate_timestamp() -> str:
    """生成时间戳目录名"""
    return datetime.now().strftime("%Y-%m-%d-%H%M%S")

def get_report_base_dir() -> Path:
    """获取报告根目录"""
    return Path.home() / ".ddo_pulse" / "reports"

def create_report_dir(timestamp: str = None) -> Path:
    """创建报告目录"""
    if timestamp is None:
        timestamp = generate_timestamp()
    report_dir = get_report_base_dir() / timestamp
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "images").mkdir(exist_ok=True)
    return report_dir
```

## 验证命令
```bash
python -c "
from ddo_pulse_tools.publishers.report_dir import generate_timestamp, create_report_dir
ts = generate_timestamp()
assert len(ts) == 15
print(f'OK: {ts}')
"
```
