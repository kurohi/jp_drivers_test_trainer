"""Tests for MockTestService — question selection, scoring, and time enforcement."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from models.attempt import Attempt, AttemptAnswer
from models.question import Question
from models.theme import Theme
from repositories.attempt_repo import AttemptRepo
from repositories.question_repo import QuestionRepo
from schemas.attempt import AnswerItem
from services.mock_test_service import (
    MAX_TIME_LIMIT_SECONDS,
    MAX_QUESTION_COUNT,
    MIN_QUESTION_COUNT,
    MockTestService,
    PASSING_SCORE,
)


@pytest.fixture
async def db_session():
    """Create an in-memory SQLite database with schema for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    class TestBase(DeclarativeBase):
        pass

    # Re-declare models with test base to avoid FK issues
    from sqlalchemy import BOOLEAN, DateTime, Float, ForeignKey, Integer, String, Text
    from sqlalchemy.orm import Mapped, mapped_column, relationship

    class TestTheme(TestBase):
        __tablename__ = "themes"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
        name_en: Mapped[str] = mapped_column(String(200), nullable=False)
        name_pt: Mapped[str] = mapped_column(String(200), nullable=False)
        parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
        sort_order: Mapped[int] = mapped_column(Integer, default=0)

    class TestQuestion(TestBase):
        __tablename__ = "questions"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        theme_id: Mapped[int] = mapped_column(Integer, ForeignKey("themes.id"), nullable=False)
        prompt_en: Mapped[str] = mapped_column(Text, nullable=False)
        prompt_pt: Mapped[str] = mapped_column(Text, nullable=False)
        answer_en: Mapped[str] = mapped_column(Text, nullable=False)
        answer_pt: Mapped[str] = mapped_column(Text, nullable=False)
        explanation_en: Mapped[str] = mapped_column(Text, nullable=False)
        explanation_pt: Mapped[str] = mapped_column(Text, nullable=False)
        tricky: Mapped[bool] = mapped_column(BOOLEAN, default=False)
        tricky_pattern: Mapped[str | None] = mapped_column(String(200), nullable=True)
        difficulty: Mapped[int] = mapped_column(Integer, default=3)
        translations_status: Mapped[str] = mapped_column(String(20), default="missing")
        source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
        license: Mapped[str | None] = mapped_column(String(100), nullable=True)
        attribution: Mapped[str | None] = mapped_column(String(200), nullable=True)
        created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
        updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class TestAttemptAnswer(TestBase):
        __tablename__ = "attempt_answers"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        attempt_id: Mapped[int] = mapped_column(Integer, ForeignKey("attempts.id"), nullable=False)
        question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id"), nullable=False)
        user_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
        is_correct: Mapped[bool] = mapped_column(BOOLEAN, default=False)
        time_spent_ms: Mapped[int] = mapped_column(Integer, default=0)

    class TestAttempt(TestBase):
        __tablename__ = "attempts"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
        finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
        score: Mapped[int] = mapped_column(Integer, default=0)
        max_score: Mapped[int] = mapped_column(Integer, default=0)
        passed: Mapped[bool] = mapped_column(BOOLEAN, default=False)
        language: Mapped[str] = mapped_column(String(5), default="en")
        difficulty_tricky: Mapped[float] = mapped_column(Float, default=0.0)
        time_limit_seconds: Mapped[int] = mapped_column(Integer, default=0)

    async with engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.drop_all)
    await engine.dispose()


async def seed_questions(session: AsyncSession, tricky_count: int, non_tricky_count: int, theme_id: int = 1):
    """Helper to seed questions with specified tricky/non-tricky counts."""
    questions = []
    for i in range(tricky_count):
        questions.append(
            TestQuestion(
                theme_id=theme_id,
                prompt_en=f"Tricky question {i}",
                prompt_pt=f"Pergunta tricky {i}",
                answer_en="true" if i % 2 == 0 else "false",
                answer_pt="true" if i % 2 == 0 else "false",
                explanation_en=f"Explanation for tricky {i}",
                explanation_pt=f"Explicação para tricky {i}",
                tricky=True,
                tricky_pattern="double_negative",
            )
        )
    for i in range(non_tricky_count):
        questions.append(
            TestQuestion(
                theme_id=theme_id,
                prompt_en=f"Normal question {i}",
                prompt_pt=f"Pergunta normal {i}",
                answer_en="true" if i % 2 == 0 else "false",
                answer_pt="true" if i % 2 == 0 else "false",
                explanation_en=f"Explanation for normal {i}",
                explanation_pt=f"Explicação para normal {i}",
                tricky=False,
            )
        )
    session.add_all(questions)
    await session.commit()
    return questions


