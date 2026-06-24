"""Skill-test walkthrough API — list, lookup, and serve SVG diagrams."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.models.skill_module import SkillModule
from src.api.repositories.skill_repo import SkillRepo

router = APIRouter(prefix="/api/skill-test", tags=["skill-test"])

# Project root: backend/src/api/routes/ -> backend/ -> project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_FRONTEND_PUBLIC = _PROJECT_ROOT / "frontend" / "public"


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------


def _get_skill_repo(
    session: AsyncSession = Depends(get_session),
) -> SkillRepo:
    return SkillRepo(session)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class SkillModuleListItem(BaseModel):
    """Lightweight module info for list endpoint (no heavy JSON blobs)."""

    model_config = {"from_attributes": True}

    id: int
    slug: str
    name_en: str
    name_pt: str
    sort_order: int


class SkillModuleDetail(BaseModel):
    """Full module detail for single-module endpoint."""

    model_config = {"from_attributes": True}

    id: int
    slug: str
    name_en: str
    name_pt: str
    sort_order: int
    overview_en: str
    overview_pt: str
    svg_path: Optional[str] = None
    correct_trajectory_json: str
    wrong_trajectory_json: str
    common_mistakes_json: str
    checklist_json: str
    pro_tip_en: str
    pro_tip_pt: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/modules", response_model=list[SkillModuleListItem])
async def list_modules(
    repo: SkillRepo = Depends(_get_skill_repo),
) -> list[SkillModuleListItem]:
    """List all skill modules (lightweight, no heavy JSON fields)."""
    modules = await repo.list_modules()
    return modules


@router.get("/modules/{slug}", response_model=SkillModuleDetail)
async def get_module(
    slug: str,
    repo: SkillRepo = Depends(_get_skill_repo),
) -> SkillModuleDetail:
    """Get a single skill module by slug."""
    module = await repo.get_by_slug(slug)
    if module is None:
        raise HTTPException(status_code=404, detail=f"Module '{slug}' not found")
    return module


@router.get("/modules/{slug}/diagram")
async def get_module_diagram(
    slug: str,
    repo: SkillRepo = Depends(_get_skill_repo),
) -> Response:
    """Return the SVG diagram file for a skill module."""
    module = await repo.get_by_slug(slug)
    if module is None:
        raise HTTPException(status_code=404, detail=f"Module '{slug}' not found")
    if not module.svg_path:
        raise HTTPException(status_code=404, detail=f"No diagram for module '{slug}'")

    svg_file = _FRONTEND_PUBLIC / module.svg_path
    if not svg_file.is_file():
        raise HTTPException(status_code=404, detail=f"SVG file not found: {module.svg_path}")

    return Response(
        content=svg_file.read_bytes(),
        media_type="image/svg+xml",
    )
