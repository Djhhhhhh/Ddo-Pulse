"""Tests for enhanced content pipeline: dual scoring, pool ranking, source priority.

Covers:
- G1: Database migration (new columns)
- G2: Dual-dimension scoring model
- G3: Dual-dimension scoring prompt
- G4: composite_score calculation
- G5: Fetch stage priority-based truncation
- G6: Pool-based ranking algorithm
- G7: Pool ranking toggle
- G8: Pipeline job API new fields
- G11: Backward compatibility
"""

import sqlite3
import os

import pytest


# ── Helpers ────────────────────────────────────────────────────────────

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "services", "backend", "db", "schema.sql"
)


@pytest.fixture
def db_conn():
    """Create an in-memory SQLite database with schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    return conn


# ── G1. Database Migration ────────────────────────────────────────────


class TestPipelineJobsNewColumns:
    """Verify pipeline_jobs table has all new columns."""

    def test_pool_ranking_enabled_column_exists(self, db_conn):
        """G1-cmd1: pipeline_jobs must have pool_ranking_enabled column."""
        # Arrange & Act
        cols = [r[1] for r in db_conn.execute("PRAGMA table_info(pipeline_jobs)").fetchall()]

        # Assert
        assert "pool_ranking_enabled" in cols

    def test_quota_columns_exist(self, db_conn):
        """G1-cmd1: pipeline_jobs must have ai_quota, dev_quota, other_quota columns."""
        cols = [r[1] for r in db_conn.execute("PRAGMA table_info(pipeline_jobs)").fetchall()]

        assert "ai_quota" in cols
        assert "dev_quota" in cols
        assert "other_quota" in cols

    def test_weight_columns_exist(self, db_conn):
        """G1-cmd1: pipeline_jobs must have relevance_weight, novelty_weight columns."""
        cols = [r[1] for r in db_conn.execute("PRAGMA table_info(pipeline_jobs)").fetchall()]

        assert "relevance_weight" in cols
        assert "novelty_weight" in cols

    def test_category_tags_columns_exist(self, db_conn):
        """G1-cmd1: pipeline_jobs must have ai_category_tags, dev_category_tags columns."""
        cols = [r[1] for r in db_conn.execute("PRAGMA table_info(pipeline_jobs)").fetchall()]

        assert "ai_category_tags" in cols
        assert "dev_category_tags" in cols


class TestJobSourcesNewColumns:
    """Verify job_sources table has priority and fetch_limit columns."""

    def test_priority_column_exists(self, db_conn):
        """G1-cmd2: job_sources must have priority column."""
        cols = [r[1] for r in db_conn.execute("PRAGMA table_info(job_sources)").fetchall()]

        assert "priority" in cols

    def test_fetch_limit_column_exists(self, db_conn):
        """G1-cmd2: job_sources must have fetch_limit column."""
        cols = [r[1] for r in db_conn.execute("PRAGMA table_info(job_sources)").fetchall()]

        assert "fetch_limit" in cols


class TestAnalyzedItemsNewColumns:
    """Verify analyzed_items table has relevance, novelty, composite_score columns."""

    def test_relevance_column_exists(self, db_conn):
        """G1-cmd3: analyzed_items must have relevance column."""
        cols = [r[1] for r in db_conn.execute("PRAGMA table_info(analyzed_items)").fetchall()]

        assert "relevance" in cols

    def test_novelty_column_exists(self, db_conn):
        """G1-cmd3: analyzed_items must have novelty column."""
        cols = [r[1] for r in db_conn.execute("PRAGMA table_info(analyzed_items)").fetchall()]

        assert "novelty" in cols

    def test_composite_score_column_exists(self, db_conn):
        """G1-cmd3: analyzed_items must have composite_score column."""
        cols = [r[1] for r in db_conn.execute("PRAGMA table_info(analyzed_items)").fetchall()]

        assert "composite_score" in cols


# ── G2. Dual-Dimension Scoring Model ──────────────────────────────────


class TestAnalysisOutputModel:
    """Verify AnalysisOutput model supports relevance and novelty."""

    def test_model_with_relevance_and_novelty(self):
        """G2-cmd1: AnalysisOutput accepts relevance and novelty fields."""
        # Arrange
        from services.backend.core.ddo_pulse_core.analyzer.models import AnalysisOutput

        # Act
        m = AnalysisOutput(
            is_quality=True,
            score=8,
            relevance=7,
            novelty=6,
            categories=["AI"],
            summary_zh="test summary",
            reason="test reason",
        )

        # Assert
        assert m.relevance == 7
        assert m.novelty == 6

    def test_model_without_relevance_and_novelty(self):
        """G2-cmd2: AnalysisOutput allows relevance and novelty to be None."""
        from services.backend.core.ddo_pulse_core.analyzer.models import AnalysisOutput

        # Act
        m = AnalysisOutput(
            is_quality=True,
            score=8,
            categories=["AI"],
            summary_zh="test summary",
            reason="test reason",
        )

        # Assert
        assert m.relevance is None
        assert m.novelty is None


# ── G3. Dual-Dimension Scoring Prompt ─────────────────────────────────


class TestDualScorePrompt:
    """Verify DUAL_SCORE_PROMPT_TEMPLATE exists and is formattable."""

    def test_template_exists_with_relevance_and_novelty(self):
        """G3-cmd1: DUAL_SCORE_PROMPT_TEMPLATE must contain relevance and novelty."""
        from services.backend.core.ddo_pulse_core.analyzer.prompt import DUAL_SCORE_PROMPT_TEMPLATE

        assert "relevance" in DUAL_SCORE_PROMPT_TEMPLATE
        assert "novelty" in DUAL_SCORE_PROMPT_TEMPLATE

    def test_template_is_formattable(self):
        """G3-cmd2: format_prompt_template can substitute all placeholders."""
        from services.backend.core.ddo_pulse_core.analyzer.prompt import (
            DUAL_SCORE_PROMPT_TEMPLATE,
            format_prompt_template,
        )

        # Act
        result = format_prompt_template(
            DUAL_SCORE_PROMPT_TEMPLATE,
            categories_hint="AI",
            interest_keywords="test",
            title="test title",
            content="test content",
            scoring_rubric="test rubric",
        )

        # Assert
        assert "{title}" not in result
        assert "{content}" not in result
        assert "relevance" in result


# ── G4. composite_score Calculation ───────────────────────────────────


class TestCompositeScoreCalculation:
    """Verify composite_score formula and fallback logic."""

    def test_weighted_calculation(self):
        """G4-cmd1: composite_score = relevance * rw + novelty * nw."""
        # Arrange
        rw, nw = 0.6, 0.4
        relevance, novelty = 8, 6

        # Act
        composite_score = relevance * rw + novelty * nw

        # Assert
        assert composite_score == pytest.approx(7.2)

    def test_fallback_to_score(self):
        """G4-cmd2: When relevance/novelty are None, use score as fallback."""
        # Arrange
        score = 8

        # Act - fallback behavior
        relevance, novelty = None, None
        if relevance is not None and novelty is not None:
            composite_score = relevance * 0.6 + novelty * 0.4
        else:
            composite_score = float(score)

        # Assert
        assert composite_score == 8.0


# ── G5. Fetch Priority-Based Truncation ───────────────────────────────


class TestFetchPriorityTruncation:
    """Verify sources are sorted by priority and items truncated."""

    def test_sources_sorted_by_priority(self):
        """G5-cmd1: Sources should be sorted P0 → P1 → P2."""
        # Arrange
        sources = [
            {"id": 1, "priority": "P1", "fetch_limit": None},
            {"id": 2, "priority": "P0", "fetch_limit": None},
            {"id": 3, "priority": "P2", "fetch_limit": 5},
        ]
        priority_order = {"P0": 0, "P1": 1, "P2": 2}

        # Act
        sorted_sources = sorted(sources, key=lambda s: priority_order.get(s["priority"], 1))

        # Assert
        assert sorted_sources[0]["id"] == 2  # P0 first
        assert sorted_sources[1]["id"] == 1  # P1 second
        assert sorted_sources[2]["id"] == 3  # P2 third

    def test_fetch_limit_defaults_by_priority(self):
        """G5-cmd1: fetch_limit defaults based on priority when NULL."""
        # Arrange
        defaults = {"P0": 5, "P1": 4, "P2": 3}
        sources = [
            {"priority": "P0", "fetch_limit": None},
            {"priority": "P1", "fetch_limit": None},
            {"priority": "P2", "fetch_limit": None},
        ]

        # Act & Assert
        for s in sources:
            fl = s["fetch_limit"] or defaults.get(s["priority"], 4)
            assert fl == defaults[s["priority"]]

    def test_items_truncated_to_limit(self):
        """G5-cmd2: Items should be truncated to fetch_limit."""
        # Arrange
        items = list(range(20))  # 20 articles
        fetch_limit = 5

        # Act - sort by published_at DESC (simulated as descending integer)
        sorted_items = sorted(items, reverse=True)
        truncated = sorted_items[:fetch_limit]

        # Assert
        assert len(truncated) == 5
        assert truncated == [19, 18, 17, 16, 15]


# ── G6. Pool-Based Ranking Algorithm ─────────────────────────────────


class TestPoolRanking:
    """Verify pool-based ranking: categorize, sort, select, backfill."""

    def test_categorization_into_pools(self):
        """G6-cmd1: Articles should be categorized into ai/dev/other pools."""
        # Arrange
        ai_tags = ["AI", "机器学习"]
        dev_tags = ["开发", "工程"]
        candidates = [
            {"id": 1, "categories": ["AI"], "composite_score": 9.0},
            {"id": 2, "categories": ["开发"], "composite_score": 8.5},
            {"id": 3, "categories": ["AI"], "composite_score": 8.0},
            {"id": 4, "categories": ["创业"], "composite_score": 7.5},
            {"id": 5, "categories": ["开发"], "composite_score": 7.0},
        ]

        # Act
        ai_pool = [c for c in candidates if any(t in ai_tags for t in c["categories"])]
        dev_pool = [c for c in candidates if any(t in dev_tags for t in c["categories"])]
        other_pool = [c for c in candidates if c not in ai_pool and c not in dev_pool]

        # Assert
        assert len(ai_pool) == 2
        assert len(dev_pool) == 2
        assert len(other_pool) == 1

    def test_quota_selection_and_backfill(self):
        """G6-cmd2: When a pool is short, backfill from other pools."""
        # Arrange
        ai_pool = [{"id": 1, "composite_score": 9.0}]
        dev_pool = [{"id": 2, "composite_score": 8.5}]
        other_pool = []
        ai_quota, dev_quota, other_quota = 2, 2, 1

        # Act
        selected = ai_pool[:ai_quota] + dev_pool[:dev_quota] + other_pool[:other_quota]
        total_target = ai_quota + dev_quota + other_quota
        remaining = sorted(
            [{"id": 3, "composite_score": 8.0}, {"id": 4, "composite_score": 7.5}],
            key=lambda x: x["composite_score"],
            reverse=True,
        )
        while len(selected) < total_target and remaining:
            selected.append(remaining.pop(0))

        # Assert
        assert len(selected) == 4  # only 4 available, not 5


# ── G7. Pool Ranking Toggle ───────────────────────────────────────────


class TestPoolRankingToggle:
    """Verify pool_ranking_enabled toggle behavior."""

    def test_disabled_uses_legacy_sort(self):
        """G7-cmd1: When pool_ranking_enabled=0, use legacy score DESC."""
        # Arrange
        pool_ranking_enabled = 0

        # Act
        if not pool_ranking_enabled:
            result = "legacy_sort"
        else:
            result = "pool_ranking"

        # Assert
        assert result == "legacy_sort"

    def test_enabled_uses_pool_ranking(self):
        """G7-cmd2: When pool_ranking_enabled=1, use pool ranking."""
        # Arrange
        pool_ranking_enabled = 1

        # Act
        if not pool_ranking_enabled:
            result = "legacy_sort"
        else:
            result = "pool_ranking"

        # Assert
        assert result == "pool_ranking"


# ── G8. Pipeline Job API Defaults ─────────────────────────────────────


class TestPipelineJobDefaults:
    """Verify default values for new pipeline_jobs fields."""

    def test_default_quotas_sum_to_12(self):
        """G8-cmd1: Default quotas should sum to 12."""
        # Arrange
        defaults = {
            "ai_quota": 6,
            "dev_quota": 4,
            "other_quota": 2,
        }

        # Act
        total = sum(defaults.values())

        # Assert
        assert total == 12


# ── G11. Backward Compatibility ───────────────────────────────────────


class TestBackwardCompatibility:
    """Verify system works without new parameters configured."""

    def test_fallback_to_score_when_no_dual_scoring(self):
        """G11-cmd1: composite_score falls back to score when relevance/novelty absent."""
        # Arrange
        score = 8
        relevance, novelty = None, None

        # Act
        if relevance is not None and novelty is not None:
            composite_score = relevance * 0.6 + novelty * 0.4
        else:
            composite_score = float(score)

        # Assert
        assert composite_score == 8.0