async def seed_theme(session: AsyncSession, theme_id: int = 1):
    """Seed a theme for questions."""
    theme = TestTheme(
        id=theme_id,
        slug=f"theme-{theme_id}",
        name_en=f"Theme {theme_id}",
        name_pt=f"Tema {theme_id}",
    )
    session.add(theme)
    await session.commit()


# We need to use the test models, not the ORM models directly.
# Let's create a simpler approach using the actual models with a test DB.

# Actually, let's use a simpler approach: use the real models but with a test DB.
# The issue is that the models are already defined with `from db import Base`.
# Let's use a different approach: create a test-specific service that uses test models.

# Simplest approach: use the real models but override the Base for testing.
# Since the models reference `from db import Base`, we need to work around this.

# Let's use a pragmatic approach: create tables manually via raw SQL.


@pytest.fixture
async def test_db():
    """Create test database with tables using raw SQL."""
    import aiosqlite

    db_path = ":memory:"
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("""
            CREATE TABLE themes (
                id INTEGER PRIMARY KEY,
                slug TEXT UNIQUE NOT NULL,
                name_en TEXT NOT NULL,
                name_pt TEXT NOT NULL,
                parent_id INTEGER,
                sort_order INTEGER DEFAULT 0
            )
        """)
        await conn.execute("""
            CREATE TABLE questions (
                id INTEGER PRIMARY KEY,
                theme_id INTEGER NOT NULL REFERENCES themes(id),
                prompt_en TEXT NOT NULL,
                prompt_pt TEXT NOT NULL,
                answer_en TEXT NOT NULL,
                answer_pt TEXT NOT NULL,
                explanation_en TEXT NOT NULL,
                explanation_pt TEXT NOT NULL,
                tricky BOOLEAN DEFAULT 0,
                tricky_pattern TEXT,
                difficulty INTEGER DEFAULT 3,
                translations_status TEXT DEFAULT 'missing',
                source_url TEXT,
                license TEXT,
                attribution TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE attempts (
                id INTEGER PRIMARY KEY,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP,
                score INTEGER DEFAULT 0,
                max_score INTEGER DEFAULT 0,
                passed BOOLEAN DEFAULT 0,
                language TEXT DEFAULT 'en',
                difficulty_tricky REAL DEFAULT 0.0,
                time_limit_seconds INTEGER DEFAULT 0
            )
        """)
        await conn.execute("""
            CREATE TABLE attempt_answers (
                id INTEGER PRIMARY KEY,
                attempt_id INTEGER NOT NULL REFERENCES attempts(id),
                question_id INTEGER NOT NULL REFERENCES questions(id),
                user_answer TEXT,
                is_correct BOOLEAN DEFAULT 0,
                time_spent_ms INTEGER DEFAULT 0
            )
        """)
        await conn.commit()
        yield conn


@pytest.fixture
async def session(test_db):
    """Create an async SQLAlchemy session over the test database."""
    from sqlalchemy import event
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # We need to use the same in-memory DB. SQLite in-memory DBs are per-connection.
    # Let's use a file-based approach instead for shared access.
    await engine.dispose()

    # Use aiosqlite directly for the test
    yield test_db


# Actually, let's take a completely different approach.
# Use the real SQLAlchemy models with a file-based test DB.


@pytest.fixture
async def async_session():
    """Create a real async session with file-based SQLite for testing."""
    import tempfile
    import os

    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    db_path = tmp.name
    tmp.close()

    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(db_url, echo=False)

    # Import the real Base and create tables
    from db import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()
    os.unlink(db_path)


async def _seed_theme(session: AsyncSession, theme_id: int = 1):
    theme = Theme(
        id=theme_id,
        slug=f"theme-{theme_id}",
        name_en=f"Theme {theme_id}",
        name_pt=f"Tema {theme_id}",
    )
    session.add(theme)
    await session.commit()


