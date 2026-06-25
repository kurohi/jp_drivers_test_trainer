from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BOOLEAN, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base

if TYPE_CHECKING:
    from models.attempt import AttemptAnswer
    from models.theme import Theme


class Question(Base):
    """
    A single driver-test question tied to a Theme.
    Each question has bilingual prompts/answers/explanations.
    """
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    theme_id: Mapped[int] = mapped_column(Integer, ForeignKey("themes.id"), nullable=False)
    prompt_en: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_pt: Mapped[str] = mapped_column(Text, nullable=False)
    answer_en: Mapped[str] = mapped_column(Text, nullable=False)  # "true" | "false"
    answer_pt: Mapped[str] = mapped_column(Text, nullable=False)
    explanation_en: Mapped[str] = mapped_column(Text, nullable=False)
    explanation_pt: Mapped[str] = mapped_column(Text, nullable=False)
    tricky: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    tricky_pattern: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    translations_status: Mapped[str] = mapped_column(
        String(20), default="missing"
    )  # "verified" | "machine" | "missing"
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    license: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    attribution: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    theme: Mapped[Theme] = relationship(
        "Theme", back_populates="questions", lazy="noload"
    )
    attempt_answers: Mapped[list[AttemptAnswer]] = relationship(
        "AttemptAnswer", back_populates="question", lazy="noload"
    )
