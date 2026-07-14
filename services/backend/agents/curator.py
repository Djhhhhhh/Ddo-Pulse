"""内容策展 Agent。"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from agents.base import Agent
from tools.analyzers.llm_analyzer import OpenRouterAnalyzer

logger = logging.getLogger(__name__)


class CuratorAgent(Agent):
    """内容策展 Agent - 负责文章分析和质量评估"""

    def __init__(self, profile: Dict[str, Any]):
        super().__init__("curator", {"profile": profile})
        self._analyzer: OpenRouterAnalyzer | None = None

    @property
    def analyzer(self) -> OpenRouterAnalyzer:
        if self._analyzer is None:
            self._analyzer = OpenRouterAnalyzer(self.config["profile"])
        return self._analyzer

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析文章

        context:
            - rows: 待分析的文章列表
            - interest_keywords: 兴趣关键词列表

        return:
            - results: 分析结果列表
            - stats: 统计信息
        """
        rows = context.get("rows", [])
        interest_keywords = context.get("interest_keywords", [])

        results: List[Dict[str, Any]] = []
        stats = {"total": len(rows), "analyzed": 0, "errors": 0}

        for row in rows:
            try:
                title = row.get("title", "")
                content = row.get("content_snippet", "")

                result = self.analyzer.analyze(title, content)
                results.append({
                    "raw_item_id": row["id"],
                    "is_quality": result.is_quality,
                    "score": result.score,
                    "categories": result.categories,
                    "summary_zh": result.summary_zh,
                    "reason": result.reason,
                })
                stats["analyzed"] += 1
            except Exception as exc:
                logger.exception("Analyze failed for raw_item %s: %s", row.get("id"), exc)
                stats["errors"] += 1

        return {"results": results, "stats": stats}

    def analyze_single(self, title: str, content: str) -> Dict[str, Any]:
        """分析单篇文章"""
        result = self.analyzer.analyze(title, content)
        return {
            "is_quality": result.is_quality,
            "score": result.score,
            "categories": result.categories,
            "summary_zh": result.summary_zh,
            "reason": result.reason,
        }