async def _seed_questions(session: AsyncSession, tricky_count: int, non_tricky_count: int, theme_id: int = 1):
    questions = []
    for i in range(tricky_count):
        questions.append(
            Question(
                theme_id=theme_id,
                prompt_en=f"Tricky question {i}",
                prompt_pt=f"Pergunta tricky {i}",
                answer_en="true" if i % 2 == 0 else "false",
                answer_pt="true" if i % 2 == 0 else "false",
                explanation_en=f"Explanation for tricky {i}",
                explanation_pt=f"Explicação para tricky {i}",
                tricky=True,
                tricky_pattern="double_negative",
            )
        )
    for i in range(non_tricky_count):
        questions.append(
            Question(
                theme_id=theme_id,
                prompt_en=f"Normal question {i}",
                prompt_pt=f"Pergunta normal {i}",
                answer_en="true" if i % 2 == 0 else "false",
                answer_pt="true" if i % 2 == 0 else "false",
                explanation_en=f"Explanation for normal {i}",
                explanation_pt=f"Explicação para normal {i}",
                tricky=False,
            )
        )
    session.add_all(questions)
    await session.commit()
    return questions


# ---- TESTS ----


@pytest.mark.asyncio
async def test_deterministic_selection_seed_42(async_session: AsyncSession):
    """Same seed=42 always produces the same question selection."""
    await _seed_theme(async_session, theme_id=1)
    await _seed_questions(async_session, tricky_count=30, non_tricky_count=70, theme_id=1)

    service = MockTestService(async_session)

    result1 = await service.select_questions(
        theme_ids=[1], question_count=10, tricky_ratio=0.5, language="en", seed=42
    )
    ids1 = [q["id"] for q in result1.questions]

    # Create a second selection with same seed
    result2 = await service.select_questions(
        theme_ids=[1], question_count=10, tricky_ratio=0.5, language="en", seed=42
    )
    ids2 = [q["id"] for q in result2.questions]

    assert ids1 == ids2, "Same seed must produce identical question selection"
    assert len(ids1) == 10
    assert result1.tricky_ratio_actual == 0.5


@pytest.mark.asyncio
async def test_tricky_ratio_fallback_when_pool_insufficient(async_session: AsyncSession):
    """When tricky_ratio=1.0 but pool only has 5 tricky out of 105 total,
    tricky_ratio_actual should be 5/50 = 0.1 (for 50 questions)."""
    await _seed_theme(async_session, theme_id=1)
    await _seed_questions(async_session, tricky_count=5, non_tricky_count=100, theme_id=1)

    service = MockTestService(async_session)

    result = await service.select_questions(
        theme_ids=[1], question_count=50, tricky_ratio=1.0, language="en", seed=1
    )

    assert len(result.questions) == 50, "Must return exactly 50 questions"
    # Only 5 tricky available, so tricky_ratio_actual = 5/50 = 0.1
    assert result.tricky_ratio_actual == 0.1, f"Expected 0.1, got {result.tricky_ratio_actual}"


@pytest.mark.asyncio
async def test_scoring_44_out_of_50_fails(async_session: AsyncSession):
    """Score of 44/50 must result in passed=False."""
    await _seed_theme(async_session, theme_id=1)
    await _seed_questions(async_session, tricky_count=25, non_tricky_count=25, theme_id=1)

    service = MockTestService(async_session)
    selection = await service.select_questions(
        theme_ids=[1], question_count=50, tricky_ratio=0.5, language="en", seed=1
    )

    # Submit 44 correct answers, 6 wrong
    user_answers = []
    for i, q in enumerate(selection.questions):
        # Get the correct answer from the DB
        from sqlalchemy import select
        stmt = select(Question).where(Question.id == q["id"])
        result = await async_session.execute(stmt)
        question = result.scalar_one()
        correct = question.answer_en

        if i < 44:
            user_answers.append(AnswerItem(question_id=q["id"], user_answer=correct))
        else:
            wrong = "false" if correct == "true" else "true"
            user_answers.append(AnswerItem(question_id=q["id"], user_answer=wrong))

    scored = await service.score_attempt(selection.attempt_id, user_answers)

    assert scored.score == 44
    assert scored.max_score == 50
    assert scored.passed is False


