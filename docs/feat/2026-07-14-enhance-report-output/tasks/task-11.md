# Task 11: HTML 报告生成

## 关联验收点
- G5: HTML PPT 式报告

## 任务描述
创建 HTML PPT 式报告生成器。

## 具体步骤

1. 创建 `tools/publishers/html_report.py`：
   - `generate_digest_html()` - 生成 HTML 报告
   - 每篇文章一个"幻灯片"
   - 支持翻页交互

2. HTML 模板设计：
   - 纯 HTML/CSS/JS
   - 响应式布局
   - 翻页按钮

## 输出文件
- `services/backend/tools/publishers/html_report.py`

## HTML 模板结构
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Ddo-Pulse 精选 · {date}</title>
    <style>
        /* 幻灯片样式 */
        .slide { display: none; height: 100vh; padding: 40px; }
        .slide.active { display: flex; flex-direction: column; justify-content: center; }
        /* 翻页按钮 */
        .nav { position: fixed; bottom: 20px; right: 20px; }
    </style>
</head>
<body>
    {slides}
    <div class="nav">
        <button onclick="prev()">上一页</button>
        <button onclick="next()">下一页</button>
    </div>
    <script>
        let current = 0;
        const slides = document.querySelectorAll('.slide');
        function show(n) { slides.forEach(s => s.classList.remove('active')); slides[n].classList.add('active'); }
        function next() { current = (current + 1) % slides.length; show(current); }
        function prev() { current = (current - 1 + slides.length) % slides.length; show(current); }
        show(0);
    </script>
</body>
</html>
```

## 验证命令
```bash
ls ~/.ddo_pulse/reports/*/digest.html 2>/dev/null | head -1 || echo "No HTML report yet"
```
