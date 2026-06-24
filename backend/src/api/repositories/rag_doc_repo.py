"""RAG document repository — docs, chunks, deletion."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.rag_chunk import RagDocument, RagChunk


class RagDocRepo:
    """CRUD queries for RagDocument and RagChunk entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_docs(self) -> list[RagDocument]:
        """List all RAG documents ordered by creation date."""
        stmt = select(RagDocument).order_by(RagDocument.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_doc(
        self,
        title: str,
        doc_type: str,
        raw_text: str,
        source_url: Optional[str] = None,
    ) -> RagDocument:
        """Create a new RagDocument and return it."""
        doc = RagDocument(
            title=title,
            doc_type=doc_type,
            raw_text=raw_text,
            source_url=source_url,
        )
        self._session.add(doc)
        await self._session.flush()
        await self._session.refresh(doc)
        return doc

    async def add_chunk(
        self,
        document_id: int,
        chunk_text: str,
        chunk_idx: int = 0,
        embedding_id: Optional[str] = None,
    ) -> RagChunk:
        """Create a new RagChunk and return it."""
        chunk = RagChunk(
            document_id=document_id,
            chunk_text=chunk_text,
            chunk_idx=chunk_idx,
            embedding_id=embedding_id,
        )
        self._session.add(chunk)
        await self._session.flush()
        await self._session.refresh(chunk)
        return chunk

    async def get_chunk(self, chunk_id: int) -> Optional[RagChunk]:
        """Return a single RagChunk by ID, or None."""
        stmt = select(RagChunk).where(RagChunk.id == chunk_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def delete_chunks_by_doc_id(self, doc_id: int) -> int:
        """Delete all RagChunks belonging to a document. Returns count deleted."""
        stmt = delete(RagChunk).where(RagChunk.document_id == doc_id)
        result = await self._session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]
