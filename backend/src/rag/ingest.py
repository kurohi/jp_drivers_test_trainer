"""
End-to-end RAG ingest pipeline.

Pipeline: read raw docs from data/rag_source_documents/ → chunk → embed
(via T6 embedder) → store (via T6 vector_store) → persist RagDocument +
RagChunk rows via SQLAlchemy.

Idempotent: if a document with matching source_url is re-ingested, delete
its old chunks + vec rows first.

Ollama-down: if OllamaUnavailableError raised, CLI prints clear error and
exits non-zero; no partial state in DB.
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, AsyncIterator

from tqdm import tqdm

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.db import PROJECT_ROOT
from src.llm.exceptions import OllamaUnavailableError
from src.models.rag_chunk import RagDocument, RagChunk
from src.rag.chunker import SemanticChunker
from src.rag.embedder import Embedder
from src.rag.vector_store import VectorStore

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class RawDocument:
    """A raw document loaded from a JSON file."""
    source_url: str
    title: str
    doc_type: str
    text: str
    file_path: str


# ---------------------------------------------------------------------------
# Test helpers — create isolated DB for tests
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _test_session_maker() -> AsyncIterator[tuple[async_sessionmaker, Path]]:
    """Create a temporary SQLite DB with all tables + vec_chunks for testing.

    Yields (session_maker, db_path). Caller is responsible for cleanup.
    """
    import sqlite_vec

    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    db_path = Path(tmp.name)
    tmp.close()

    # Pre-setup: create tables + vec_chunks on a sync connection so the
    # sqlite-vec extension is loaded on the DB file before async opens it.
    sync_conn = sqlite3.connect(str(db_path))
    sync_conn.enable_load_extension(True)
    sync_conn.load_extension(sqlite_vec.loadable_path())
    sync_conn.execute("PRAGMA foreign_keys = ON")

    # Create ORM tables via SQLAlchemy metadata
    from sqlalchemy import MetaData
    metadata = MetaData()
    # Manually create the tables we need
    sync_conn.execute("""
        CREATE TABLE IF NOT EXISTS rag_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url VARCHAR(500),
            title VARCHAR(300) NOT NULL,
            doc_type VARCHAR(20) NOT NULL,
            raw_text TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    sync_conn.execute("""
        CREATE TABLE IF NOT EXISTS rag_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL REFERENCES rag_documents(id),
            chunk_text TEXT NOT NULL,
            chunk_idx INTEGER NOT NULL DEFAULT 0,
            embedding_id VARCHAR(100)
        )
    """)
    sync_conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(embedding float[768])"
    )
    sync_conn.commit()
    sync_conn.close()

    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(db_url, echo=False)

    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    try:
        yield session_maker, db_path
    finally:
        await engine.dispose()
        db_path.unlink(missing_ok=True)


def _get_vec_conn(db_path: Path) -> sqlite3.Connection:
    """Open a sync sqlite3 connection with sqlite-vec loaded."""
    import sqlite_vec

    conn = sqlite3.connect(str(db_path))
    conn.enable_load_extension(True)
    conn.load_extension(sqlite_vec.loadable_path())
    return conn


def _load_raw_documents(source_dir: Path | None = None) -> list[RawDocument]:
    """Load all JSON documents from the source directory tree."""
    if source_dir is None:
        source_dir = PROJECT_ROOT / "data" / "rag_source_documents"

    docs: list[RawDocument] = []
    for json_path in sorted(source_dir.rglob("*.json")):
        with open(json_path) as f:
            data = json.load(f)
        docs.append(RawDocument(
            source_url=data["source_url"],
            title=data["title"],
            doc_type=data["doc_type"],
            text=data["text"],
            file_path=str(json_path),
        ))
    return docs


