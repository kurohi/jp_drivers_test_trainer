"""RAG (Retrieval-Augmented Generation) schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class RagQueryIn(BaseModel):
    """RAG query input."""

    question: str
    language: Literal["en", "pt"]
    k: int = Field(default=5, ge=1, le=20)


class RagSourceOut(BaseModel):
    """A single RAG source."""

    source_url: str
    title: str
    snippet: str


class RagAnswerOut(BaseModel):
    """RAG answer output."""

    answer: str
    sources: list[RagSourceOut]
