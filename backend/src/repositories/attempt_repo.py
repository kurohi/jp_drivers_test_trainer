"""Attempt repository — data access for Attempt and AttemptAnswer ORM models."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.attempt import Attempt, AttemptAnswer


class AttemptRepo:
    """Data access layer for Attempt operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_attempt(
        self,
        language: str,
        tricky_ratio: float,
        time_limit_seconds: int,
    ) -> Attempt:
        """Create a new attempt record."""
        attempt = Attempt(
            language=language,
            difficulty_tricky=tricky_ratio,
            time_limit_seconds=time_limit_seconds,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(attempt)
        await self.session.commit()
        await self.session.refresh(attempt)
        return attempt

    async def create_attempt_answers(
        self,
        attempt_id: int,
        question_ids: list[int],
    ) -> list[AttemptAnswer]:
        """Create blank AttemptAnswer records for each question in the attempt."""
        answers = [
            AttemptAnswer(attempt_id=attempt_id, question_id=qid)
            for qid in question_ids
        ]
        self.session.add_all(answers)
        await self.session.commit()
        for a in answers:
            await self.session.refresh(a)
        return answers

    async def get_attempt(self, attempt_id: int) -> Attempt | None:
        """Fetch an attempt by ID with its answers."""
        stmt = select(Attempt).where(Attempt.id == attempt_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_attempt_with_answers(self, attempt_id: int) -> Attempt | None:
        """Fetch an attempt with eager-loaded answers."""
        from sqlalchemy.orm import selectinload

        stmt = (
            select(Attempt)
            .options(selectinload(Attempt.answers))
            .where(Attempt.id == attempt_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_attempt_result(
        self,
        attempt_id: int,
        score: int,
        max_score: int,
        passed: bool,
        finished_at: datetime | None = None,
    ) -> Attempt:
        """Update attempt with scoring results."""
        attempt = await self.get_attempt(attempt_id)
        if attempt is None:
            raise ValueError(f"Attempt {attempt_id} not found")

        attempt.score = score
        attempt.max_score = max_score
        attempt.passed = passed
        attempt.finished_at = finished_at or datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(attempt)
        return attempt

    async def update_answer(
        self,
        attempt_id: int,
        question_id: int,
        user_answer: str,
        is_correct: bool,
        time_spent_ms: int = 0,
    ) -> AttemptAnswer:
        """Update a single attempt answer with the user's response."""
        stmt = (
            select(AttemptAnswer)
            .where(AttemptAnswer.attempt_id == attempt_id)
            .where(AttemptAnswer.question_id == question_id)
        )
        result = await self.session.execute(stmt)
        answer = result.scalar_one_or_none()
        if answer is None:
            raise ValueError(
                f"Answer for attempt={attempt_id}, question={question_id} not found"
            )

        answer.user_answer = user_answer
        answer.is_correct = is_correct
        answer.time_spent_ms = time_spent_ms

        await self.session.commit()
        await self.session.refresh(answer)
        return answer
