# Task 10: 本地 MD 报告

## 关联验收点
- G4: 本地 MD 报告

## 任务描述
创建本地 Markdown 格式的报告生成器。

## 具体步骤

1. 创建 `tools/publishers/markdown.py`：
   - `generate_digest_md()` - 生成公众号友好的 MD 报告
   - 包含：标题、评分、分类、深度解读、链接

2. 格式要求：
   - 适配微信公众号排版
   - 包含深度解读内容

## 输出文件
- `services/backend/tools/publishers/markdown.py`

## 代码设计
```python
from pathlib import Path
from typing import List, Any

def generate_digest_md(
    date: str,
    articles: List[Any],
    output_path: Path
) -> Path:
    """生成公众号友好的 MD 报告"""
    lines = [f"# Ddo-Pulse 精选 · {date}", ""]
    
    for idx, article in enumerate(articles, 1):
        title = article["title"]
        url = article["url"]
        score = article["score"]
        categories = "、".join(article.get("categories", []))
        summary = article.get("summary_zh", "")
        deep_analysis = article.get("deep_analysis", {})
        
        lines.append(f"## {idx}. [{title}]({url})")
        lines.append(f"**{score} 分** · {categories}")
        
        if summary:
            lines.append("")
            lines.append(summary)
        
        if deep_analysis:
            lines.append("")
            lines.append("### 深度解读")
            lines.append("")
            if deep_analysis.get("core_content"):
                lines.append(deep_analysis["core_content"])
            if deep_analysis.get("key_points"):
                lines.append("")
                lines.append("**关键观点：**")
                for point in deep_analysis["key_points"]:
                    lines.append(f"- {point}")
            if deep_analysis.get("insights"):
                lines.append("")
                lines.append(f"**思路启发：** {deep_analysis['insights']}")
        
        lines.append("")
        lines.append("---")
        lines.append("")
    
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
```

## 验证命令
```bash
ls ~/.ddo_pulse/reports/*/digest.md 2>/dev/null | head -1 || echo "No MD report yet"
```
