"""每日精选工作流。"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from agents.curator import CuratorAgent
from agents.reporter import ReporterAgent
from tools.publishers.feishu import build_feishu_post_payload, send_feishu_webhook

logger = logging.getLogger(__name__)


class DailyDigestWorkflow:
    """每日精选工作流 - 整合 fetch、analyze、digest、output 流程"""

    def __init__(self, db, profile: Dict[str, Any], job_config: Dict[str, Any]):
        self.db = db
        self.profile = profile
        self.job_config = job_config
        self.curator = CuratorAgent(profile)
        self.reporter = ReporterAgent(profile)

    def run(self) -> Dict[str, Any]:
        """
        执行工作流

        return:
            - fetch: 抓取统计
            - analyze: 分析统计
            - output: 输出统计
            - feishu_pushed: 飞书推送状态
        """
        stats: Dict[str, Any] = {
            "fetch": 0,
            "analyze": 0,
            "digest": 0,
            "output": 0,
            "feishu_pushed": False,
            "report_dir": None,
        }

        try:
            # 1. 获取精选文章
            articles = self.db.list_digest_candidates(
                score_threshold=int(self.job_config.get("score_threshold", 7)),
                limit=int(self.job_config.get("digest_top_n", 8)),
                exclude_pushed=True,
            )
            stats["digest"] = len(articles)

            if not articles:
                logger.info("No articles to digest")
                return stats

            # 2. 转换为字典格式
            article_dicts = []
            for row in articles:
                article_dicts.append({
                    "id": row["id"],
                    "title": row["title"],
                    "url": row["url"],
                    "score": row["score"],
                    "categories": json.loads(row.get("categories_json", "[]")),
                    "summary_zh": row.get("summary_zh", ""),
                    "reason": row.get("reason", ""),
                    "content_snippet": row.get("content_snippet", ""),
                })

            # 3. 生成报告
            result = self.reporter.run({
                "articles": article_dicts,
                "job_config": self.job_config,
            })

            stats["output"] = 1
            stats["report_dir"] = result.get("report_dir")

            # 4. 推送到飞书
            if self.job_config.get("push_digest"):
                webhook = (self.job_config.get("feishu_webhook_url") or "").strip()
                if webhook:
                    payload = build_feishu_post_payload(
                        result.get("timestamp", ""),
                        articles,
                        batch_label=f"新增 {len(articles)} 篇"
                    )
                    ok, response = send_feishu_webhook(webhook, payload)
                    stats["feishu_pushed"] = ok

                    if ok:
                        # 标记文章已推送
                        item_ids = [int(r["id"]) for r in articles]
                        self.db.mark_articles_pushed(item_ids)

        except Exception as exc:
            logger.exception("Daily digest workflow failed: %s", exc)
            stats["error"] = str(exc)

        return stats
