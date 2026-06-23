"""Mock test API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.services.mock_test_service import MockTestService
from src.schemas.attempt import (
    AttemptResultOut,
    AttemptStartIn,
    AttemptSubmitIn,
)
from src.schemas.question import QuestionListItem
from src.schemas.ui_meta import Difficulty

router = APIRouter()


def _map_difficulty(difficulty: int) -> Difficulty:
    """Map integer difficulty (1-5) to Difficulty literal."""
    mapping = {1: 0.0, 2: 0.25, 3: 0.5, 4: 0.75, 5: 1.0}
    return mapping.get(difficulty, 0.5)


def _question_dict_to_list_item(q_dict: dict) -> QuestionListItem:
    """Convert a question dict (from SelectionResult) to QuestionListItem."""
    return QuestionListItem(
        id=q_dict["id"],
        theme_id=q_dict["theme_id"],
        prompt_en=q_dict["prompt_en"],
        prompt_pt=q_dict["prompt_pt"],
        tricky=q_dict["tricky"],
        tricky_pattern=q_dict.get("tricky_pattern"),
        difficulty=_map_difficulty(q_dict.get("difficulty", 3)),
        translations_status="complete",
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def start_mock_test(
    body: AttemptStartIn,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """
    Start a new mock test attempt.
    Returns attempt_id, started_at, expires_at, questions (WITHOUT answers), time_limit_seconds.
    """
    service = MockTestService(session)
    try:
        selection = await service.select_questions(
            theme_ids=body.theme_ids,
            question_count=body.question_count,
            tricky_ratio=body.tricky_ratio,
            language=body.language,
            seed=body.seed,
            time_limit_seconds=body.time_limit_seconds,
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(e)},
        )

    # Calculate expires_at
    started_at = datetime.now(timezone.utc)
    expires_at_ts = started_at.timestamp() + body.time_limit_seconds
    expires_at = datetime.fromtimestamp(expires_at_ts, tz=timezone.utc)

    questions = [
        _question_dict_to_list_item(q) for q in selection.questions
    ]

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "attempt_id": selection.attempt_id,
            "started_at": started_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "questions": [q.model_dump() for q in questions],
            "time_limit_seconds": body.time_limit_seconds,
        },
    )


@router.post("/{attempt_id}/submit", response_model=AttemptResultOut)
async def submit_mock_test(
    attempt_id: int,
    body: AttemptSubmitIn,
    session: AsyncSession = Depends(get_session),
) -> AttemptResultOut:
    """
    Submit answers for a mock test attempt.
    Returns AttemptResultOut with answers + explanations (only after submit).
    """
    service = MockTestService(session)
    try:
        result = await service.score_attempt(
            attempt_id=attempt_id,
            user_answers=body.answers,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    return result


@router.get("/history")
async def get_mock_test_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Get mock test attempt history."""
    from src.api.repositories.attempt_repo import AttemptRepo

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
        })

    return JSONResponse(content={"items": items, "total": len(items)})


@router.get("/{attempt_id}")
async def get_mock_test_result(
    attempt_id: int,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Fetch a mock test attempt result."""
    from src.api.repositories.attempt_repo import AttemptRepo

    repo = AttemptRepo(session)
    attempt = await repo.get_with_answers(attempt_id)
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found"
        )

    content = {
        "attempt_id": attempt.id,
        "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
        "finished_at": attempt.finished_at.isoformat() if attempt.finished_at else None,
        "score": attempt.score,
        "max_score": attempt.max_score,
        "passed": attempt.passed,
        "language": attempt.language,
        "difficulty_tricky": attempt.difficulty_tricky,
        "time_limit_seconds": attempt.time_limit_seconds,
    }
    return JSONResponse(content=content)


@router.get("/{attempt_id}/timeout")
async def check_timeout(
    attempt_id: int,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """
    Check time remaining for an attempt.
    Returns {remaining_seconds, expired}.
    If expired + unsubmitted, auto-scores.
    """
    from src.api.repositories.attempt_repo import AttemptRepo

    repo = AttemptRepo(session)
    attempt = await repo.get_with_answers(attempt_id)
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found"
        )

    service = MockTestService(session)

    # Check if already finished
    if attempt.finished_at is not None:
        return JSONResponse(content={
            "remaining_seconds": 0,
            "expired": True,
        })

    remaining = service.time_remaining(attempt)
    expired = remaining <= 0

    if expired:
        # Auto-score if expired and not yet submitted
        try:
            result = await service.enforce_time_limit(attempt_id)
            if result is not None:
                return JSONResponse(content={
                    "remaining_seconds": 0,
                    "expired": True,
                    "auto_scored": True,
                    "score": result.score,
                    "max_score": result.max_score,
                    "passed": result.passed,
                })
        except ValueError:
            pass  # Already scored or other error

    return JSONResponse(content={
        "remaining_seconds": remaining,
        "expired": expired,
    })
