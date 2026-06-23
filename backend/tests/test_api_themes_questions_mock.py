"""API endpoint tests — themes, questions, mock tests, attempts."""

from __future__ import annotations

import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db import get_session
from src.main import app


@pytest.fixture
async def test_engine():
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    db_path = tmp.name
    tmp.close()
    db_url = f"sqlite+aiosqlite:///{db_path}"

    engine = create_async_engine(db_url, echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def _load_vec(dbapi_conn, connection_record):
        import sqlite_vec
        raw_conn = dbapi_conn._connection
        raw_conn.enable_load_extension(True)
        raw_conn.load_extension(sqlite_vec.loadable_path())

    from db import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
    os.unlink(db_path)


@pytest.fixture
async def test_session(test_engine):
    session_maker = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_maker() as session:
        yield session


async def seed_theme(session: AsyncSession, slug: str = "traffic-signs", theme_id: int = 1):
    from models.theme import Theme
    theme = Theme(
        id=theme_id,
        slug=slug,
        name_en="Traffic Signs",
        name_pt="Sinais de Trnsito",
        sort_order=1,
    )
    session.add(theme)
    await session.commit()
    return theme


async def seed_questions(session: AsyncSession, count: int = 60, theme_id: int = 1):
    from models.question import Question
    questions = []
    for i in range(count):
        is_tricky = i < 15
        questions.append(
            Question(
                theme_id=theme_id,
                prompt_en=f"Question {i}: Is this statement correct?",
                prompt_pt=f"Pergunta {i}: Esta afirmação está correta?",
                answer_en="true" if i % 2 == 0 else "false",
                answer_pt="true" if i % 2 == 0 else "false",
                explanation_en=f"Explanation for question {i}",
                explanation_pt=f"Explicação para pergunta {i}",
                tricky=is_tricky,
                tricky_pattern="double_negative" if is_tricky else None,
                translations_status="complete",
            )
        )
    session.add_all(questions)
    await session.commit()
    return questions


@pytest.fixture
async def client(test_engine):
    session_maker = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_session():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


class TestThemesAPI:
    async def test_list_themes_returns_empty_when_no_data(self, client: AsyncClient):
        resp = await client.get("/api/themes/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_get_theme_by_slug_not_found(self, client: AsyncClient):
        resp = await client.get("/api/themes/nonexistent")
        assert resp.status_code == 404

    async def test_get_theme_tree_not_found(self, client: AsyncClient):
        resp = await client.get("/api/themes/nonexistent/tree")
        assert resp.status_code == 404


class TestQuestionsAPI:
    async def test_list_questions_returns_empty_when_no_data(self, client: AsyncClient):
        resp = await client.get("/api/questions/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_list_questions_excludes_answers(self, client: AsyncClient, test_session: AsyncSession):
        await seed_theme(test_session)
        await seed_questions(test_session, count=5)

        resp = await client.get("/api/questions/?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 5

        item = data[0]
        assert "answer_en" not in item
        assert "answer_pt" not in item
        assert "explanation_en" not in item
        assert "explanation_pt" not in item
        assert "id" in item
        assert "prompt_en" in item
        assert "tricky" in item

    async def test_get_question_detail_includes_answers(self, client: AsyncClient, test_session: AsyncSession):
        await seed_theme(test_session)
        questions = await seed_questions(test_session, count=3)

        q_id = questions[0].id
        resp = await client.get(f"/api/questions/{q_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["answer_en"] in ("true", "false")
        assert data["explanation_en"] != ""

    async def test_get_question_not_found(self, client: AsyncClient):
        resp = await client.get("/api/questions/99999")
        assert resp.status_code == 404

    async def test_list_questions_filter_by_theme(self, client: AsyncClient, test_session: AsyncSession):
        await seed_theme(test_session, slug="theme-a", theme_id=1)
        await seed_theme(test_session, slug="theme-b", theme_id=2)
        await seed_questions(test_session, count=3, theme_id=1)
        await seed_questions(test_session, count=2, theme_id=2)

        resp = await client.get("/api/questions/?theme_id=2&limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(q["theme_id"] == 2 for q in data)

    async def test_list_questions_filter_tricky(self, client: AsyncClient, test_session: AsyncSession):
        await seed_theme(test_session)
        await seed_questions(test_session, count=10)

        resp = await client.get("/api/questions/?tricky=1&limit=50")
        assert resp.status_code == 200
        data = resp.json()
        assert all(q["tricky"] is True for q in data)


class TestMockTestsAPI:
    async def test_start_mock_test_validation_question_count_too_low(self, client: AsyncClient):
        resp = await client.post("/api/mock-tests/", json={
            "language": "en",
            "question_count": 4,
        })
        assert resp.status_code == 422

    async def test_start_mock_test_validation_question_count_too_high(self, client: AsyncClient):
        resp = await client.post("/api/mock-tests/", json={
            "language": "en",
            "question_count": 51,
        })
        assert resp.status_code == 422

    async def test_start_mock_test_validation_time_limit_exceeded(self, client: AsyncClient):
        resp = await client.post("/api/mock-tests/", json={
            "language": "en",
            "question_count": 10,
            "time_limit_seconds": 1801,
        })
        assert resp.status_code == 422

    async def test_start_mock_test_validation_invalid_tricky_ratio(self, client: AsyncClient):
        resp = await client.post("/api/mock-tests/", json={
            "language": "en",
            "question_count": 10,
            "tricky_ratio": 0.33,
        })
        assert resp.status_code == 422

    async def test_start_mock_test_validation_valid_tricky_ratios(self, client: AsyncClient):
        for ratio in [0.0, 0.25, 0.5, 0.75, 1.0]:
            resp = await client.post("/api/mock-tests/", json={
                "language": "en",
                "question_count": 5,
                "tricky_ratio": ratio,
            })
            assert resp.status_code != 422 or "tricky_ratio" not in str(resp.json())

    async def test_start_mock_test_returns_questions_without_answers(self, client: AsyncClient, test_session: AsyncSession):
        await seed_theme(test_session)
        await seed_questions(test_session, count=60)

        resp = await client.post("/api/mock-tests/", json={
            "language": "en",
            "question_count": 10,
            "tricky_ratio": 0.5,
            "time_limit_seconds": 600,
            "seed": 42,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "attempt_id" in data
        assert "questions" in data
        assert len(data["questions"]) == 10
        assert "time_limit_seconds" in data
        assert data["time_limit_seconds"] == 600

        q = data["questions"][0]
        assert "answer_en" not in q
        assert "explanation_en" not in q
        assert "prompt_en" in q

    async def test_submit_mock_test_returns_answers_with_explanations(self, client: AsyncClient, test_session: AsyncSession):
        await seed_theme(test_session)
        await seed_questions(test_session, count=60)

        start_resp = await client.post("/api/mock-tests/", json={
            "language": "en",
            "question_count": 10,
            "tricky_ratio": 0.5,
            "time_limit_seconds": 600,
            "seed": 42,
        })
        assert start_resp.status_code == 201
        attempt_id = start_resp.json()["attempt_id"]
        questions = start_resp.json()["questions"]

        answers = []
        for q in questions:
            answers.append({
                "question_id": q["id"],
                "user_answer": "true",
            })

        submit_resp = await client.post(f"/api/mock-tests/{attempt_id}/submit", json={
            "answers": answers,
        })
        assert submit_resp.status_code == 200
        data = submit_resp.json()
        assert "answers" in data
        assert "score" in data
        assert "passed" in data

        answer_item = data["answers"][0]
        assert "explanation_en" in answer_item
        assert "correct_answer" in answer_item
        assert "is_correct" in answer_item

    async def test_get_mock_test_result(self, client: AsyncClient, test_session: AsyncSession):
        await seed_theme(test_session)
        await seed_questions(test_session, count=60)

        start_resp = await client.post("/api/mock-tests/", json={
            "language": "en",
            "question_count": 10,
            "tricky_ratio": 0.5,
            "time_limit_seconds": 600,
            "seed": 42,
        })
        assert start_resp.status_code == 201
        attempt_id = start_resp.json()["attempt_id"]

        resp = await client.get(f"/api/mock-tests/{attempt_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["attempt_id"] == attempt_id

    async def test_get_mock_test_result_not_found(self, client: AsyncClient):
        resp = await client.get("/api/mock-tests/99999")
        assert resp.status_code == 404

    async def test_get_mock_test_history(self, client: AsyncClient):
        resp = await client.get("/api/mock-tests/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    async def test_timeout_check_not_found(self, client: AsyncClient):
        resp = await client.get("/api/mock-tests/99999/timeout")
        assert resp.status_code == 404


class TestAttemptsAPI:
    async def test_list_attempts_returns_empty_when_no_data(self, client: AsyncClient):
        resp = await client.get("/api/attempts/")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    async def test_create_attempt(self, client: AsyncClient):
        resp = await client.post("/api/attempts/", params={
            "language": "en",
            "difficulty_tricky": 0.5,
            "time_limit_seconds": 900,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "attempt_id" in data
        assert data["language"] == "en"

    async def test_get_attempt_not_found(self, client: AsyncClient):
        resp = await client.get("/api/attempts/99999")
        assert resp.status_code == 404
