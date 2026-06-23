"""TDD tests for the RAG teacher endpoint — happy path, refusal, and 503."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.llm.exceptions import OllamaUnavailableError
from src.rag.embedder import Embedder
from src.rag.retriever import Retriever, RetrievedChunk
from src.schemas.rag import RagAnswerOut
from src.services.rag_teacher_service import RagTeacherService


# ---------------------------------------------------------------------------
# Fixtures — isolated test DB with RAG data
# ---------------------------------------------------------------------------

def _make_test_db(tmp_path: Path, seed_chunks: bool = True) -> Path:
    """Create a temp SQLite DB with RAG tables and optional seed data."""
    import sqlite_vec

    db_path = tmp_path / "test_rag.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.enable_load_extension(True)
    conn.load_extension(sqlite_vec.loadable_path())
    conn.execute("PRAGMA foreign_keys = ON")

    conn.execute("""
        CREATE TABLE rag_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url VARCHAR(500),
            title VARCHAR(300) NOT NULL,
            doc_type VARCHAR(20) NOT NULL,
            raw_text TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE rag_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL REFERENCES rag_documents(id),
            chunk_text TEXT NOT NULL,
            chunk_idx INTEGER NOT NULL DEFAULT 0,
            embedding_id VARCHAR(100)
        )
    """)
    conn.execute(
        "CREATE VIRTUAL TABLE vec_chunks USING vec0(embedding float[768])"
    )

    if seed_chunks:
        conn.execute(
            "INSERT INTO rag_documents (source_url, title, doc_type, raw_text) VALUES (?, ?, ?, ?)",
            (
                "https://test.example.com/rule/right-of-way",
                "Right of Way Rules",
                "rule",
                "In Japan, vehicles must follow specific right-of-way rules.",
            ),
        )
        doc_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.execute(
            "INSERT INTO rag_chunks (document_id, chunk_text, chunk_idx) VALUES (?, ?, ?)",
            (doc_id, "The vehicle approaching from the right has priority.", 0),
        )
        chunk_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        embedding_blob = b"\x00" * (768 * 4)
        conn.execute(
            "INSERT INTO vec_chunks (rowid, embedding) VALUES (?, ?)",
            (chunk_id, embedding_blob),
        )

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def seeded_db(tmp_path: Path) -> Path:
    return _make_test_db(tmp_path, seed_chunks=True)


@pytest.fixture
def empty_db(tmp_path: Path) -> Path:
    return _make_test_db(tmp_path, seed_chunks=False)


# ---------------------------------------------------------------------------
# Dummy Ollama client for tests
# ---------------------------------------------------------------------------

class _DummyOllamaClient:
    """Minimal stand-in for OllamaClient."""

    def __init__(self, embed_response: list[float] | None = None, chat_response: str | None = None):
        self._embed_response = embed_response or [0.0] * 768
        self._chat_response = chat_response or "Test answer.\n\nSources: [0]"
        self.embed_calls: list[str] = []
        self.chat_calls: list[dict] = []

    async def embed(self, text: str) -> list[float]:
        self.embed_calls.append(text)
        return self._embed_response

    async def chat(self, messages: list[dict], temperature: float = 0.3, num_predict: int = 2000) -> str:
        self.chat_calls.append({"messages": messages, "temperature": temperature})
        return self._chat_response

    async def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Test 1: Retriever returns chunks with sources
# ---------------------------------------------------------------------------

async def test_retriever_returns_chunks_with_sources(seeded_db: Path):
    """Retriever embeds query, searches vec, joins with ORM, returns RetrievedChunk."""
    import sqlite_vec

    def vec_factory():
        conn = sqlite3.connect(str(seeded_db))
        conn.enable_load_extension(True)
        conn.load_extension(sqlite_vec.loadable_path())
        return conn

    dummy_ollama = _DummyOllamaClient(embed_response=[0.0] * 768)
    embedder = Embedder(ollama_client=dummy_ollama, batch_delay_seconds=0.0)

    from models.rag_chunk import RagChunk, RagDocument

    mock_chunk = MagicMock(spec=RagChunk)
    mock_chunk.id = 1
    mock_chunk.chunk_text = "The vehicle approaching from the right has priority."
    mock_chunk.document_id = 1
    mock_chunk.chunk_idx = 0

    mock_doc = MagicMock(spec=RagDocument)
    mock_doc.id = 1
    mock_doc.source_url = "https://test.example.com/rule/right-of-way"
    mock_doc.title = "Right of Way Rules"
    mock_doc.doc_type = "rule"
    mock_doc.raw_text = "In Japan, vehicles must follow specific right-of-way rules."

    mock_chunk.document = mock_doc

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_chunk]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result

    retriever = Retriever(
        embedder=embedder,
        vec_conn_factory=vec_factory,
        session=mock_session,
    )

    results = await retriever.retrieve(query="right of way", k=5, min_distance=0.2)

    assert len(results) == 1
    assert results[0].distance == 0.0
    assert results[0].chunk.chunk_text == mock_chunk.chunk_text
    assert results[0].document.title == "Right of Way Rules"


# ---------------------------------------------------------------------------
# Test 2: Service happy path — returns RagAnswerOut with sources
# ---------------------------------------------------------------------------

async def test_service_happy_path():
    """RagTeacherService returns structured answer with sources."""
    from models.rag_chunk import RagChunk, RagDocument

    mock_chunk = MagicMock(spec=RagChunk)
    mock_chunk.id = 1
    mock_chunk.chunk_text = "The vehicle approaching from the right has priority."
    mock_chunk.document_id = 1

    mock_doc = MagicMock(spec=RagDocument)
    mock_doc.id = 1
    mock_doc.source_url = "https://test.example.com/rule/right-of-way"
    mock_doc.title = "Right of Way Rules"

    retrieved = [RetrievedChunk(chunk=mock_chunk, document=mock_doc, distance=0.05)]

    mock_retriever = AsyncMock()
    mock_retriever.retrieve.return_value = retrieved

    dummy_ollama = _DummyOllamaClient(
        chat_response="In Japan, right-of-way goes to the right.\n\nSources: [0]"
    )

    service = RagTeacherService(
        retriever=mock_retriever,
        ollama_client=dummy_ollama,
        min_distance=0.2,
    )

    result = await service.ask(question="Who has right of way?", language="en", k=5)

    assert isinstance(result, RagAnswerOut)
    assert "right-of-way" in result.answer.lower() or "right" in result.answer.lower()
    assert len(result.sources) == 1
    assert result.sources[0].title == "Right of Way Rules"
    assert result.sources[0].source_url == "https://test.example.com/rule/right-of-way"


# ---------------------------------------------------------------------------
# Test 3: Refusal — no relevant chunks returns refusal message
# ---------------------------------------------------------------------------

async def test_service_refusal_off_corpus():
    """When no chunks pass the distance threshold, return refusal."""
    mock_retriever = AsyncMock()
    mock_retriever.retrieve.return_value = []

    dummy_ollama = _DummyOllamaClient()

    service = RagTeacherService(
        retriever=mock_retriever,
        ollama_client=dummy_ollama,
        min_distance=0.2,
    )

    result = await service.ask(question="How to bake a cake?", language="en", k=5)

    assert isinstance(result, RagAnswerOut)
    assert "cannot answer" in result.answer.lower()
    assert result.sources == []
    assert len(dummy_ollama.chat_calls) == 0


# ---------------------------------------------------------------------------
# Test 4: Ollama down — service raises OllamaUnavailableError
# ---------------------------------------------------------------------------

async def test_service_ollama_down_raises():
    """When Ollama is unreachable, service propagates OllamaUnavailableError."""
    from models.rag_chunk import RagChunk, RagDocument

    mock_chunk = MagicMock(spec=RagChunk)
    mock_chunk.id = 1
    mock_chunk.chunk_text = "Some chunk text."
    mock_chunk.document_id = 1

    mock_doc = MagicMock(spec=RagDocument)
    mock_doc.id = 1
    mock_doc.source_url = "https://example.com"
    mock_doc.title = "Test Doc"

    retrieved = [RetrievedChunk(chunk=mock_chunk, document=mock_doc, distance=0.05)]

    mock_retriever = AsyncMock()
    mock_retriever.retrieve.return_value = retrieved

    mock_ollama = AsyncMock()
    mock_ollama.chat.side_effect = OllamaUnavailableError("Connection refused")

    service = RagTeacherService(
        retriever=mock_retriever,
        ollama_client=mock_ollama,
        min_distance=0.2,
    )

    with pytest.raises(OllamaUnavailableError):
        await service.ask(question="Right of way?", language="en", k=5)


# ---------------------------------------------------------------------------
# Test 5: Route 503 — Ollama down returns HTTP 503
# ---------------------------------------------------------------------------

async def test_route_ollama_down_returns_503():
    """When Ollama is unreachable, the route returns HTTP 503 with detail."""
    from fastapi.testclient import TestClient
    from src.main import app

    with patch("src.rag.embedder.Embedder.embed") as mock_embed:
        mock_embed.side_effect = OllamaUnavailableError("Connection refused")

        with TestClient(app) as client:
            resp = client.post(
                "/api/rag/ask",
                json={
                    "question": "Who has right of way?",
                    "language": "en",
                    "k": 5,
                },
            )

    assert resp.status_code == 503
    data = resp.json()
    assert "detail" in data
    detail = data["detail"]
    assert detail["error"] == "ollama_unavailable"
    assert "host" in detail
    assert "message" in detail
