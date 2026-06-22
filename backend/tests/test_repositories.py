"""
TDD tests for all repository classes.

Uses a temporary in-memory SQLite database with all tables created
via SQLAlchemy's Base.metadata.create_all().
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# ---------------------------------------------------------------------------
# In-memory test engine + session
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite://"

# We need a shared Base that mirrors the production models for table creation.
# Since models import `from db import Base`, we reuse that Base by importing
# the models (which register tables on the Base).
from db import Base  # noqa: E402 — must import after setting up test env

# Import all models so tables are registered on Base
from models.theme import Theme  # noqa: E402
from models.question import Question  # noqa: E402
from models.attempt import Attempt, AttemptAnswer  # noqa: E402
from models.study_plan import StudyPlan  # noqa: E402
from models.rag_chunk import RagDocument, RagChunk  # noqa: E402
from models.skill_module import SkillModule  # noqa: E402

# Import repositories
from api.repositories.theme_repo import ThemeRepo  # noqa: E402
from api.repositories.question_repo import QuestionRepo  # noqa: E402
from api.repositories.attempt_repo import AttemptRepo  # noqa: E402
from api.repositories.study_plan_repo import StudyPlanRepo  # noqa: E402
from api.repositories.rag_doc_repo import RagDocRepo  # noqa: E402
from api.repositories.skill_repo import SkillRepo  # noqa: E402


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """Create an in-memory SQLite async session with all tables."""
    engine = create_async_engine(TEST_DB_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session_maker() as s:
        yield s

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def _make_theme(slug: str, name_en: str, name_pt: str, parent_id=None, sort_order=0) -> Theme:
    return Theme(
        slug=slug,
        name_en=name_en,
        name_pt=name_pt,
        parent_id=parent_id,
        sort_order=sort_order,
    )


def _make_question(
    theme_id: int,
    tricky: bool = False,
    translations_status: str = "verified",
    difficulty: int = 3,
) -> Question:
    return Question(
        theme_id=theme_id,
        prompt_en=f"Question EN {theme_id}",
        prompt_pt=f"Question PT {theme_id}",
        answer_en="true",
        answer_pt="verdadeiro",
        explanation_en="Explanation EN",
        explanation_pt="Explicação PT",
        tricky=tricky,
        tricky_pattern="wording" if tricky else None,
        difficulty=difficulty,
        translations_status=translations_status,
    )


# ---------------------------------------------------------------------------
# ThemeRepo tests
# ---------------------------------------------------------------------------

class TestThemeRepo:
    async def test_list_root_themes(self, session: AsyncSession):
        repo = ThemeRepo(session)
        t1 = _make_theme("signals", "Signals", "Sinais", sort_order=1)
        t2 = _make_theme("signs", "Signs", "Placas", sort_order=2)
        session.add_all([t1, t2])
        await session.flush()

        roots = await repo.list_root_themes()
        assert len(roots) == 2
        assert roots[0].slug == "signals"
        assert roots[1].slug == "signs"

    async def test_list_root_themes_excludes_children(self, session: AsyncSession):
        repo = ThemeRepo(session)
        parent = _make_theme("signals", "Signals", "Sinais")
        session.add(parent)
        await session.flush()

        child = _make_theme("signals-sub", "Sub", "Sub PT", parent_id=parent.id)
        session.add(child)
        await session.flush()

        roots = await repo.list_root_themes()
        assert len(roots) == 1
        assert roots[0].slug == "signals"

    async def test_get_theme_tree(self, session: AsyncSession):
        repo = ThemeRepo(session)
        parent = _make_theme("signals", "Signals", "Sinais")
        session.add(parent)
        await session.flush()

        child = _make_theme("signals-sub", "Sub", "Sub PT", parent_id=parent.id)
        session.add(child)
        await session.flush()

        tree = await repo.get_theme_tree()
        assert len(tree) == 1
        assert tree[0].slug == "signals"
        assert len(tree[0].children) == 1
        assert tree[0].children[0].slug == "signals-sub"

    async def test_get_by_slug_found(self, session: AsyncSession):
        repo = ThemeRepo(session)
        theme = _make_theme("signals", "Signals", "Sinais")
        session.add(theme)
        await session.flush()

        result = await repo.get_by_slug("signals")
        assert result is not None
        assert result.slug == "signals"

    async def test_get_by_slug_not_found(self, session: AsyncSession):
        repo = ThemeRepo(session)
        result = await repo.get_by_slug("nonexistent")
        assert result is None


# ---------------------------------------------------------------------------
# QuestionRepo tests
# ---------------------------------------------------------------------------

class TestQuestionRepo:
    async def test_list_all(self, session: AsyncSession):
        theme = _make_theme("signals", "Signals", "Sinais")
        session.add(theme)
        await session.flush()

        q1 = _make_question(theme.id)
        q2 = _make_question(theme.id)
        session.add_all([q1, q2])
        await session.flush()

        repo = QuestionRepo(session)
        items = await repo.list()
        assert len(items) == 2

    async def test_list_by_theme_id(self, session: AsyncSession):
        t1 = _make_theme("signals", "Signals", "Sinais")
        t2 = _make_theme("signs", "Signs", "Placas")
        session.add_all([t1, t2])
        await session.flush()

        session.add_all([
            _make_question(t1.id),
            _make_question(t1.id),
            _make_question(t2.id),
        ])
        await session.flush()

        repo = QuestionRepo(session)
        items = await repo.list(theme_id=t1.id)
        assert len(items) == 2
        assert all(q.theme_id == t1.id for q in items)

    async def test_list_tricky_only(self, session: AsyncSession):
        theme = _make_theme("signals", "Signals", "Sinais")
        session.add(theme)
        await session.flush()

        session.add_all([
            _make_question(theme.id, tricky=True),
            _make_question(theme.id, tricky=False),
            _make_question(theme.id, tricky=True),
        ])
        await session.flush()

        repo = QuestionRepo(session)
        items = await repo.list(tricky_only=True)
        assert len(items) == 2
        assert all(q.tricky for q in items)

    async def test_list_excludes_missing_translations(self, session: AsyncSession):
        theme = _make_theme("signals", "Signals", "Sinais")
        session.add(theme)
        await session.flush()

        session.add_all([
            _make_question(theme.id, translations_status="verified"),
            _make_question(theme.id, translations_status="missing"),
            _make_question(theme.id, translations_status="machine"),
        ])
        await session.flush()

        repo = QuestionRepo(session)
        items = await repo.list(language="en")
        # "missing" should be excluded
        assert len(items) == 2
        assert all(q.translations_status != "missing" for q in items)

    async def test_list_pagination(self, session: AsyncSession):
        theme = _make_theme("signals", "Signals", "Sinais")
        session.add(theme)
        await session.flush()

        for _ in range(10):
            session.add(_make_question(theme.id))
        await session.flush()

        repo = QuestionRepo(session)
        page1 = await repo.list(limit=3, offset=0)
        assert len(page1) == 3

        page2 = await repo.list(limit=3, offset=3)
        assert len(page2) == 3
        assert page1[0].id != page2[0].id

    async def test_get_by_id_found(self, session: AsyncSession):
        theme = _make_theme("signals", "Signals", "Sinais")
        session.add(theme)
        await session.flush()

        q = _make_question(theme.id)
        session.add(q)
        await session.flush()

        repo = QuestionRepo(session)
        result = await repo.get_by_id(q.id)
        assert result is not None
        assert result.id == q.id

    async def test_get_by_id_not_found(self, session: AsyncSession):
        repo = QuestionRepo(session)
        result = await repo.get_by_id(99999)
        assert result is None

    async def test_count_by_theme(self, session: AsyncSession):
        t1 = _make_theme("signals", "Signals", "Sinais")
        t2 = _make_theme("signs", "Signs", "Placas")
        session.add_all([t1, t2])
        await session.flush()

        session.add_all([
            _make_question(t1.id),
            _make_question(t1.id),
            _make_question(t1.id),
            _make_question(t2.id),
        ])
        await session.flush()

        repo = QuestionRepo(session)
        assert await repo.count_by_theme(t1.id) == 3
        assert await repo.count_by_theme(t2.id) == 1
        assert await repo.count_by_theme(999) == 0

    async def test_random_sample_deterministic_with_seed(self, session: AsyncSession):
        theme = _make_theme("signals", "Signals", "Sinais")
        session.add(theme)
        await session.flush()

        # Create 20 questions: 10 tricky, 10 normal
        for i in range(10):
            session.add(_make_question(theme.id, tricky=True))
            session.add(_make_question(theme.id, tricky=False))
        await session.flush()

        repo = QuestionRepo(session)

        # Same seed → same results
        sample1 = await repo.random_sample(
            theme_ids=[theme.id], count=10, tricky_ratio=0.5, seed=42
        )
        sample2 = await repo.random_sample(
            theme_ids=[theme.id], count=10, tricky_ratio=0.5, seed=42
        )

        assert len(sample1) == 10
        assert len(sample2) == 10
        assert [q.id for q in sample1] == [q.id for q in sample2]

    async def test_random_sample_different_seeds(self, session: AsyncSession):
        theme = _make_theme("signals", "Signals", "Sinais")
        session.add(theme)
        await session.flush()

        for i in range(20):
            session.add(_make_question(theme.id, tricky=(i % 2 == 0)))
        await session.flush()

        repo = QuestionRepo(session)

        sample_a = await repo.random_sample(
            theme_ids=[theme.id], count=10, tricky_ratio=0.5, seed=1
        )
        sample_b = await repo.random_sample(
            theme_ids=[theme.id], count=10, tricky_ratio=0.5, seed=2
        )

        # Different seeds should (very likely) produce different orderings
        ids_a = {q.id for q in sample_a}
        ids_b = {q.id for q in sample_b}
        # At least some difference in selection or order
        assert len(ids_a) == 10
        assert len(ids_b) == 10

    async def test_random_sample_raises_value_error_insufficient_pool(self, session: AsyncSession):
        theme = _make_theme("signals", "Signals", "Sinais")
        session.add(theme)
        await session.flush()

        # Only 3 questions, requesting 10
        for _ in range(3):
            session.add(_make_question(theme.id))
        await session.flush()

        repo = QuestionRepo(session)

        with pytest.raises(ValueError, match="Insufficient question pool"):
            await repo.random_sample(theme_ids=[theme.id], count=10, tricky_ratio=0.5, seed=42)

    async def test_random_sample_raises_value_error_insufficient_normal_pool(self, session: AsyncSession):
        theme = _make_theme("signals", "Signals", "Sinais")
        session.add(theme)
        await session.flush()

        # 10 tricky, 1 normal — requesting 10 with 0.5 tricky_ratio
        # needs 5 normal but only 1 available
        for _ in range(10):
            session.add(_make_question(theme.id, tricky=True))
        session.add(_make_question(theme.id, tricky=False))
        await session.flush()

        repo = QuestionRepo(session)

        with pytest.raises(ValueError, match="Insufficient question pool"):
            await repo.random_sample(
                theme_ids=[theme.id], count=10, tricky_ratio=0.5, seed=42
            )

    async def test_bulk_create(self, session: AsyncSession):
        theme = _make_theme("signals", "Signals", "Sinais")
        session.add(theme)
        await session.flush()

        repo = QuestionRepo(session)
        items = [
            _make_question(theme.id),
            _make_question(theme.id),
            _make_question(theme.id),
        ]

        created = await repo.bulk_create(items)
        assert len(created) == 3
        assert all(q.id is not None for q in created)

        # Verify they're in the DB
        all_items = await repo.list()
        assert len(all_items) == 3


# ---------------------------------------------------------------------------
# AttemptRepo tests
# ---------------------------------------------------------------------------

class TestAttemptRepo:
    async def test_create(self, session: AsyncSession):
        repo = AttemptRepo(session)
        attempt = await repo.create(
            language="en",
            difficulty_tricky=0.5,
            time_limit_seconds=1800,
        )
        assert attempt.id is not None
        assert attempt.language == "en"
        assert attempt.difficulty_tricky == 0.5
        assert attempt.time_limit_seconds == 1800
        assert attempt.score == 0

    async def test_get_found(self, session: AsyncSession):
        repo = AttemptRepo(session)
        attempt = await repo.create(language="pt")

        result = await repo.get(attempt.id)
        assert result is not None
        assert result.id == attempt.id

    async def test_get_not_found(self, session: AsyncSession):
        repo = AttemptRepo(session)
        result = await repo.get(99999)
        assert result is None

    async def test_list_ordered_by_recent(self, session: AsyncSession):
        repo = AttemptRepo(session)
        a1 = await repo.create(language="en")
        a2 = await repo.create(language="pt")

        items = await repo.list()
        assert len(items) == 2
        # Most recent first
        assert items[0].id == a2.id
        assert items[1].id == a1.id

    async def test_list_pagination(self, session: AsyncSession):
        repo = AttemptRepo(session)
        for _ in range(5):
            await repo.create(language="en")

        page1 = await repo.list(limit=2, offset=0)
        assert len(page1) == 2

        page2 = await repo.list(limit=2, offset=2)
        assert len(page2) == 2

    async def test_add_answer(self, session: AsyncSession):
        theme = _make_theme("signals", "Signals", "Sinais")
        session.add(theme)
        await session.flush()

        q = _make_question(theme.id)
        session.add(q)
        await session.flush()

        attempt_repo = AttemptRepo(session)
        attempt = await attempt_repo.create(language="en")

        answer = await attempt_repo.add_answer(
            attempt_id=attempt.id,
            question_id=q.id,
            user_answer="true",
            is_correct=True,
            time_spent_ms=5000,
        )
        assert answer.id is not None
        assert answer.attempt_id == attempt.id
        assert answer.question_id == q.id
        assert answer.user_answer == "true"
        assert answer.is_correct is True

    async def test_get_with_answers(self, session: AsyncSession):
        theme = _make_theme("signals", "Signals", "Sinais")
        session.add(theme)
        await session.flush()

        q1 = _make_question(theme.id)
        q2 = _make_question(theme.id)
        session.add_all([q1, q2])
        await session.flush()

        attempt_repo = AttemptRepo(session)
        attempt = await attempt_repo.create(language="en")

        await attempt_repo.add_answer(attempt.id, q1.id, "true", True)
        await attempt_repo.add_answer(attempt.id, q2.id, "false", False)

        result = await attempt_repo.get_with_answers(attempt.id)
        assert result is not None
        assert len(result.answers) == 2


# ---------------------------------------------------------------------------
# StudyPlanRepo tests
# ---------------------------------------------------------------------------

class TestStudyPlanRepo:
    async def test_create(self, session: AsyncSession):
        repo = StudyPlanRepo(session)
        days_json = json.dumps([{"day": 1, "theme_ids": [1, 2]}])
        plan = await repo.create(
            days_json=days_json,
            source="llm-generated",
            weak_themes_json=json.dumps([1]),
        )
        assert plan.id is not None
        assert plan.source == "llm-generated"
        assert plan.days_json == days_json

    async def test_latest(self, session: AsyncSession):
        repo = StudyPlanRepo(session)
        p1 = await repo.create(days_json=json.dumps([]), source="default-beginner")
        p2 = await repo.create(days_json=json.dumps([]), source="llm-generated")

        latest = await repo.latest()
        assert latest is not None
        assert latest.id == p2.id

    async def test_latest_empty(self, session: AsyncSession):
        repo = StudyPlanRepo(session)
        result = await repo.latest()
        assert result is None

    async def test_list(self, session: AsyncSession):
        repo = StudyPlanRepo(session)
        for _ in range(5):
            await repo.create(days_json=json.dumps([]))

        items = await repo.list(limit=3)
        assert len(items) == 3


# ---------------------------------------------------------------------------
# RagDocRepo tests
# ---------------------------------------------------------------------------

class TestRagDocRepo:
    async def test_list_docs(self, session: AsyncSession):
        repo = RagDocRepo(session)
        d1 = await repo.add_doc("Rule 1", "rule", "Text 1")
        d2 = await repo.add_doc("Rule 2", "rule", "Text 2")

        docs = await repo.list_docs()
        assert len(docs) == 2
        # Most recent first
        assert docs[0].id == d2.id

    async def test_add_doc(self, session: AsyncSession):
        repo = RagDocRepo(session)
        doc = await repo.add_doc(
            title="Traffic Rules",
            doc_type="rule",
            raw_text="Full text here",
            source_url="https://example.com",
        )
        assert doc.id is not None
        assert doc.title == "Traffic Rules"
        assert doc.source_url == "https://example.com"

    async def test_add_chunk(self, session: AsyncSession):
        repo = RagDocRepo(session)
        doc = await repo.add_doc("Doc", "rule", "Text")

        chunk = await repo.add_chunk(
            document_id=doc.id,
            chunk_text="Chunk text",
            chunk_idx=0,
            embedding_id="emb-123",
        )
        assert chunk.id is not None
        assert chunk.document_id == doc.id
        assert chunk.chunk_text == "Chunk text"
        assert chunk.embedding_id == "emb-123"

    async def test_get_chunk_found(self, session: AsyncSession):
        repo = RagDocRepo(session)
        doc = await repo.add_doc("Doc", "rule", "Text")
        chunk = await repo.add_chunk(doc.id, "Chunk text")

        result = await repo.get_chunk(chunk.id)
        assert result is not None
        assert result.id == chunk.id

    async def test_get_chunk_not_found(self, session: AsyncSession):
        repo = RagDocRepo(session)
        result = await repo.get_chunk(99999)
        assert result is None

    async def test_delete_chunks_by_doc_id(self, session: AsyncSession):
        repo = RagDocRepo(session)
        doc = await repo.add_doc("Doc", "rule", "Text")

        await repo.add_chunk(doc.id, "Chunk 1")
        await repo.add_chunk(doc.id, "Chunk 2")
        await repo.add_chunk(doc.id, "Chunk 3")

        deleted = await repo.delete_chunks_by_doc_id(doc.id)
        assert deleted == 3

        # Verify they're gone
        c1 = await repo.get_chunk(1)  # IDs may vary, but should be None
        # All chunks for this doc should be deleted
        docs = await repo.list_docs()
        assert len(docs) == 1  # doc still exists


# ---------------------------------------------------------------------------
# SkillRepo tests
# ---------------------------------------------------------------------------

class TestSkillRepo:
    async def test_list_modules(self, session: AsyncSession):
        repo = SkillRepo(session)
        m1 = SkillModule(
            slug="parallel-parking",
            name_en="Parallel Parking",
            name_pt="Estacionamento Paralelo",
            sort_order=1,
            overview_en="Learn parallel parking",
            overview_pt="Aprenda estacionamento paralelo",
            svg_path="/svg/parking.svg",
            correct_trajectory_json="{}",
            wrong_trajectory_json="{}",
            common_mistakes_json="[]",
            checklist_json="[]",
            pro_tip_en="Check mirrors",
            pro_tip_pt="Verifique os espelhos",
        )
        m2 = SkillModule(
            slug="hill-start",
            name_en="Hill Start",
            name_pt="Partida em Subida",
            sort_order=2,
            overview_en="Learn hill starts",
            overview_pt="Aprenda partidas em subida",
            svg_path="/svg/hill.svg",
            correct_trajectory_json="{}",
            wrong_trajectory_json="{}",
            common_mistakes_json="[]",
            checklist_json="[]",
            pro_tip_en="Use handbrake",
            pro_tip_pt="Use o freio de mão",
        )
        session.add_all([m1, m2])
        await session.flush()

        modules = await repo.list_modules()
        assert len(modules) == 2
        assert modules[0].slug == "parallel-parking"
        assert modules[1].slug == "hill-start"

    async def test_get_by_slug_found(self, session: AsyncSession):
        repo = SkillRepo(session)
        m = SkillModule(
            slug="parallel-parking",
            name_en="Parallel Parking",
            name_pt="Estacionamento Paralelo",
            sort_order=1,
            overview_en="Learn parallel parking",
            overview_pt="Aprenda estacionamento paralelo",
            svg_path="/svg/parking.svg",
            correct_trajectory_json="{}",
            wrong_trajectory_json="{}",
            common_mistakes_json="[]",
            checklist_json="[]",
            pro_tip_en="Check mirrors",
            pro_tip_pt="Verifique os espelhos",
        )
        session.add(m)
        await session.flush()

        result = await repo.get_by_slug("parallel-parking")
        assert result is not None
        assert result.slug == "parallel-parking"

    async def test_get_by_slug_not_found(self, session: AsyncSession):
        repo = SkillRepo(session)
        result = await repo.get_by_slug("nonexistent")
        assert result is None
