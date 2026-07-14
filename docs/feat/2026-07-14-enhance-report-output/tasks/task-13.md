# Task 13: 报告 API

## 关联验收点
- G8: 前端报告预览

## 任务描述
创建报告相关的 API 端点。

## 具体步骤

1. 创建 `api/ddo_pulse_api/routes/reports.py`：
   - `GET /api/reports` - 获取报告列表
   - `GET /api/reports/{timestamp}` - 获取报告详情
   - `GET /api/reports/{timestamp}/html` - 获取 HTML 内容

2. 更新 `api/ddo_pulse_api/main.py`：
   - 注册 reports 路由

## 输出文件
- `services/backend/api/ddo_pulse_api/routes/reports.py`

## API 设计
```python
from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/")
async def list_reports():
    """获取报告列表"""
    reports_dir = Path.home() / ".ddo_pulse" / "reports"
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
                "image_count": len(list(images_dir.glob("*.png"))) if images_dir.exists() else 0
            })
    
    return {"reports": reports}

@router.get("/{timestamp}")
async def get_report(timestamp: str):
    """获取报告详情"""
    report_dir = Path.home() / ".ddo_pulse" / "reports" / timestamp
    if not report_dir.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    md_file = report_dir / "digest.md"
    html_file = report_dir / "digest.html"
    
    return {
        "timestamp": timestamp,
        "md_content": md_file.read_text(encoding="utf-8") if md_file.exists() else None,
        "html_content": html_file.read_text(encoding="utf-8") if html_file.exists() else None
    }

@router.get("/{timestamp}/html")
async def get_report_html(timestamp: str):
    """获取 HTML 内容（用于 iframe 预览）"""
    report_dir = Path.home() / ".ddo_pulse" / "reports" / timestamp
    html_file = report_dir / "digest.html"
    
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="HTML report not found")
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
```

## 验证命令
```bash
curl -s http://localhost:8765/api/reports 2>/dev/null | python -m json.tool || echo "API not running"
```
