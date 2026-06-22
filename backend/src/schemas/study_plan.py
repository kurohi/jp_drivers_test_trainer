"""Study plan schemas."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class WeakThemeStat(BaseModel):
    """Weak theme statistics."""

    model_config = {"from_attributes": True}

    theme_id: int
    name_en: str
    wrong_count: int
    total_attempts: int


class PlanDay(BaseModel):
    """A single study day in a plan."""

    model_config = {"from_attributes": True}

    date: date
    theme_ids: list[int]
    question_count: int
    focus_note_en: str
    focus_note_pt: str


class StudyPlanGenerateIn(BaseModel):
    """Generate a new study plan."""

    available_days: int = Field(default=7, ge=1, le=30)
    hours_per_day: float = Field(default=1.5, ge=0.25, le=8.0)


class StudyPlanOut(BaseModel):
    """Full study plan output."""

    model_config = {"from_attributes": True}

    id: int
    created_at: str  # ISO8601 datetime string
    source: Literal["default-beginner", "llm-generated"]
    days: list[PlanDay]
