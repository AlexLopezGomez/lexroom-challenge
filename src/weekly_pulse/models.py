from __future__ import annotations

import datetime

from pydantic import BaseModel, Field, computed_field, field_validator


class ModuleData(BaseModel):
    """Raw per-module metrics for one week."""

    name: str
    artifacts: int = Field(ge=0)
    errors: int = Field(ge=0)
    avg_response_ms: int = Field(ge=0)

    @computed_field  # type: ignore[misc]
    @property
    def error_rate(self) -> float:
        """Fraction of artifacts that resulted in errors."""
        return self.errors / self.artifacts if self.artifacts > 0 else 0.0


class WeekData(BaseModel):
    """All metrics captured for a single calendar week."""

    week: str
    daily_active_users: list[int] = Field(min_length=1)
    modules: list[ModuleData] = Field(min_length=1)

    @field_validator("week")
    @classmethod
    def validate_week(cls, v: str) -> str:
        """Ensure week is a valid ISO-8601 date string."""
        datetime.date.fromisoformat(v)
        return v

    @field_validator("daily_active_users")
    @classmethod
    def validate_dau(cls, v: list[int]) -> list[int]:
        """Reject any negative DAU values."""
        for val in v:
            if val < 0:
                raise ValueError(f"daily_active_users contains negative value: {val}")
        return v


class DAUStats(BaseModel):
    """Computed daily-active-user statistics comparing two weeks."""

    avg_current: float
    avg_previous: float
    pct_change: float


class ModuleRank(BaseModel):
    """A module's artifact volume rank."""

    name: str
    artifacts: int
    rank: int


class ErrorFlag(BaseModel):
    """A module whose error rate exceeds the configured threshold."""

    name: str
    error_rate: float
    errors: int
    artifacts: int


class PulseReport(BaseModel):
    """Assembled weekly pulse report ready for formatting."""

    week: str
    dau: DAUStats
    top_modules: list[ModuleRank]
    error_flags: list[ErrorFlag]
    highlight: str | None = None
