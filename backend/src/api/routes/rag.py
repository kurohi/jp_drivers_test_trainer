"""RAG Teacher API routes."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_ollama, get_session, get_settings
from src.config import Settings
from src.db import PROJECT_ROOT
from src.llm.exceptions import OllamaUnavailableError
from src.llm.provider import OllamaClient
from src.rag.embedder import Embedder
from src.rag.retriever import Retriever
from src.schemas.rag import RagAnswerOut, RagQueryIn
from src.services.rag_teacher_service import RagTeacherService

router = APIRouter(prefix="/api/rag", tags=["rag"])


def _vec_conn_factory(db_path: Path | None = None) -> sqlite3.Connection:
    """Create a fresh sqlite3.Connection with sqlite-vec loaded."""
    import sqlite_vec

    if db_path is None:
        db_path = PROJECT_ROOT / "data" / "jp_drivers.sqlite"

    conn = sqlite3.connect(str(db_path))
    conn.enable_load_extension(True)
    conn.load_extension(sqlite_vec.loadable_path())
    return conn


@router.post("/ask", response_model=RagAnswerOut)
async def ask_question(
    body: RagQueryIn,
    session: AsyncSession = Depends(get_session),
    ollama_client: OllamaClient = Depends(get_ollama),
    settings: Settings = Depends(get_settings),
) -> RagAnswerOut:
    """Answer a question using RAG over the JP driver's test corpus.

    Returns a refusal if no relevant chunks are found (all distances >= 0.2).
    Returns HTTP 503 if Ollama is unavailable.
    """
    # Build the embedder (wraps OllamaClient for embeddings)
    embedder = Embedder(ollama_client=ollama_client, batch_delay_seconds=0.0)

    # Build the retriever
    retriever = Retriever(
        embedder=embedder,
        vec_conn_factory=_vec_conn_factory,
        session=session,
    )

    # Build the teacher service
    service = RagTeacherService(
        retriever=retriever,
        ollama_client=ollama_client,
        min_distance=0.2,
    )

    try:
        return await service.ask(
            question=body.question,
            language=body.language,
            k=body.k,
        )
    except OllamaUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ollama_unavailable",
                "host": settings.ollama_url,
                "message": str(e),
            },
        )
