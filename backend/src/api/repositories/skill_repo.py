"""Skill module repository — list and lookup."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.skill_module import SkillModule


class SkillRepo:
    """CRUD queries for SkillModule entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_modules(self) -> list[SkillModule]:
        """List all skill modules ordered by sort_order."""
        stmt = select(SkillModule).order_by(SkillModule.sort_order)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Optional[SkillModule]:
        """Return a single skill module by slug, or None."""
        stmt = select(SkillModule).where(SkillModule.slug == slug)
        result = await self._session.execute(stmt)
        return result.scalars().first()
