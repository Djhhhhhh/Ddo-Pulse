"""报告生成 Agent。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from agents.base import Agent
from prompts.reporter import DEEP_ANALYSIS_PROMPT
from tools.publishers.report_dir import create_report_dir, generate_timestamp

logger = logging.getLogger(__name__)


class ReporterAgent(Agent):
    """报告生成 Agent - 负责深度解读和报告输出"""

    def __init__(self, profile: Dict[str, Any] | None = None):
        super().__init__("reporter", {"profile": profile})
        self._analyzer = None

    @property
    def analyzer(self):
        if self._analyzer is None and self.config.get("profile"):
            from tools.analyzers.llm_analyzer import OpenRouterAnalyzer
            self._analyzer = OpenRouterAnalyzer(self.config["profile"])
        return self._analyzer

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成报告

        context:
            - articles: 文章列表（含分析结果）
            - date: 报告日期（可选，默认今天）
            - job_config: 任务配置

        return:
            - report_dir: 报告目录路径
            - md_path: MD 文件路径
            - html_path: HTML 文件路径
            - screenshots: 截图路径列表
        """
        articles = context.get("articles", [])
        date = context.get("date")
        job_config = context.get("job_config", {})
        timestamp = context.get("timestamp") or generate_timestamp()

        # 创建报告目录
        report_dir = create_report_dir(timestamp)

        # 深度解读
        analyzed_articles = self._deep_analyze_batch(articles)

        # 生成 MD 报告
        md_path = self._generate_md(analyzed_articles, date or timestamp, report_dir)

        # 生成 HTML 报告
        html_path = self._generate_html(analyzed_articles, date or timestamp, report_dir)

        # 生成截图
        screenshots = self._generate_screenshots(html_path, report_dir)

        return {
            "report_dir": str(report_dir),
            "md_path": str(md_path),
            "html_path": str(html_path),
            "screenshots": [str(s) for s in screenshots],
            "timestamp": timestamp,
        }

    def _deep_analyze_batch(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量深度解读"""
        results = []
        for article in articles:
            try:
                deep_analysis = self._deep_analyze_single(
                    article.get("title", ""),
                    article.get("content_snippet", "") or article.get("summary_zh", "")
                )
                article["deep_analysis"] = deep_analysis
            except Exception as exc:
                logger.warning("Deep analysis failed: %s", exc)
                article["deep_analysis"] = {}
            results.append(article)
        return results

    def _deep_analyze_single(self, title: str, content: str) -> Dict[str, Any]:
        """单篇文章深度解读"""
        if not self.analyzer:
            return {}

        prompt = DEEP_ANALYSIS_PROMPT.format(title=title, content=content[:4000])

        try:
            from openai import OpenAI
            client = self.analyzer._client
            completion = client.chat.completions.create(
                model=str(self.config["profile"]["model"]),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1024,
            )
            raw = completion.choices[0].message.content or ""
            # 提取 JSON
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                return json.loads(raw[start:end + 1])
        except Exception as exc:
            logger.warning("Deep analysis API call failed: %s", exc)

        return {}

    def _generate_md(
        self,
        articles: List[Dict[str, Any]],
        date: str,
        report_dir: Path
    ) -> Path:
        """生成 MD 报告"""
        from tools.publishers.markdown import generate_digest_md
        md_path = report_dir / "digest.md"
        return generate_digest_md(date, articles, md_path)

    def _generate_html(
        self,
        articles: List[Dict[str, Any]],
        date: str,
        report_dir: Path
    ) -> Path:
        """生成 HTML 报告"""
        from tools.publishers.html_report import generate_digest_html
        html_path = report_dir / "digest.html"
        return generate_digest_html(date, articles, html_path)

    def _generate_screenshots(self, html_path: Path, report_dir: Path) -> List[Path]:
        """生成截图"""
        from tools.publishers.screenshot import generate_screenshots
        images_dir = report_dir / "images"
        return generate_screenshots(html_path, images_dir)
