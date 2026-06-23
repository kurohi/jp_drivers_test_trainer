"""Tests for StudyPlanService and study plan endpoints."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models.attempt import Attempt, AttemptAnswer
from models.question import Question
from models.theme import Theme
from src.llm.exceptions import OllamaUnavailableError
from src.services.study_plan_service import (
    ALL_22_THEME_IDS,
    StudyPlanService,
)


@pytest.fixture
async def async_session():
    """Create a real async session with file-based SQLite for testing."""
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        db_path = tmp.name

    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(db_url, echo=False)

    from db import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()
    os.unlink(db_path)


async def _seed_theme(session: AsyncSession, theme_id: int = 1, name_en: str = "Theme 1"):
    theme = Theme(
        id=theme_id,
        slug=f"theme-{theme_id}",
        name_en=name_en,
        name_pt=f"Tema {theme_id}",
    )
    session.add(theme)
    await session.commit()


async def _seed_questions(session: AsyncSession, count: int, theme_id: int = 1):
    questions = []
    for i in range(count):
        questions.append(
            Question(
                theme_id=theme_id,
                prompt_en=f"Question {i}",
                prompt_pt=f"Pergunta {i}",
                answer_en="true" if i % 2 == 0 else "false",
                answer_pt="true" if i % 2 == 0 else "false",
                explanation_en=f"Explanation {i}",
                explanation_pt=f"Explicação {i}",
                tricky=False,
            )
        )
    session.add_all(questions)
    await session.commit()
    return questions


async def _seed_attempt_with_answers(
    session: AsyncSession,
    questions: list[Question],
    correct_indices: set[int],
    started_at: datetime | None = None,
):
    """Seed a finished attempt with answers."""
    started = started_at or datetime.now(UTC)
    attempt = Attempt(
        language="en",
        difficulty_tricky=0.0,
        time_limit_seconds=1800,
        started_at=started,
        finished_at=started + timedelta(minutes=30),
        score=len(correct_indices),
        max_score=len(questions),
        passed=len(correct_indices) >= 45,
    )
    session.add(attempt)
    await session.flush()

    answers = []
    for i, q in enumerate(questions):
        is_correct = i in correct_indices
        answers.append(
            AttemptAnswer(
                attempt_id=attempt.id,
                question_id=q.id,
                user_answer="true" if is_correct else "false",
                is_correct=is_correct,
                time_spent_ms=5000,
            )
        )
    session.add_all(answers)
    await session.commit()
    return attempt


# ---- TESTS ----


@pytest.mark.asyncio
async def test_empty_history_returns_default_plan(async_session: AsyncSession):
    """With no attempts in history, generate_study_plan returns default 14-day beginner plan."""
    service = StudyPlanService(async_session)
    plan = await service.generate_study_plan(available_days=7, hours_per_day=1.5)

    assert plan.source == "default-beginner"
    assert len(plan.days) == 14
    assert plan.id > 0
    assert plan.created_at != ""


@pytest.mark.asyncio
async def test_default_plan_covers_all_22_themes(async_session: AsyncSession):
    """Default beginner plan distributes all 22 themes across 14 days."""
    service = StudyPlanService(async_session)
    plan = service.build_default_beginner_plan(available_days=14)

    all_themes_in_plan = set()
    for day in plan.days:
        for tid in day.theme_ids:
            all_themes_in_plan.add(tid)

    assert all_themes_in_plan == set(ALL_22_THEME_IDS)
    assert len(plan.days) == 14
    assert plan.source == "default-beginner"


@pytest.mark.asyncio
async def test_mocked_llm_returns_adaptive_plan(async_session: AsyncSession):
    """With history and a working LLM, generate_study_plan returns an LLM-generated plan."""
    await _seed_theme(async_session, theme_id=1, name_en="Traffic Signals")
    questions = await _seed_questions(async_session, count=10, theme_id=1)
    # Seed an attempt with 3 wrong out of 10 (theme 1 is weak)
    await _seed_attempt_with_answers(
        async_session, questions, correct_indices={0, 1, 2, 3, 4, 5, 6}
    )

    service = StudyPlanService(async_session)

    # Mock OllamaClient to return valid JSON
    mock_ollama = AsyncMock()
    mock_ollama.chat.return_value = json.dumps({
        "days": [
            {
                "date": "2026-06-23",
                "theme_ids": [1],
                "question_count": 20,
                "focus_note_en": "Focus on traffic signals",
                "focus_note_pt": "Foque em sinais de trânsito",
            },
            {
                "date": "2026-06-24",
                "theme_ids": [1],
                "question_count": 20,
                "focus_note_en": "Review traffic signals again",
                "focus_note_pt": "Revise sinais de trânsito novamente",
            },
        ]
    })

    plan = await service.generate_study_plan(
        available_days=2, hours_per_day=1.5, ollama_client=mock_ollama
    )

    assert plan.source == "llm-generated"
    assert len(plan.days) == 2
    assert plan.days[0].theme_ids == [1]


@pytest.mark.asyncio
async def test_llm_parse_failure_falls_back_to_default(async_session: AsyncSession):
    """When LLM returns unparseable JSON, falls back to default beginner plan."""
    await _seed_theme(async_session, theme_id=1, name_en="Traffic Signals")
    questions = await _seed_questions(async_session, count=10, theme_id=1)
    await _seed_attempt_with_answers(
        async_session, questions, correct_indices={0, 1, 2, 3, 4, 5, 6}
    )

    service = StudyPlanService(async_session)

    # Mock OllamaClient to return invalid JSON
    mock_ollama = AsyncMock()
    mock_ollama.chat.return_value = "This is not valid JSON at all {{{"

    plan = await service.generate_study_plan(
        available_days=7, hours_per_day=1.5, ollama_client=mock_ollama
    )

    assert plan.source == "default-beginner"
    assert len(plan.days) == 14


@pytest.mark.asyncio
async def test_ollama_down_falls_back_to_default_and_logs(async_session: AsyncSession):
    """When Ollama is unavailable, falls back to default plan and logs 'ollama_unavailable'."""
    await _seed_theme(async_session, theme_id=1, name_en="Traffic Signals")
    questions = await _seed_questions(async_session, count=10, theme_id=1)
    await _seed_attempt_with_answers(
        async_session, questions, correct_indices={0, 1, 2, 3, 4, 5, 6}
    )

    service = StudyPlanService(async_session)

    # Mock OllamaClient to raise OllamaUnavailableError
    mock_ollama = AsyncMock()
    mock_ollama.chat.side_effect = OllamaUnavailableError("Connection refused")

    with patch("src.services.study_plan_service.logger") as mock_logger:
        plan = await service.generate_study_plan(
            available_days=7, hours_per_day=1.5, ollama_client=mock_ollama
        )

        assert plan.source == "default-beginner"
        assert len(plan.days) == 14

        # Verify logging occurred
        assert any("ollama_unavailable" in str(c) for c in mock_logger.warning.call_args_list)


@pytest.mark.asyncio
async def test_weak_theme_stats_empty_with_no_history(async_session: AsyncSession):
    """weak_theme_stats returns empty list when no attempts exist."""
    service = StudyPlanService(async_session)
    stats = await service.weak_theme_stats()
    assert stats == []


@pytest.mark.asyncio
async def test_weak_theme_stats_computes_correctly(async_session: AsyncSession):
    """weak_theme_stats correctly computes per-theme wrong counts."""
    await _seed_theme(async_session, theme_id=1, name_en="Traffic Signals")
    await _seed_theme(async_session, theme_id=2, name_en="Right of Way")

    q1 = await _seed_questions(async_session, count=5, theme_id=1)
    q2 = await _seed_questions(async_session, count=5, theme_id=2)

    # Attempt 1: theme 1 has 2 wrong (indices 3,4), theme 2 has 1 wrong (index 9)
    await _seed_attempt_with_answers(
        async_session, q1 + q2, correct_indices={0, 1, 2, 5, 6, 7, 8}
    )

    service = StudyPlanService(async_session)
    stats = await service.weak_theme_stats()

    # Theme 1: 2 wrong out of 5, Theme 2: 1 wrong out of 5
    assert len(stats) == 2
    assert stats[0].theme_id == 1
    assert stats[0].wrong_count == 2
    assert stats[1].theme_id == 2
    assert stats[1].wrong_count == 1


@pytest.mark.asyncio
async def test_llm_hallucinated_theme_ids_falls_back(async_session: AsyncSession):
    """When LLM returns theme_ids outside weak themes, falls back to default."""
    await _seed_theme(async_session, theme_id=1, name_en="Traffic Signals")
    questions = await _seed_questions(async_session, count=10, theme_id=1)
    await _seed_attempt_with_answers(
        async_session, questions, correct_indices={0, 1, 2, 3, 4, 5, 6}
    )

    service = StudyPlanService(async_session)

    # Mock LLM returning theme_id=99 which is not in weak themes (only theme 1)
    mock_ollama = AsyncMock()
    mock_ollama.chat.return_value = json.dumps({
        "days": [
            {
                "date": "2026-06-23",
                "theme_ids": [99],
                "question_count": 20,
                "focus_note_en": "Focus on theme 99",
                "focus_note_pt": "Foque no tema 99",
            }
        ]
    })

    plan = await service.generate_study_plan(
        available_days=1, hours_per_day=1.5, ollama_client=mock_ollama
    )

    assert plan.source == "default-beginner"
