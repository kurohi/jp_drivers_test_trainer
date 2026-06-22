"""Attempt schemas."""

from typing import Literal

from pydantic import BaseModel, Field

from .ui_meta import Language


class AnswerItem(BaseModel):
    """A single answer submitted by the user."""

    question_id: int
    user_answer: Literal["true", "false"]
    time_spent_ms: int | None = None


class AttemptStartIn(BaseModel):
    """Start a new mock test attempt."""

    language: Language
    theme_ids: list[int] | None = None  # None = all themes
    question_count: int = Field(default=50, ge=1, le=200)
    tricky_ratio: float = Field(default=0.5, ge=0.0, le=1.0)
    time_limit_seconds: int = Field(default=1800, ge=60, le=7200)
    seed: int | None = None


class AttemptSubmitIn(BaseModel):
    """Submit answers for an attempt."""

    answers: list[AnswerItem]


class AttemptAnswerOut(BaseModel):
    """A single answer result in attempt output."""

    question_id: int
    is_correct: bool
    user_answer: Literal["true", "false"]
    correct_answer: Literal["true", "false"]
    explanation_en: str
    explanation_pt: str


class AttemptResultOut(BaseModel):
    """Result of a completed attempt."""

    model_config = {"from_attributes": True}

    attempt_id: int
    score: int
    max_score: int
    passed: bool
    tricky_ratio_actual: float
    boundary_score: int = 45
    answers: list[AttemptAnswerOut]
