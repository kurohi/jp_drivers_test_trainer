"""Question repository — list, filter, random sample, bulk create."""

from __future__ import annotations

import random
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.question import Question


class QuestionRepo:
    """CRUD + sampling queries for Question entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self,
        theme_id: Optional[int] = None,
        tricky_only: bool = False,
        language: str = "en",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Question]:
        """
        List questions with optional filters.
        Excludes questions where translations_status="missing" for the
        requested language.
        """
        stmt = select(Question)

        if theme_id is not None:
            stmt = stmt.where(Question.theme_id == theme_id)

        if tricky_only:
            stmt = stmt.where(Question.tricky.is_(True))

        # Exclude questions missing translation for the requested language
        if language == "en":
            stmt = stmt.where(Question.translations_status != "missing")
        elif language == "pt":
            stmt = stmt.where(Question.translations_status != "missing")

        stmt = stmt.order_by(Question.id).limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, question_id: int) -> Optional[Question]:
        """Return a single question by ID, or None."""
        stmt = select(Question).where(Question.id == question_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def count_by_theme(self, theme_id: int) -> int:
        """Return the number of questions for a given theme."""
        stmt = select(func.count()).select_from(Question).where(
            Question.theme_id == theme_id
        )
        result = await self._session.execute(stmt)
        return int(result.scalar() or 0)

    async def random_sample(
        self,
        theme_ids: Optional[list[int]] = None,
        count: int = 50,
        tricky_ratio: float = 0.5,
        seed: Optional[int] = None,
    ) -> list[Question]:
        """
        Return a deterministic random sample of questions.

        - Filters by theme_ids if provided (None = all themes).
        - Applies tricky_ratio: fraction of questions that should be tricky.
        - Uses Python random.Random(seed) for determinism.
        - Raises ValueError if the pool is insufficient to produce `count` items.
        """
        stmt = select(Question)
        if theme_ids:
            stmt = stmt.where(Question.theme_id.in_(theme_ids))

        result = await self._session.execute(stmt)
        pool = list(result.scalars().all())

        if len(pool) < count:
            raise ValueError(
                f"Insufficient question pool: need {count}, have {len(pool)}"
            )

        rng = random.Random(seed)

        tricky_count = int(count * tricky_ratio)
        normal_count = count - tricky_count

        tricky_pool = [q for q in pool if q.tricky]
        normal_pool = [q for q in pool if not q.tricky]

        # If tricky pool is insufficient, fill from normal pool
        actual_tricky = min(tricky_count, len(tricky_pool))
        actual_normal = count - actual_tricky

        if len(normal_pool) < actual_normal:
            raise ValueError(
                f"Insufficient question pool after tricky allocation: "
                f"need {actual_normal} normal, have {len(normal_pool)}"
            )

        selected_tricky = rng.sample(tricky_pool, actual_tricky)
        selected_normal = rng.sample(normal_pool, actual_normal)

        combined = selected_tricky + selected_normal
        rng.shuffle(combined)
        return combined

    async def bulk_create(self, items: list[Question]) -> list[Question]:
        """Insert multiple questions in one transaction."""
        self._session.add_all(items)
        await self._session.flush()
        for item in items:
            await self._session.refresh(item)
        return items
