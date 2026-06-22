from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TEXT, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base

if TYPE_CHECKING:
    pass  # RagChunk and RagDocument reference each other via strings only


class RagDocument(Base):
    """
    A source document (rule, explanation, or skill) used for RAG.
    """
    __tablename__ = "rag_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_url: Mapped[str] = mapped_column(String(500), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    doc_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "rule" | "explanation" | "skill"
    raw_text: Mapped[str] = mapped_column(TEXT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    chunks: Mapped[list[RagChunk]] = relationship(
        "RagChunk", back_populates="document", lazy="noload"
    )


class RagChunk(Base):
    """
    A chunk of a RagDocument, stored for vector similarity search.
    embedding_id references the row in vec_chunks.
    """
    __tablename__ = "rag_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rag_documents.id"), nullable=False
    )
    chunk_text: Mapped[str] = mapped_column(TEXT, nullable=False)
    chunk_idx: Mapped[int] = mapped_column(Integer, default=0)
    embedding_id: Mapped[str] = mapped_column(String(100), nullable=True)

    document: Mapped[RagDocument] = relationship(
        "RagDocument", back_populates="chunks", lazy="noload"
    )