async def _delete_existing_doc(
    session: AsyncSession, source_url: str, vec_conn: sqlite3.Connection | None
) -> list[int]:
    """Delete an existing document and its chunks + vec rows. Returns old chunk IDs."""
    from sqlalchemy.orm import selectinload

    result = await session.execute(
        select(RagDocument)
        .where(RagDocument.source_url == source_url)
        .options(selectinload(RagDocument.chunks))
    )
    existing = result.scalar_one_or_none()
    if existing is None:
        return []

    old_chunk_ids = [c.id for c in existing.chunks if c.id is not None]

    if vec_conn is not None:
        for cid in old_chunk_ids:
            vec_conn.execute("DELETE FROM vec_chunks WHERE rowid = ?", (cid,))
        vec_conn.commit()

    await session.execute(
        delete(RagChunk).where(RagChunk.document_id == existing.id)
    )
    await session.execute(
        delete(RagDocument).where(RagDocument.id == existing.id)
    )
    await session.commit()
    return old_chunk_ids


# ---------------------------------------------------------------------------
# Core ingest function
# ---------------------------------------------------------------------------

async def ingest_documents(
    embedder: Embedder,
    source_dir: Path | None = None,
    session_maker: async_sessionmaker | None = None,
    db_path: Path | None = None,
) -> dict:
    """
    Run the full ingest pipeline.

    Args:
        embedder: T6 Embedder instance for generating embeddings.
        source_dir: Optional override for the source documents directory.
        session_maker: Optional session maker (for testing). Uses default if None.
        db_path: Optional DB path for vector store (for testing). Uses default if None.

    Returns:
        Dict with stats: {docs_ingested, chunks_created, total_docs, total_chunks}

    Raises:
        OllamaUnavailableError: If Ollama is unreachable (no partial state).
    """
    raw_docs = _load_raw_documents(source_dir)
    if not raw_docs:
        return {"docs_ingested": 0, "chunks_created": 0, "total_docs": 0, "total_chunks": 0}

    chunker = SemanticChunker(embedder=embedder, chunk_size=512, overlap=50)

    # Use provided or default session maker / db path
    if session_maker is not None and db_path is not None:
        sm = session_maker
        dp = db_path
    else:
        dp = PROJECT_ROOT / "data" / "jp_drivers.sqlite"
        db_url = f"sqlite+aiosqlite:///{dp}"
        engine = create_async_engine(db_url, echo=False)
        sm = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    docs_ingested = 0
    chunks_created = 0

    vec_rows: list[tuple[int, list[float]]] = []
    old_vec_rowids: list[int] = []

    pbar = tqdm(total=len(raw_docs), desc="Ingesting documents", unit="doc")
    async with sm() as session:
        for raw_doc in raw_docs:
            old_ids = await _delete_existing_doc(session, raw_doc.source_url, None)
            old_vec_rowids.extend(old_ids)

            chunks = await chunker.chunk(raw_doc.text)
            if not chunks:
                pbar.update(1)
                continue

            doc = RagDocument(
                source_url=raw_doc.source_url,
                title=raw_doc.title,
                doc_type=raw_doc.doc_type,
                raw_text=raw_doc.text,
            )
            session.add(doc)
            await session.flush()

            chunk_texts = [c.text for c in chunks]
            try:
                embeddings = await embedder.embed_batch(chunk_texts)
            except OllamaUnavailableError:
                pbar.close()
                await session.rollback()
                raise

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                rag_chunk = RagChunk(
                    document_id=doc.id,
                    chunk_text=chunk.text,
                    chunk_idx=i,
                )
                session.add(rag_chunk)
                await session.flush()
                vec_rows.append((rag_chunk.id, embedding))
                chunks_created += 1

            docs_ingested += 1
            pbar.update(1)

        await session.commit()
    pbar.close()

    # Phase 2: sync — upsert vectors (avoids aiosqlite lock conflict)
    vec_conn = _get_vec_conn(dp)
    try:
        vector_store = VectorStore(vec_conn)
        for rowid in old_vec_rowids:
            vector_store.delete_chunk(rowid)
        for rowid, embedding in vec_rows:
            vector_store.upsert_chunk(rowid=rowid, embedding=embedding)
    finally:
        vec_conn.close()

    # Get totals
    async with sm() as session:
        doc_count = (await session.execute(select(RagDocument))).scalars().all()
        chunk_count = (await session.execute(select(RagChunk))).scalars().all()

    return {
        "docs_ingested": docs_ingested,
        "chunks_created": chunks_created,
        "total_docs": len(doc_count),
        "total_chunks": len(chunk_count),
    }
