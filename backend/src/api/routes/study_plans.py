"""Study plan API routes."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_ollama, get_session, get_settings, get_study_plan_repo
from src.api.repositories.study_plan_repo import StudyPlanRepo
from src.config import Settings
from src.llm.provider import OllamaClient
from src.schemas.study_plan import PlanDay, StudyPlanGenerateIn, StudyPlanOut
from src.services.study_plan_service import StudyPlanService

router = APIRouter(prefix="/api/study-plans", tags=["study-plans"])


def _plan_to_out(plan: StudyPlanRepo) -> StudyPlanOut:
    """Convert a StudyPlan ORM record to StudyPlanOut."""
    days_data = json.loads(plan.days_json)
    days = [PlanDay(**d) for d in days_data]
    return StudyPlanOut(
        id=plan.id,
        created_at=plan.created_at.isoformat(),
        source=plan.source,
        days=days,
    )


@router.post("/generate", response_model=StudyPlanOut)
async def generate_study_plan(
    body: StudyPlanGenerateIn,
    session: AsyncSession = Depends(get_session),
    ollama_client: OllamaClient = Depends(get_ollama),
    settings: Settings = Depends(get_settings),
) -> StudyPlanOut:
    """Generate a new study plan based on weak areas."""
    service = StudyPlanService(session)
    return await service.generate_study_plan(
        available_days=body.available_days,
        hours_per_day=body.hours_per_day,
        ollama_client=ollama_client,
        settings=settings,
    )


@router.get("/latest", response_model=StudyPlanOut)
async def get_latest_study_plan(
    session: AsyncSession = Depends(get_session),
    study_plan_repo: StudyPlanRepo = Depends(get_study_plan_repo),
) -> StudyPlanOut:
    """Get the most recently generated study plan."""
    plan = await study_plan_repo.latest()
    if plan is None:
        raise HTTPException(status_code=404, detail="No study plan found")
    return _plan_to_out(plan)


@router.get("/history")
async def get_study_plan_history(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    study_plan_repo: StudyPlanRepo = Depends(get_study_plan_repo),
) -> list[StudyPlanOut]:
    """Get study plan history with pagination."""
    plans = await study_plan_repo.list(limit=limit)
    return [_plan_to_out(p) for p in plans]
