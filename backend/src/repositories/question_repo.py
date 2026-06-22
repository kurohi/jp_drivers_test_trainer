"""Question repository — data access for Question ORM model."""

from __future__ import annotations

import random
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.question import Question


@dataclass
class QuestionSample:
    """Result of a random question sample operation."""

    questions: list[Question]
    tricky_count_requested: int
    tricky_count_actual: int
    tricky_ratio_actual: float


class QuestionRepo:
    """Data access layer for Question operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def random_sample(
        self,
        theme_ids: list[int] | None,
        count: int,
        tricky_ratio: float,
        seed: int | None = None,
    ) -> QuestionSample:
        """
        Deterministically select `count` questions filtered by theme_ids,
        targeting `tricky_ratio` tricky questions.

        Falls back gracefully when the pool lacks enough tricky questions:
        fills remaining slots with non-tricky questions.

        Args:
            theme_ids: Filter to these themes. None = all themes.
            count: Total number of questions to select.
            tricky_ratio: Target ratio of tricky questions (0.0–1.0).
            seed: RNG seed for deterministic selection.

        Returns:
            QuestionSample with selected questions and actual tricky ratio.
        """
        rng = random.Random(seed)

        # Build base query filtered by themes
        stmt = select(Question)
        if theme_ids:
            stmt = stmt.where(Question.theme_id.in_(theme_ids))

        result = await self.session.execute(stmt)
        all_questions = list(result.scalars().all())

        # Split into tricky / non-tricky pools
        tricky_pool = [q for q in all_questions if q.tricky]
        non_tricky_pool = [q for q in all_questions if not q.tricky]

        # Calculate target counts
        tricky_target = int(count * tricky_ratio)

        # Step 1: Take as many tricky as we can (up to target)
        tricky_actual = min(tricky_target, len(tricky_pool))

        # Step 2: Fill remaining from non-tricky
        remaining = count - tricky_actual
        non_tricky_actual = min(remaining, len(non_tricky_pool))

        # Step 3: If still short, take more from tricky pool (fallback)
        still_short = count - (tricky_actual + non_tricky_actual)
        if still_short > 0:
            extra_tricky = min(still_short, len(tricky_pool) - tricky_actual)
            tricky_actual += extra_tricky

        # Deterministic sampling
        selected_tricky = rng.sample(tricky_pool, tricky_actual) if tricky_actual > 0 else []
        selected_non_tricky = rng.sample(non_tricky_pool, non_tricky_actual) if non_tricky_actual > 0 else []

        selected = selected_tricky + selected_non_tricky
        tricky_ratio_actual = tricky_actual / count if count > 0 else 0.0

        return QuestionSample(
            questions=selected,
            tricky_count_requested=tricky_target,
            tricky_count_actual=tricky_actual,
            tricky_ratio_actual=round(tricky_ratio_actual, 4),
        )

    async def get_by_id(self, question_id: int) -> Question | None:
        """Fetch a single question by ID."""
        stmt = select(Question).where(Question.id == question_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, question_ids: list[int]) -> list[Question]:
        """Fetch multiple questions by IDs."""
        stmt = select(Question).where(Question.id.in_(question_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
