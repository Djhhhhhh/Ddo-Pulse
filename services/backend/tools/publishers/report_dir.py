"""报告目录管理工具。"""

from datetime import datetime
from pathlib import Path


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
