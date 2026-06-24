from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class SkillModule(Base):
    """
    A skill module (micro-learning unit) with correct/wrong trajectories,
    common mistakes, checklist, and pro-tips in both languages.
    """
    __tablename__ = "skill_modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    name_pt: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    overview_en: Mapped[str] = mapped_column(Text, nullable=False)
    overview_pt: Mapped[str] = mapped_column(Text, nullable=False)
    svg_path: Mapped[str] = mapped_column(String(300), nullable=True)
    correct_trajectory_json: Mapped[str] = mapped_column(Text, nullable=False)
    wrong_trajectory_json: Mapped[str] = mapped_column(Text, nullable=False)
    common_mistakes_json: Mapped[str] = mapped_column(Text, nullable=False)
    checklist_json: Mapped[str] = mapped_column(Text, nullable=False)
    pro_tip_en: Mapped[str] = mapped_column(Text, nullable=False)
    pro_tip_pt: Mapped[str] = mapped_column(Text, nullable=False)
