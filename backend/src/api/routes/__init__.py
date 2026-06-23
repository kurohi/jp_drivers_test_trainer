"""API routes — barrel export and router aggregation."""

from fastapi import APIRouter

from .themes import router as themes_router
from .questions import router as questions_router
from .mock_tests import router as mock_tests_router
from .attempts import router as attempts_router

api_router = APIRouter()

api_router.include_router(themes_router, prefix="/themes", tags=["themes"])
api_router.include_router(questions_router, prefix="/questions", tags=["questions"])
api_router.include_router(mock_tests_router, prefix="/mock-tests", tags=["mock-tests"])
api_router.include_router(attempts_router, prefix="/attempts", tags=["attempts"])

__all__ = ["api_router"]
