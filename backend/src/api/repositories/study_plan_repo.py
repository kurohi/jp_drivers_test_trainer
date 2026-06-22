"""Study plan repository — create, latest, list."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.study_plan import StudyPlan


class StudyPlanRepo:
    """CRUD queries for StudyPlan entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        days_json: str,
        source: str = "default-beginner",
        weak_themes_json: Optional[str] = None,
    ) -> StudyPlan:
        """Create a new StudyPlan and return it."""
        plan = StudyPlan(
            days_json=days_json,
            source=source,
            weak_themes_json=weak_themes_json,
        )
        self._session.add(plan)
        await self._session.flush()
        await self._session.refresh(plan)
        return plan

    async def latest(self) -> Optional[StudyPlan]:
        """Return the most recently created study plan, or None."""
        stmt = (
            select(StudyPlan)
            .order_by(StudyPlan.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list(self, limit: int = 10) -> list[StudyPlan]:
        """List study plans ordered by most recent first."""
        stmt = (
            select(StudyPlan)
            .order_by(StudyPlan.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
