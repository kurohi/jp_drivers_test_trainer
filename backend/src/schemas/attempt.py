"""Attempt schemas."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .ui_meta import Language

VALID_TRICKY_RATIOS = {0.0, 0.25, 0.5, 0.75, 1.0}


class SelectionResult(BaseModel):
    """Result of question selection for a mock test attempt."""

    attempt_id: int
    questions: list[dict]  # Serialized question summaries
    tricky_ratio_actual: float
    question_count: int


class AnswerItem(BaseModel):
    """A single answer submitted by the user."""

    question_id: int
    user_answer: Literal["true", "false"]
    time_spent_ms: int | None = None


class AttemptStartIn(BaseModel):
    """Start a new mock test attempt."""

    language: Language
    theme_ids: list[int] | None = None  # None = all themes
    question_count: int = Field(default=50, ge=5, le=50)
    tricky_ratio: float = Field(default=0.5)
    time_limit_seconds: int = Field(default=1800, le=1800)
    seed: int | None = None

    @field_validator("tricky_ratio")
    @classmethod
    def validate_tricky_ratio(cls, v: float) -> float:
        if v not in VALID_TRICKY_RATIOS:
            raise ValueError(
                f"tricky_ratio must be one of {sorted(VALID_TRICKY_RATIOS)}, got {v}"
            )
        return v


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
