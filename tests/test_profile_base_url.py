"""Tests for base_url field support in LLM profiles.

Covers:
- G1: ProfileOut and ProfileUpdate schemas include base_url
- G2: update_llm_profile supports base_url parameter
"""

import sqlite3

import pytest


# ── G1. API Schema Tests ──────────────────────────────────────────────


class TestProfileOutBaseUrl:
    """Verify ProfileOut schema exposes base_url field."""

    def test_profile_out_has_base_url_field(self):
        """G1-cmd1: ProfileOut must include base_url."""
        # Arrange
        from services.backend.api.ddo_pulse_api.schemas import ProfileOut

        # Act
        p = ProfileOut(
            id=1,
            name="test",
            base_url="https://openrouter.ai/api/v1",
            model="gpt-4o",
            is_default=True,
            score_threshold=7,
            api_key_set=True,
        )

        # Assert
        assert hasattr(p, "base_url")
        assert p.base_url == "https://openrouter.ai/api/v1"

    def test_profile_out_base_url_custom_value(self):
        """G1-cmd1: ProfileOut accepts custom base_url."""
        from services.backend.api.ddo_pulse_api.schemas import ProfileOut

        p = ProfileOut(
            id=1,
            name="test",
            base_url="http://localhost:11434/v1",
            model="llama3",
            is_default=False,
            score_threshold=7,
            api_key_set=False,
        )

        assert p.base_url == "http://localhost:11434/v1"


class TestProfileUpdateBaseUrl:
    """Verify ProfileUpdate schema accepts base_url field."""

    def test_profile_update_has_base_url_field(self):
        """G1-cmd2: ProfileUpdate must accept base_url."""
        from services.backend.api.ddo_pulse_api.schemas import ProfileUpdate

        # Act
        p = ProfileUpdate(
            base_url="http://localhost:11434/v1",
            model="llama3",
        )

        # Assert
        assert p.base_url == "http://localhost:11434/v1"

    def test_profile_update_base_url_optional(self):
        """G1-cmd2: ProfileUpdate base_url is optional."""
        from services.backend.api.ddo_pulse_api.schemas import ProfileUpdate

        p = ProfileUpdate(model="gpt-4o")

        assert p.base_url is None


# ── G2. DB Layer Tests ────────────────────────────────────────────────


class TestUpdateLlmProfileBaseUrl:
    """Verify update_llm_profile handles base_url correctly."""

    @pytest.fixture
    def db_conn(self):
        """Create an in-memory SQLite database with schema."""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        # Read and execute schema
        import os

        schema_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "services",
            "backend",
            "db",
            "schema.sql",
        )
        with open(schema_path) as f:
            conn.executescript(f.read())
        return conn

    @pytest.fixture
    def repo(self, db_conn):
        """Create a Repository instance."""
        from services.backend.db.ddo_pulse_db.repository import Repository

        return Repository(db_conn)

    def test_update_base_url(self, repo):
        """G2-cmd1: update_llm_profile updates base_url field."""
        # Arrange
        repo.ensure_default_profile_from_dict(
            {
                "name": "default",
                "model": "gpt-4o",
                "api_key": "sk-test",
                "base_url": "https://openrouter.ai/api/v1",
            }
        )

        # Act
        result = repo.update_llm_profile(1, base_url="http://localhost:11434/v1")

        # Assert
        assert result is True
        row = repo.get_llm_profile(1)
        assert row["base_url"] == "http://localhost:11434/v1"

    def test_update_base_url_preserves_when_none(self, repo):
        """G2-cmd1: update_llm_profile preserves base_url when None."""
        # Arrange
        repo.ensure_default_profile_from_dict(
            {
                "name": "default",
                "model": "gpt-4o",
                "api_key": "sk-test",
                "base_url": "https://openrouter.ai/api/v1",
            }
        )

        # Act - update only model, not base_url
        repo.update_llm_profile(1, model="gpt-4o-mini")

        # Assert - base_url unchanged
        row = repo.get_llm_profile(1)
        assert row["base_url"] == "https://openrouter.ai/api/v1"

    def test_default_base_url_value(self, db_conn):
        """G1-cmd1: Database default base_url is correct."""
        # Arrange & Act
        db_conn.execute(
            "INSERT INTO llm_profiles (name, model) VALUES (?, ?)",
            ("test", "gpt-4o"),
        )
        row = db_conn.execute(
            "SELECT base_url FROM llm_profiles WHERE id=1"
        ).fetchone()

        # Assert
        assert row["base_url"] == "https://openrouter.ai/api/v1"
