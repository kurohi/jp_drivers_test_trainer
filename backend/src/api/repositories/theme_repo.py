"""Theme repository — hierarchical theme tree queries."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.theme import Theme


class ThemeRepo:
    """CRUD + tree queries for Theme entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_root_themes(self) -> list[Theme]:
        """Return all root themes (parent_id IS NULL) ordered by sort_order."""
        stmt = (
            select(Theme)
            .where(Theme.parent_id.is_(None))
            .order_by(Theme.sort_order)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_theme_tree(self) -> list[Theme]:
        """
        Return the full theme tree with children eagerly loaded.
        Uses joinedload to fetch the hierarchy in a single query.
        """
        from sqlalchemy.orm import joinedload

        stmt = (
            select(Theme)
            .where(Theme.parent_id.is_(None))
            .options(joinedload(Theme.children))
            .order_by(Theme.sort_order)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_slug(self, slug: str) -> Optional[Theme]:
        """Return a single theme by its slug, or None."""
        stmt = select(Theme).where(Theme.slug == slug)
        result = await self._session.execute(stmt)
        return result.scalars().first()
