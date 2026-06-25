"""Mock test service — question selection, scoring, and time enforcement."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.attempt import AttemptAnswer
from src.models.question import Question
from src.repositories.attempt_repo import AttemptRepo
from src.repositories.question_repo import QuestionRepo
from src.schemas.attempt import (
    AnswerItem,
    AttemptAnswerOut,
    AttemptResultOut,
    SelectionResult,
)

PASSING_SCORE = 45
DEFAULT_QUESTION_COUNT = 50
DEFAULT_TIME_LIMIT_SECONDS = 1800
VALID_TRICKY_RATIOS = {0.0, 0.25, 0.5, 0.75, 1.0}
MIN_QUESTION_COUNT = 5
MAX_QUESTION_COUNT = 50
MAX_TIME_LIMIT_SECONDS = 1800


class MockTestService:
    """Business logic for mock test attempts."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.question_repo = QuestionRepo(session)
        self.attempt_repo = AttemptRepo(session)

    async def select_questions(
        self,
        theme_ids: list[int] | None,
        question_count: int = DEFAULT_QUESTION_COUNT,
        tricky_ratio: float = 0.5,
        language: str = "en",
        seed: int | None = None,
        time_limit_seconds: int = DEFAULT_TIME_LIMIT_SECONDS,
    ) -> SelectionResult:
        """
        Select questions for a new mock test attempt.

        Validates inputs, calls QuestionRepo.random_sample, creates the
        Attempt record with blank AttemptAnswer rows, and returns the
        selection result.

        Raises ValueError on invalid question_count or time_limit_seconds.
        """
        self._validate_question_count(question_count)
        self._validate_time_limit(time_limit_seconds)
        self._validate_tricky_ratio(tricky_ratio)

        sample = await self.question_repo.random_sample(
            theme_ids=theme_ids,
            count=question_count,
            tricky_ratio=tricky_ratio,
            seed=seed,
        )

        attempt = await self.attempt_repo.create_attempt(
            language=language,
            tricky_ratio=tricky_ratio,
            time_limit_seconds=time_limit_seconds,
        )

        question_ids = [q.id for q in sample.questions]
        await self.attempt_repo.create_attempt_answers(
            attempt_id=attempt.id,
            question_ids=question_ids,
        )

        questions_data = [
            {
                "id": q.id,
                "theme_id": q.theme_id,
                "prompt_en": q.prompt_en,
                "prompt_pt": q.prompt_pt,
                "image_url": q.image_url,
                "tricky": q.tricky,
                "tricky_pattern": q.tricky_pattern,
                "difficulty": q.difficulty,
            }
            for q in sample.questions
        ]

        return SelectionResult(
            attempt_id=attempt.id,
            questions=questions_data,
            tricky_ratio_actual=sample.tricky_ratio_actual,
            question_count=len(sample.questions),
        )

    async def score_attempt(
        self,
        attempt_id: int,
        user_answers: list[AnswerItem],
    ) -> AttemptResultOut:
        """
        Score a completed attempt by comparing user answers to stored correct answers.

        Computes score/max_score, determines pass/fail at 45/50 boundary,
        persists results, and returns the full attempt result.
        """
        attempt = await self.attempt_repo.get_attempt_with_answers(attempt_id)
        if attempt is None:
            raise ValueError(f"Attempt {attempt_id} not found")

        if attempt.finished_at is not None:
            raise ValueError(f"Attempt {attempt_id} already finished")

        # Build lookup: question_id -> AttemptAnswer ORM record
        answer_lookup: dict[int, AttemptAnswer] = {
            aa.question_id: aa for aa in attempt.answers
        }

        # Fetch all questions for this attempt to get correct answers
        question_ids = [aa.question_id for aa in attempt.answers]
        questions = await self.question_repo.get_by_ids(question_ids)
        question_lookup: dict[int, Question] = {q.id: q for q in questions}

        correct_count = 0
        scored_answers: list[AttemptAnswerOut] = []

        for ua in user_answers:
            aa = answer_lookup.get(ua.question_id)
            if aa is None:
                continue

            question = question_lookup.get(ua.question_id)
            if question is None:
                continue

            correct_answer = getattr(question, f"answer_{attempt.language}", "false")
            is_correct = ua.user_answer.lower() == correct_answer.lower()

            if is_correct:
                correct_count += 1

            await self.attempt_repo.update_answer(
                attempt_id=attempt_id,
                question_id=ua.question_id,
                user_answer=ua.user_answer,
                is_correct=is_correct,
                time_spent_ms=ua.time_spent_ms or 0,
            )

            scored_answers.append(
                AttemptAnswerOut(
                    question_id=ua.question_id,
                    is_correct=is_correct,
                    user_answer=ua.user_answer,
                    correct_answer=correct_answer,
                    prompt_en=question.prompt_en,
                    prompt_pt=question.prompt_pt,
                    image_url=question.image_url,
                    explanation_en=question.explanation_en,
                    explanation_pt=question.explanation_pt,
                )
            )

        max_score = len(attempt.answers)
        passed = correct_count >= PASSING_SCORE

        await self.attempt_repo.update_attempt_result(
            attempt_id=attempt_id,
            score=correct_count,
            max_score=max_score,
            passed=passed,
        )

        # Recompute tricky_ratio_actual from selected questions
        tricky_count = sum(1 for q in questions if q.tricky)
        tricky_ratio_actual = tricky_count / max_score if max_score > 0 else 0.0

        return AttemptResultOut(
            attempt_id=attempt_id,
            score=correct_count,
            max_score=max_score,
            passed=passed,
            tricky_ratio_actual=round(tricky_ratio_actual, 4),
            boundary_score=PASSING_SCORE,
            answers=scored_answers,
        )

    def time_remaining(self, attempt: Attempt) -> int:
        if attempt.finished_at is not None:
            return 0

        deadline = attempt.started_at + timedelta(seconds=attempt.time_limit_seconds)
        now = datetime.now(timezone.utc)
        if deadline.tzinfo is None:
            now = now.replace(tzinfo=None)
        remaining = (deadline - now).total_seconds()
        return max(0, int(remaining))

    async def enforce_time_limit(self, attempt_id: int) -> AttemptResultOut | None:
        """
        Check if an attempt has exceeded its time limit.

        If expired and not yet submitted, auto-scores with current answers
        and marks the attempt as finished (timeout-disqualified).

        Returns AttemptResultOut if timed out, None if still within limit.
        """
        attempt = await self.attempt_repo.get_attempt_with_answers(attempt_id)
        if attempt is None:
            raise ValueError(f"Attempt {attempt_id} not found")

        if attempt.finished_at is not None:
            return None

        remaining = self.time_remaining(attempt)
        if remaining > 0:
            return None

        # Time expired — auto-score with whatever answers exist
        submitted_answers: list[AnswerItem] = []
        for aa in attempt.answers:
            if aa.user_answer is not None:
                submitted_answers.append(
                    AnswerItem(
                        question_id=aa.question_id,
                        user_answer=aa.user_answer,
                        time_spent_ms=aa.time_spent_ms,
                    )
                )

        result = await self.score_attempt(attempt_id, submitted_answers)
        return result

    @staticmethod
    def _validate_question_count(count: int) -> None:
        if count < MIN_QUESTION_COUNT or count > MAX_QUESTION_COUNT:
            raise ValueError(
                f"question_count must be between {MIN_QUESTION_COUNT} and {MAX_QUESTION_COUNT}, got {count}"
            )

    @staticmethod
    def _validate_time_limit(seconds: int) -> None:
        if seconds > MAX_TIME_LIMIT_SECONDS:
            raise ValueError(
                f"time_limit_seconds must be <= {MAX_TIME_LIMIT_SECONDS}, got {seconds}"
            )

    @staticmethod
    def _validate_tricky_ratio(ratio: float) -> None:
        if ratio not in VALID_TRICKY_RATIOS:
            raise ValueError(
                f"tricky_ratio must be one of {sorted(VALID_TRICKY_RATIOS)}, got {ratio}"
            )
