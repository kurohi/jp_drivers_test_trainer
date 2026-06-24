"""RAG retriever — embed query, search sqlite-vec, join with ORM for source metadata."""
from __future__ import annotations

import asyncio
import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.rag_chunk import RagChunk, RagDocument
from src.rag.embedder import Embedder
from src.rag.vector_store import VectorStore

if TYPE_CHECKING:
    pass


@dataclass
class RetrievedChunk:
    """A retrieved chunk with its similarity distance and source document."""

    chunk: RagChunk
    document: RagDocument
    distance: float


class Retriever:
    """Async retriever that embeds a query, searches sqlite-vec, and joins with ORM.

    Args:
        embedder: T6 Embedder for query embedding.
        vec_conn_factory: Callable that returns a fresh sqlite3.Connection with
            sqlite-vec loaded (sync, called inside asyncio.to_thread).
        session: AsyncSession for ORM lookups.
    """

    def __init__(
        self,
        embedder: Embedder,
        vec_conn_factory: callable,
        session: AsyncSession,
    ) -> None:
        self._embedder = embedder
        self._vec_conn_factory = vec_conn_factory
        self._session = session

    async def retrieve(
        self,
        query: str,
        k: int = 5,
        min_distance: float = 0.2,
    ) -> list[RetrievedChunk]:
        """Embed query, search vector store, join with ORM for source metadata.

        Args:
            query: The user's question.
            k: Maximum number of chunks to retrieve.
            min_distance: Maximum allowed distance (Euclidean). Chunks with
                distance >= this threshold are filtered out.

        Returns:
            List of RetrievedChunk ordered by ascending distance (most similar first).
        """
        # Step 1: Embed the query
        query_embedding = await self._embedder.embed(query)

        # Step 2: Search vector store (sync — bridge via to_thread)
        def _search() -> list[tuple[int, float]]:
            conn = self._vec_conn_factory()
            try:
                store = VectorStore(conn)
                return store.search(query_embedding, k=k)
            finally:
                conn.close()

        raw_results = await asyncio.to_thread(_search)

        # Step 3: Filter by min_distance threshold
        filtered = [(rowid, dist) for rowid, dist in raw_results if dist < min_distance]
        if not filtered:
            return []

        # Step 4: Fetch RagChunk + RagDocument from ORM
        chunk_ids = [rowid for rowid, _ in filtered]
        stmt = (
            select(RagChunk)
            .where(RagChunk.id.in_(chunk_ids))
            .options(selectinload(RagChunk.document))
        )
        result = await self._session.execute(stmt)
        chunks = result.scalars().all()

        # Build lookup: chunk_id → RagChunk
        chunk_map = {c.id: c for c in chunks}

        # Step 5: Assemble RetrievedChunk list, preserving distance order
        retrieved: list[RetrievedChunk] = []
        for rowid, dist in filtered:
            chunk = chunk_map.get(rowid)
            if chunk is not None:
                retrieved.append(
                    RetrievedChunk(
                        chunk=chunk,
                        document=chunk.document,
                        distance=dist,
                    )
                )

        return retrieved
