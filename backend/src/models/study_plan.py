from __future__ import annotations

from datetime import datetime

from sqlalchemy import TEXT, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class StudyPlan(Base):
    """
    A personalised study plan covering N days across selected themes.
    days_json: JSON array of {day: int, theme_ids: int[], description: str}
    weak_themes_json: JSON array of theme IDs the user is weakest on.
    source: "default-beginner" | "llm-generated"
    """
    __tablename__ = "study_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    days_json: Mapped[str] = mapped_column(TEXT, nullable=False)
    source: Mapped[str] = mapped_column(
        String(50), default="default-beginner"
    )
    weak_themes_json: Mapped[str] = mapped_column(TEXT, nullable=True)
