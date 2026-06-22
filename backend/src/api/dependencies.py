"""API dependency injectors."""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.db import get_session
from src.llm.provider import OllamaClient
from src.api.repositories.theme_repo import ThemeRepo
from src.api.repositories.question_repo import QuestionRepo
from src.api.repositories.attempt_repo import AttemptRepo
from src.api.repositories.study_plan_repo import StudyPlanRepo
from src.api.repositories.rag_doc_repo import RagDocRepo
from src.api.repositories.skill_repo import SkillRepo


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton (reads config.yaml + .env)."""
    return Settings()


def get_ollama() -> OllamaClient:
    """Build an OllamaClient from settings (one per request)."""
    return OllamaClient(get_settings())


# ---------------------------------------------------------------------------
# Repository dependency factories
# ---------------------------------------------------------------------------


def get_theme_repo(
    session: AsyncSession = Depends(get_session),
) -> ThemeRepo:
    """Yield a ThemeRepo bound to the request-scoped async session."""
    return ThemeRepo(session)


def get_question_repo(
    session: AsyncSession = Depends(get_session),
) -> QuestionRepo:
    """Yield a QuestionRepo bound to the request-scoped async session."""
    return QuestionRepo(session)


def get_attempt_repo(
    session: AsyncSession = Depends(get_session),
) -> AttemptRepo:
    """Yield an AttemptRepo bound to the request-scoped async session."""
    return AttemptRepo(session)


def get_study_plan_repo(
    session: AsyncSession = Depends(get_session),
) -> StudyPlanRepo:
    """Yield a StudyPlanRepo bound to the request-scoped async session."""
    return StudyPlanRepo(session)


def get_rag_doc_repo(
    session: AsyncSession = Depends(get_session),
) -> RagDocRepo:
    """Yield a RagDocRepo bound to the request-scoped async session."""
    return RagDocRepo(session)


def get_skill_repo(
    session: AsyncSession = Depends(get_session),
) -> SkillRepo:
    """Yield a SkillRepo bound to the request-scoped async session."""
    return SkillRepo(session)
