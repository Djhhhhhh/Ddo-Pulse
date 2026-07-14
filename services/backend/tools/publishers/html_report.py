"""HTML PPT 式报告生成器。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List


def _parse_categories(raw: str | None) -> List[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x) for x in data]
    except json.JSONDecodeError:
        pass
    return []


def _generate_slide_html(idx: int, row: dict, deep_analysis: dict) -> str:
    """生成单个幻灯片 HTML"""
    title = row.get("title") or row.get("url", "")
    url = row.get("url", "")
    score = row.get("score", 0)
    categories = row.get("categories", [])
    if isinstance(categories, str):
        categories = _parse_categories(categories)
    cats = "、".join(categories) or "未分类"
    summary = (row.get("summary_zh") or "").strip()
    reason = (row.get("reason") or "").strip()

    core_content = deep_analysis.get("core_content", "")
    key_points = deep_analysis.get("key_points", [])
    insights = deep_analysis.get("insights", "")

    points_html = ""
    if key_points:
        points_html = '<div class="key-points"><h3>核心要点</h3><ul>'
        for point in key_points:
            points_html += f"<li>{point}</li>"
        points_html += "</ul></div>"

    insights_html = ""
    if insights:
        insights_html = f'<div class="insights"><h3>💡 思路启发</h3><p>{insights}</p></div>'

    return f"""
    <div class="slide" id="slide-{idx}">
        <div class="slide-header">
            <span class="slide-number">{idx}</span>
            <span class="score">{score} 分</span>
            <span class="categories">{cats}</span>
        </div>
        <h2 class="title"><a href="{url}" target="_blank">{title}</a></h2>
        <div class="summary">{summary}</div>
        <div class="reason"><em>{reason}</em></div>
        <div class="deep-analysis">
            <h3>📖 深度解读</h3>
            <p>{core_content}</p>
            {points_html}
            {insights_html}
        </div>
    </div>
    """


def generate_digest_html(
    date: str,
    articles: List[Any],
    output_path: Path
) -> Path:
    """生成 HTML PPT 式报告"""
    slides_html = ""

    if not articles:
        slides_html = '<div class="slide active"><p>今日暂无达到阈值的精选文章。</p></div>'
    else:
        for idx, row in enumerate(articles, 1):
            deep_analysis = row.get("deep_analysis", {})
            slides_html += _generate_slide_html(idx, row, deep_analysis)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ddo-Pulse 精选 · {date}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .slide {{
            display: none;
            min-height: 100vh;
            padding: 40px;
            background: white;
            flex-direction: column;
            justify-content: center;
        }}
        .slide.active {{
            display: flex;
        }}
        .slide-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
        }}
        .slide-number {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }}
        .score {{
            background: #f0f0f0;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            color: #667eea;
        }}
        .categories {{
            color: #666;
            font-size: 14px;
        }}
        .title {{
            font-size: 28px;
            margin-bottom: 20px;
            line-height: 1.4;
        }}
        .title a {{
            color: #333;
            text-decoration: none;
        }}
        .title a:hover {{
            color: #667eea;
        }}
        .summary {{
            font-size: 16px;
            line-height: 1.8;
            color: #444;
            margin-bottom: 15px;
        }}
        .reason {{
            color: #888;
            font-size: 14px;
            margin-bottom: 25px;
            padding-left: 15px;
            border-left: 3px solid #667eea;
        }}
        .deep-analysis {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin-top: 15px;
        }}
        .deep-analysis h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 18px;
        }}
        .deep-analysis p {{
            line-height: 1.8;
            color: #555;
            margin-bottom: 15px;
        }}
        .key-points ul {{
            list-style: none;
            padding: 0;
        }}
        .key-points li {{
            padding: 8px 0;
            padding-left: 25px;
            position: relative;
            color: #555;
        }}
        .key-points li:before {{
            content: "✓";
            position: absolute;
            left: 0;
            color: #667eea;
            font-weight: bold;
        }}
        .insights {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }}
        .insights h3 {{
            color: #856404;
            margin-bottom: 10px;
        }}
        .insights p {{
            color: #856404;
            margin: 0;
        }}
        .nav {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            display: flex;
            gap: 10px;
            z-index: 100;
        }}
        .nav button {{
            padding: 12px 24px;
            border: none;
            border-radius: 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .nav button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }}
        .progress {{
            position: fixed;
            bottom: 15px;
            left: 50%;
            transform: translateX(-50%);
            color: #667eea;
            font-size: 14px;
            z-index: 100;
        }}
    </style>
</head>
<body>
    {slides_html}
    <div class="nav">
        <button onclick="prev()">⬅ 上一页</button>
        <button onclick="next()">下一页 ➡</button>
    </div>
    <div class="progress" id="progress">1 / {len(articles)}</div>
    <script>
        let current = 0;
        const slides = document.querySelectorAll('.slide');
        const progress = document.getElementById('progress');

        function show(n) {{
            slides.forEach(s => s.classList.remove('active'));
            slides[n].classList.add('active');
            progress.textContent = (n + 1) + ' / ' + slides.length;
        }}

        function next() {{
            current = (current + 1) % slides.length;
            show(current);
        }}

        function prev() {{
            current = (current - 1 + slides.length) % slides.length;
            show(current);
        }}

        // 键盘快捷键
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowRight' || e.key === ' ') {{
                e.preventDefault();
                next();
            }} else if (e.key === 'ArrowLeft') {{
                e.preventDefault();
                prev();
            }}
        }});

        show(0);
    </script>
</body>
</html>"""

    output_path.write_text(html_content, encoding="utf-8")
    return output_path
