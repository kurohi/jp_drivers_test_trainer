from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BOOLEAN, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base

if TYPE_CHECKING:
    from models.question import Question


class Attempt(Base):
    """
    A complete quiz session (all questions answered or time expired).
    """
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    max_score: Mapped[int] = mapped_column(Integer, default=0)
    passed: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    language: Mapped[str] = mapped_column(String(5), default="en")  # "en" | "pt"
    difficulty_tricky: Mapped[float] = mapped_column(Float, default=0.0)
    time_limit_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    answers: Mapped[list[AttemptAnswer]] = relationship(
        "AttemptAnswer", back_populates="attempt", lazy="noload"
    )


class AttemptAnswer(Base):
    """
    An individual question answer within an Attempt.
    """
    __tablename__ = "attempt_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("attempts.id"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id"), nullable=False
    )
    user_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    time_spent_ms: Mapped[int] = mapped_column(Integer, default=0)

    attempt: Mapped[Attempt] = relationship(
        "Attempt", back_populates="answers", lazy="noload"
    )
    question: Mapped[Question] = relationship(
        "Question", back_populates="attempt_answers", lazy="noload"
    )
