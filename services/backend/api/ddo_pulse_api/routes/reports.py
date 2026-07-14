"""报告 API 路由。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

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
            html_file = d / "digest.html"
            images_dir = d / "images"

            reports.append({
                "timestamp": d.name,
                "has_md": md_file.exists(),
                "has_html": html_file.exists(),
                "image_count": len(list(images_dir.glob("*.png"))) if images_dir.exists() else 0,
            })

    return {"reports": reports}


@router.get("/{timestamp}")
async def get_report(timestamp: str) -> Dict[str, Any]:
    """获取报告详情"""
    report_dir = _get_reports_dir() / timestamp
    if not report_dir.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    md_file = report_dir / "digest.md"
    html_file = report_dir / "digest.html"
    images_dir = report_dir / "images"

    return {
        "timestamp": timestamp,
        "md_content": md_file.read_text(encoding="utf-8") if md_file.exists() else None,
        "html_content": html_file.read_text(encoding="utf-8") if html_file.exists() else None,
        "images": [f.name for f in images_dir.glob("*.png")] if images_dir.exists() else [],
    }


@router.get("/{timestamp}/html")
async def get_report_html(timestamp: str) -> HTMLResponse:
    """获取 HTML 内容（用于 iframe 预览）"""
    report_dir = _get_reports_dir() / timestamp
    html_file = report_dir / "digest.html"

    if not html_file.exists():
        raise HTTPException(status_code=404, detail="HTML report not found")

    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))


@router.get("/{timestamp}/md")
async def get_report_md(timestamp: str) -> Dict[str, str]:
    """获取 MD 内容"""
    report_dir = _get_reports_dir() / timestamp
    md_file = report_dir / "digest.md"

    if not md_file.exists():
        raise HTTPException(status_code=404, detail="MD report not found")

    return {"content": md_file.read_text(encoding="utf-8")}


@router.get("/{timestamp}/images/{filename}")
async def get_report_image(timestamp: str, filename: str):
    """获取报告图片"""
    from fastapi.responses import FileResponse

    image_path = _get_reports_dir() / timestamp / "images" / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(image_path, media_type="image/png")
