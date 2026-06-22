from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base

if TYPE_CHECKING:
    from models.question import Question


class Theme(Base):
    """
    Hierarchical theme tree for driver-test subjects.
    Root themes are the 22 official domains; children allow sub-topics.
    """
    __tablename__ = "themes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    name_pt: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("themes.id"), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Self-referential hierarchy
    parent: Mapped[Optional[Theme]] = relationship(
        "Theme", remote_side="Theme.id", back_populates="children"
    )
    children: Mapped[list[Theme]] = relationship(
        "Theme", back_populates="parent"
    )
    # Theme -> Questions (string reference resolved by SQLAlchemy at runtime)
    questions: Mapped[list[Question]] = relationship(
        "Question", back_populates="theme", lazy="noload"
    )
