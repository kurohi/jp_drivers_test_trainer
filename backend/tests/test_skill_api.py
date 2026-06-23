"""TDD tests for the skill-test walkthrough API endpoints.

Uses an in-memory SQLite database with skill_modules seeded from ORM objects.
Overrides the DB session dependency to isolate from production data.
"""

from __future__ import annotations

from typing import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db import Base, get_session
from main import app
from models.skill_module import SkillModule

TEST_DB_URL = "sqlite+aiosqlite://"


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


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """HTTP client with overridden DB session dependency."""

    async def _override_get_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


def _make_skill_module(
    slug: str,
    name_en: str = "Test Module",
    name_pt: str = "Modulo de Teste",
    sort_order: int = 1,
) -> SkillModule:
    """Factory for a minimal SkillModule ORM object."""
    return SkillModule(
        slug=slug,
        name_en=name_en,
        name_pt=name_pt,
        sort_order=sort_order,
        overview_en="Overview in English",
        overview_pt="Resumo em portugues",
        svg_path=f"assets/skill/{slug}-diagram.svg",
        correct_trajectory_json='{"keypoints": [], "path": []}',
        wrong_trajectory_json='{"keypoints": [], "path": [], "failure_reason": {}}',
        common_mistakes_json='{"en": [], "pt": []}',
        checklist_json='[]',
        pro_tip_en="Test pro tip",
        pro_tip_pt="Dica de teste",
    )


class TestSkillTestAPI:
    """Tests for GET /api/skill-test/modules, /{slug}, and /{slug}/diagram."""

    async def test_list_modules_empty(self, client: AsyncClient):
        """List endpoint returns empty array when no modules exist."""
        resp = await client.get("/api/skill-test/modules")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_modules_returns_8(self, client: AsyncClient, session: AsyncSession):
        """List endpoint returns all seeded modules with lightweight fields only."""
        slugs = [
            "s-curve", "crank", "hill-start", "parallel-parking",
            "pedestrian-crossing", "railroad-crossing", "sudden-stop",
            "general-driving",
        ]
        modules = [_make_skill_module(slug, sort_order=i) for i, slug in enumerate(slugs, 1)]
        session.add_all(modules)
        await session.flush()

        resp = await client.get("/api/skill-test/modules")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 8

        # Verify lightweight fields only (no heavy JSON blobs)
        item = data[0]
        assert set(item.keys()) == {"id", "slug", "name_en", "name_pt", "sort_order"}
        assert item["slug"] == "s-curve"

    async def test_get_module_by_slug(self, client: AsyncClient, session: AsyncSession):
        """Single module endpoint returns full detail."""
        mod = _make_skill_module("crank", sort_order=2)
        session.add(mod)
        await session.flush()

        resp = await client.get("/api/skill-test/modules/crank")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "crank"
        assert data["name_en"] == "Test Module"
        assert data["overview_en"] == "Overview in English"
        assert data["correct_trajectory_json"] == '{"keypoints": [], "path": []}'
        assert data["svg_path"] == "assets/skill/crank-diagram.svg"

    async def test_get_module_by_slug_404(self, client: AsyncClient):
        """Unknown slug returns 404."""
        resp = await client.get("/api/skill-test/modules/nonexistent-module")
        assert resp.status_code == 404
        assert "nonexistent-module" in resp.json()["detail"]

    async def test_get_module_diagram_404_no_module(self, client: AsyncClient):
        """Diagram endpoint returns 404 for unknown slug."""
        resp = await client.get("/api/skill-test/modules/unknown/diagram")
        assert resp.status_code == 404

    async def test_get_module_diagram_404_no_svg_path(self, client: AsyncClient, session: AsyncSession):
        """Diagram endpoint returns 404 when module has no svg_path."""
        mod = _make_skill_module("no-svg")
        mod.svg_path = None
        session.add(mod)
        await session.flush()

        resp = await client.get("/api/skill-test/modules/no-svg/diagram")
        assert resp.status_code == 404

    async def test_get_module_diagram_404_file_not_found(self, client: AsyncClient, session: AsyncSession):
        """Diagram endpoint returns 404 when SVG file does not exist on disk."""
        mod = _make_skill_module("missing-file")
        mod.svg_path = "assets/skill/nonexistent-diagram.svg"
        session.add(mod)
        await session.flush()

        resp = await client.get("/api/skill-test/modules/missing-file/diagram")
        assert resp.status_code == 404
