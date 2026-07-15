"""报告 API 路由。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _get_reports_dir() -> Path:
    """获取报告根目录"""
    return Path.home() / ".ddo_pulse" / "reports"


@router.get("/")
async def list_reports() -> Dict[str, List[Dict[str, Any]]]:
    """获取报告列表"""
    reports_dir = _get_reports_dir()
    if not reports_dir.exists():
        return {"reports": []}

    reports = []
    for d in sorted(reports_dir.iterdir(), reverse=True):
        if d.is_dir():
            md_file = d / "digest.md"

            reports.append({
                "timestamp": d.name,
                "has_md": md_file.exists(),
            })

    return {"reports": reports}


@router.get("/{timestamp}")
async def get_report(timestamp: str) -> Dict[str, Any]:
    """获取报告详情"""
    report_dir = _get_reports_dir() / timestamp
    if not report_dir.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    md_file = report_dir / "digest.md"

    return {
        "timestamp": timestamp,
        "md_content": md_file.read_text(encoding="utf-8") if md_file.exists() else None,
    }


@router.get("/{timestamp}/md")
async def get_report_md(timestamp: str) -> Dict[str, str]:
    """获取 MD 内容"""
    report_dir = _get_reports_dir() / timestamp
    md_file = report_dir / "digest.md"

    if not md_file.exists():
        raise HTTPException(status_code=404, detail="MD report not found")

    return {"content": md_file.read_text(encoding="utf-8")}
