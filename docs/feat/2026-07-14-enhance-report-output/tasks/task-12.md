# Task 12: 截图功能

## 关联验收点
- G6: 自动截图功能

## 任务描述
实现 HTML 报告自动截图功能。

## 具体步骤

1. 创建 `tools/publishers/screenshot.py`：
   - `generate_screenshots()` - 生成截图
   - 使用 Playwright 打开 HTML
   - 逐页截图保存为 PNG

2. 截图参数：
   - 宽度：1080px（公众号推荐）
   - 格式：PNG
   - 命名：page-01.png, page-02.png, ...

## 输出文件
- `services/backend/tools/publishers/screenshot.py`

## 代码设计
```python
from pathlib import Path
from typing import List

def generate_screenshots(
    html_path: Path,
    output_dir: Path,
    width: int = 1080
) -> List[Path]:
    """生成 HTML 报告截图"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed, skipping screenshots")
        return []
    
    screenshots = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 800})
        page.goto(f"file://{html_path}")
        
        # 获取幻灯片数量
        slide_count = page.eval_on_selector_all(".slide", "els => els.length")
        
        for i in range(slide_count):
            # 显示当前幻灯片
            page.evaluate(f"show({i})")
            page.wait_for_timeout(500)
            
            # 截图
            screenshot_path = output_dir / f"page-{i+1:02d}.png"
            page.screenshot(path=str(screenshot_path))
            screenshots.append(screenshot_path)
        
        browser.close()
    
    return screenshots
```

## 验证命令
```bash
python -c "import playwright; print('Playwright installed')" 2>/dev/null || echo "Playwright not installed (skip)"
ls ~/.ddo_pulse/reports/*/images/*.png 2>/dev/null | head -1 || echo "No screenshots yet"
```
