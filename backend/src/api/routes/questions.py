"""Question API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.api.repositories.question_repo import QuestionRepo
from src.schemas.question import QuestionDetail, QuestionListItem
from src.schemas.ui_meta import Difficulty

router = APIRouter()


def _question_to_list_item(q, language: str = "en") -> QuestionListItem:
    """Convert ORM Question to QuestionListItem — NO answers or explanations."""
    return QuestionListItem(
        id=q.id,
        theme_id=q.theme_id,
        prompt_en=q.prompt_en,
        prompt_pt=q.prompt_pt,
        tricky=q.tricky,
        tricky_pattern=q.tricky_pattern,
        difficulty=_map_difficulty(q.difficulty),
        translations_status=q.translations_status,
    )


def _question_to_detail(q, language: str = "en") -> QuestionDetail:
    """Convert ORM Question to QuestionDetail — WITH answers and explanations."""
    return QuestionDetail(
        id=q.id,
        theme_id=q.theme_id,
        prompt_en=q.prompt_en,
        prompt_pt=q.prompt_pt,
        tricky=q.tricky,
        tricky_pattern=q.tricky_pattern,
        difficulty=_map_difficulty(q.difficulty),
        translations_status=q.translations_status,
        answer_en=q.answer_en,
        answer_pt=q.answer_pt,
        explanation_en=q.explanation_en,
        explanation_pt=q.explanation_pt,
    )


def _map_difficulty(difficulty: int) -> Difficulty:
    """Map integer difficulty (1-5) to Difficulty literal."""
    mapping = {1: 0.0, 2: 0.25, 3: 0.5, 4: 0.75, 5: 1.0}
    return mapping.get(difficulty, 0.5)


@router.get("/", response_model=list[QuestionListItem])
async def list_questions(
    theme_id: int | None = Query(default=None),
    tricky: int = Query(default=0, ge=0, le=1),
    language: str = Query(default="en", pattern="^(en|pt)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[QuestionListItem]:
    """
    List questions WITHOUT answers or explanations.
    Returns QuestionListItem summaries only.
    """
    repo = QuestionRepo(session)
    questions = await repo.list(
        theme_id=theme_id,
        tricky_only=bool(tricky),
        language=language,
        limit=limit,
        offset=offset,
    )
    return [_question_to_list_item(q, language) for q in questions]


@router.get("/{question_id}", response_model=QuestionDetail)
async def get_question(
    question_id: int,
    language: str = Query(default="en", pattern="^(en|pt)$"),
    session: AsyncSession = Depends(get_session),
) -> QuestionDetail:
    """
    Get a single question WITH answer and explanation.
    Only use this for review/admin — not during active mock tests.
    """
    repo = QuestionRepo(session)
    question = await repo.get_by_id(question_id)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )
    return _question_to_detail(question, language)
