"""Attempt API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.api.repositories.attempt_repo import AttemptRepo

router = APIRouter()


@router.get("/")
async def list_attempts(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """List all attempts (paginated)."""
    repo = AttemptRepo(session)
    attempts = await repo.list(limit=limit, offset=offset)

    items = []
    for attempt in attempts:
        items.append({
            "attempt_id": attempt.id,
            "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
            "finished_at": attempt.finished_at.isoformat() if attempt.finished_at else None,
            "score": attempt.score,
            "max_score": attempt.max_score,
            "passed": attempt.passed,
            "language": attempt.language,
            "difficulty_tricky": attempt.difficulty_tricky,
            "time_limit_seconds": attempt.time_limit_seconds,
        })

    return JSONResponse(content={"items": items, "total": len(items)})


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_attempt(
    language: str = Query(default="en", pattern="^(en|pt)$"),
    difficulty_tricky: float = Query(default=0.0, ge=0.0, le=1.0),
    time_limit_seconds: int = Query(default=1800, ge=0, le=1800),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Create a new attempt record."""
    repo = AttemptRepo(session)
    attempt = await repo.create(
        language=language,
        difficulty_tricky=difficulty_tricky,
        time_limit_seconds=time_limit_seconds,
    )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "attempt_id": attempt.id,
            "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
            "language": attempt.language,
            "difficulty_tricky": attempt.difficulty_tricky,
            "time_limit_seconds": attempt.time_limit_seconds,
        },
    )


@router.get("/{attempt_id}")
async def get_attempt(
    attempt_id: int,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Get a single attempt by ID."""
    repo = AttemptRepo(session)
    attempt = await repo.get_with_answers(attempt_id)
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found"
        )

    return JSONResponse(content={
        "attempt_id": attempt.id,
        "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
        "finished_at": attempt.finished_at.isoformat() if attempt.finished_at else None,
        "score": attempt.score,
        "max_score": attempt.max_score,
        "passed": attempt.passed,
        "language": attempt.language,
        "difficulty_tricky": attempt.difficulty_tricky,
        "time_limit_seconds": attempt.time_limit_seconds,
    })