@pytest.mark.asyncio
async def test_scoring_45_out_of_50_passes(async_session: AsyncSession):
    """Score of 45/50 must result in passed=True (boundary case)."""
    await _seed_theme(async_session, theme_id=1)
    await _seed_questions(async_session, tricky_count=25, non_tricky_count=25, theme_id=1)

    service = MockTestService(async_session)
    selection = await service.select_questions(
        theme_ids=[1], question_count=50, tricky_ratio=0.5, language="en", seed=2
    )

    user_answers = []
    for i, q in enumerate(selection.questions):
        from sqlalchemy import select
        stmt = select(Question).where(Question.id == q["id"])
        result = await async_session.execute(stmt)
        question = result.scalar_one()
        correct = question.answer_en

        if i < 45:
            user_answers.append(AnswerItem(question_id=q["id"], user_answer=correct))
        else:
            wrong = "false" if correct == "true" else "true"
            user_answers.append(AnswerItem(question_id=q["id"], user_answer=wrong))

    scored = await service.score_attempt(selection.attempt_id, user_answers)

    assert scored.score == 45
    assert scored.max_score == 50
    assert scored.passed is True
    assert scored.boundary_score == PASSING_SCORE


@pytest.mark.asyncio
async def test_timeout_marks_finished_with_current_score(async_session: AsyncSession):
    """When time limit is exceeded, enforce_time_limit auto-scores and marks finished."""
    await _seed_theme(async_session, theme_id=1)
    await _seed_questions(async_session, tricky_count=25, non_tricky_count=25, theme_id=1)

    service = MockTestService(async_session)
    selection = await service.select_questions(
        theme_ids=[1], question_count=50, tricky_ratio=0.5, language="en", seed=3,
        time_limit_seconds=60,
    )

    # Manually update some answers in DB (without scoring) to simulate partial progress
    from sqlalchemy import select
    for i, q in enumerate(selection.questions):
        stmt = select(Question).where(Question.id == q["id"])
        result = await async_session.execute(stmt)
        question = result.scalar_one()
        correct = question.answer_en

        if i < 30:
            await service.attempt_repo.update_answer(
                attempt_id=selection.attempt_id,
                question_id=q["id"],
                user_answer=correct,
                is_correct=True,
                time_spent_ms=5000,
            )

    # Backdate the attempt's started_at to simulate timeout
    stmt = select(Attempt).where(Attempt.id == selection.attempt_id)
    result = await async_session.execute(stmt)
    attempt = result.scalar_one()
    attempt.started_at = datetime.now(timezone.utc) - timedelta(seconds=120)
    await async_session.commit()
    async_session.expire_all()

    # Enforce time limit — should auto-score with the 30 answers already in DB
    timeout_result = await service.enforce_time_limit(selection.attempt_id)

    assert timeout_result is not None, "Should return result when timed out"
    assert timeout_result.score == 30

    # Verify attempt is marked finished
    stmt = select(Attempt).where(Attempt.id == selection.attempt_id)
    result = await async_session.execute(stmt)
    attempt = result.scalar_one()
    assert attempt.finished_at is not None, "Attempt should be marked as finished"


# ---- Validation tests ----


@pytest.mark.asyncio
async def test_validate_question_count_too_low(async_session: AsyncSession):
    """question_count < 5 raises ValueError."""
    service = MockTestService(async_session)
    with pytest.raises(ValueError, match="between 5 and 50"):
        await service.select_questions(theme_ids=None, question_count=4)


@pytest.mark.asyncio
async def test_validate_question_count_too_high(async_session: AsyncSession):
    """question_count > 50 raises ValueError."""
    service = MockTestService(async_session)
    with pytest.raises(ValueError, match="between 5 and 50"):
        await service.select_questions(theme_ids=None, question_count=51)


@pytest.mark.asyncio
async def test_validate_time_limit_exceeded(async_session: AsyncSession):
    """time_limit_seconds > 1800 raises ValueError."""
    service = MockTestService(async_session)
    with pytest.raises(ValueError, match="<= 1800"):
        await service.select_questions(theme_ids=None, time_limit_seconds=1801)


@pytest.mark.asyncio
async def test_validate_tricky_ratio_invalid(async_session: AsyncSession):
    """tricky_ratio not in {0.0, 0.25, 0.5, 0.75, 1.0} raises ValueError."""
    service = MockTestService(async_session)
    with pytest.raises(ValueError, match="must be one of"):
        await service.select_questions(theme_ids=None, tricky_ratio=0.33)
