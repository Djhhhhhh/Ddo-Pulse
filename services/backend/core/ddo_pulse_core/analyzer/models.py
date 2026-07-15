"""Pydantic models for LLM analysis output."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AnalysisOutput(BaseModel):
    is_quality: bool
    score: int = Field(ge=1, le=10)
    categories: list[str] = Field(default_factory=list)
    summary_zh: str
    reason: str
    relevance: int | None = Field(default=None, ge=0, le=10)
    novelty: int | None = Field(default=None, ge=0, le=10)

    @field_validator("categories", mode="before")
    @classmethod
    def _coerce_categories(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value] if value.strip() else []
        if isinstance(value, list):
            return [str(v) for v in value if str(v).strip()]
        return []
