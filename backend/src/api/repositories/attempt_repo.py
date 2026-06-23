"""Attempt repository — create, retrieve, add answers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.attempt import Attempt, AttemptAnswer


class AttemptRepo:
    """CRUD queries for Attempt and AttemptAnswer entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        language: str = "en",
        difficulty_tricky: float = 0.0,
        time_limit_seconds: int = 0,
    ) -> Attempt:
        """Create a new Attempt and return it."""
        attempt = Attempt(
            language=language,
            difficulty_tricky=difficulty_tricky,
            time_limit_seconds=time_limit_seconds,
        )
        self._session.add(attempt)
        await self._session.flush()
        await self._session.refresh(attempt)
        return attempt

    async def get(self, attempt_id: int) -> Optional[Attempt]:
        """Return a single Attempt by ID, or None."""
        stmt = select(Attempt).where(Attempt.id == attempt_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list(self, limit: int = 20, offset: int = 0) -> list[Attempt]:
        """List attempts ordered by most recent first."""
        stmt = (
            select(Attempt)
            .order_by(Attempt.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_answer(
        self,
        attempt_id: int,
        question_id: int,
        user_answer: Optional[str] = None,
        is_correct: bool = False,
        time_spent_ms: int = 0,
    ) -> AttemptAnswer:
        """Add an AttemptAnswer to an existing Attempt."""
        answer = AttemptAnswer(
            attempt_id=attempt_id,
            question_id=question_id,
            user_answer=user_answer,
            is_correct=is_correct,
            time_spent_ms=time_spent_ms,
        )
        self._session.add(answer)
        await self._session.flush()
        await self._session.refresh(answer)
        return answer

    async def get_with_answers(self, attempt_id: int) -> Optional[Attempt]:
        """Return an Attempt with its answers loaded.

        Since Attempt.answers uses lazy='noload', we query answers separately
        and attach them to the attempt instance.
        """
        stmt = select(Attempt).where(Attempt.id == attempt_id)
        result = await self._session.execute(stmt)
        attempt = result.scalars().first()
        if attempt is None:
            return None

        answers_stmt = select(AttemptAnswer).where(
            AttemptAnswer.attempt_id == attempt_id
        )
        answers_result = await self._session.execute(answers_stmt)
        attempt.answers = list(answers_result.scalars().all())
        return attempt

    async def list_recent_with_answers(
        self, days: int = 30
    ) -> list[Attempt]:
        """Return finished attempts from the past N days with answers loaded.

        Only includes attempts that have been scored (finished_at is set).
        Answers are attached to each attempt instance.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(Attempt)
            .where(Attempt.finished_at.isnot(None))
            .where(Attempt.started_at >= cutoff)
            .order_by(Attempt.started_at.desc())
        )
        result = await self._session.execute(stmt)
        attempts = list(result.scalars().all())

        # Load answers for each attempt
        for attempt in attempts:
            answers_stmt = select(AttemptAnswer).where(
                AttemptAnswer.attempt_id == attempt.id
            )
            answers_result = await self._session.execute(answers_stmt)
            attempt.answers = list(answers_result.scalars().all())

        return attempts
