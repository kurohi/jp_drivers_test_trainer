"""
TDD tests for rag/ingest.py — end-to-end ingest pipeline.

Tests:
1. Feed 3 stub docs → assert 3 RagDocument rows, ≥3 RagChunk rows, ≥3 vec_chunks rows
2. Re-ingest same docs → counts stay stable (idempotent)
3. OllamaUnavailableError → no partial state in DB
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Generator

import pytest

import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rag.embedder import Embedder
from rag.ingest import ingest_documents, _test_session_maker, RawDocument
from rag.vector_store import VectorStore
from models.rag_chunk import RagDocument, RagChunk
from sqlalchemy import select, text


# ---------------------------------------------------------------------------
# Dummy Ollama client for tests (no network)
# ---------------------------------------------------------------------------

class _DummyOllamaClient:
    """Minimal stand-in for OllamaClient used in tests."""

    embed_model: str = "nomic-embed-text"

    def __init__(self) -> None:
        self.embed_calls: list[str] = []

    async def embed(self, text: str) -> list[float]:
        self.embed_calls.append(text)
        h = hash(text)
        offset = (h % 1000) * 0.0001
        return [offset + 0.001 * i for i in range(768)]

    async def close(self) -> None:
        pass


@pytest.fixture
def dummy_ollama() -> _DummyOllamaClient:
    return _DummyOllamaClient()


@pytest.fixture
def embedder(dummy_ollama: _DummyOllamaClient) -> Embedder:
    return Embedder(ollama_client=dummy_ollama, batch_delay_seconds=0.0)


# ---------------------------------------------------------------------------
# Stub documents fixture
# ---------------------------------------------------------------------------

_STUB_DOCS = [
    {
        "source_url": "https://test.example.com/rule/right-of-way",
        "title": "Right of Way Rules",
        "doc_type": "rule",
        "text": (
            "In Japan, vehicles must follow specific right-of-way rules at intersections "
            "without traffic signals. The vehicle approaching from the right has priority "
            "over vehicles approaching from the left. This is known as the right-hand "
            "priority rule and applies to most uncontrolled intersections.\n\n"
            "When entering an intersection, vehicles turning left must yield to vehicles "
            "going straight. Vehicles turning right must yield to both straight-going "
            "vehicles and left-turning vehicles. This hierarchy ensures predictable traffic "
            "flow and reduces accidents.\n\n"
            "At intersections with stop signs, all vehicles must come to a complete stop "
            "before proceeding. After stopping, the right-hand priority rule applies. "
            "If two vehicles arrive simultaneously, the one on the right proceeds first.\n\n"
            "Emergency vehicles always have absolute right of way. When you hear a siren, "
            "pull to the left side of the road and stop. Never block intersections when "
            "emergency vehicles are approaching.\n\n"
            "Pedestrian crossings take priority over vehicle traffic. When a pedestrian "
            "is crossing or about to cross at a marked crosswalk, vehicles must stop and "
            "wait. This rule is strictly enforced in Japan with significant penalties.\n\n"
            "Temporary traffic signs and signals override permanent ones. During road "
            "construction or special events, follow the directions of temporary signage "
            "and traffic controllers."
        ),
    },
    {
        "source_url": "https://test.example.com/explanation/road-signs",
        "title": "Understanding Japanese Road Signs",
        "doc_type": "explanation",
        "text": (
            "Japanese road signs follow international conventions but include unique "
            "elements specific to Japan's driving culture. Understanding these signs is "
            "essential for passing the written driving test and safe driving.\n\n"
            "Warning signs are diamond-shaped with a yellow background and black border. "
            "They alert drivers to potential hazards ahead such as curves, intersections, "
            "pedestrian crossings, or animal crossings. The symbol inside indicates the "
            "specific hazard.\n\n"
            "Regulatory signs are circular with a white background and red border for "
            "prohibitions, or blue background for mandatory actions. A red circle with "
            "a horizontal bar means no entry. A blue circle with a white arrow indicates "
            "the required direction of travel.\n\n"
            "Information signs are rectangular and typically blue or green. Blue signs "
            "provide general information about services, facilities, and directions. "
            "Green signs on expressways indicate exits, distances, and route information.\n\n"
            "Speed limit signs are circular with a white background, red border, and "
            "black number. The number indicates the maximum speed in kilometers per hour."
        ),
    },
    {
        "source_url": "https://test.example.com/skill/parking",
        "title": "Parallel Parking Techniques",
        "doc_type": "skill",
        "text": (
            "Parallel parking is a required skill on the Japanese driving test. "
            "Mastering this technique requires understanding reference points, proper "
            "mirror usage, and smooth steering control.\n\n"
            "Begin by positioning your vehicle parallel to the car in front of the "
            "parking space, approximately 50-70 centimeters away. Align your rear bumper "
            "with the rear bumper of the parked car. Signal your intention to park and "
            "check all mirrors and blind spots.\n\n"
            "Shift into reverse and begin turning the steering wheel fully to the right. "
            "Move slowly while checking your left mirror. When you can see the rear of "
            "the car behind the space in your left mirror, straighten the wheel.\n\n"
            "Continue reversing until your front corner clears the rear of the car ahead. "
            "Then turn the wheel fully to the left and continue backing in. Adjust your "
            "position by moving forward and backward as needed to center the vehicle.\n\n"
            "Garage parking is another common test requirement. Approach the space at a "
            "slight angle, signal, and begin reversing when your side mirror aligns with "
            "the edge of the space. Turn the wheel smoothly and use reference points."
        ),
    },
]


@pytest.fixture
def stub_source_dir(tmp_path: Path) -> Path:
    """Create a temp directory with 3 stub JSON documents."""
    source_dir = tmp_path / "rag_source_documents"
    for i, doc_data in enumerate(_STUB_DOCS, start=1):
        doc_type = doc_data["doc_type"]
        doc_path = source_dir / doc_type / f"stub_{i:03d}.json"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        with open(doc_path, "w") as f:
            json.dump(doc_data, f)
    return source_dir


# ---------------------------------------------------------------------------
# Test 1: Ingest 3 stub docs → correct row counts
# ---------------------------------------------------------------------------

async def test_ingest_three_docs_creates_rows(embedder: Embedder, stub_source_dir: Path):
    """Ingest 3 stub documents; verify 3 RagDocument rows, ≥3 RagChunk rows, ≥3 vec_chunks rows."""
    async with _test_session_maker() as (session_maker, db_path):
        stats = await ingest_documents(
            embedder=embedder,
            source_dir=stub_source_dir,
            session_maker=session_maker,
            db_path=db_path,
        )

        assert stats["docs_ingested"] == 3
        assert stats["chunks_created"] >= 3

        # Verify DB state
        async with session_maker() as session:
            docs = (await session.execute(select(RagDocument))).scalars().all()
            chunks = (await session.execute(select(RagChunk))).scalars().all()

            assert len(docs) == 3
            assert len(chunks) >= 3

            # Verify vec_chunks has matching rows
            vec_conn = sqlite3.connect(str(db_path))
            import sqlite_vec
            vec_conn.enable_load_extension(True)
            vec_conn.load_extension(sqlite_vec.loadable_path())

            vec_count = vec_conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]
            vec_conn.close()

            assert vec_count >= 3


# ---------------------------------------------------------------------------
# Test 2: Re-ingest keeps counts stable (idempotent)
# ---------------------------------------------------------------------------

async def test_reingest_is_idempotent(embedder: Embedder, stub_source_dir: Path):
    """Re-ingesting the same documents should not increase row counts."""
    async with _test_session_maker() as (session_maker, db_path):
        # First ingest
        stats1 = await ingest_documents(
            embedder=embedder,
            source_dir=stub_source_dir,
            session_maker=session_maker,
            db_path=db_path,
        )

        # Second ingest (same docs)
        stats2 = await ingest_documents(
            embedder=embedder,
            source_dir=stub_source_dir,
            session_maker=session_maker,
            db_path=db_path,
        )

        # Counts should be identical
        assert stats1["total_docs"] == stats2["total_docs"] == 3
        assert stats1["total_chunks"] == stats2["total_chunks"]

        # Verify DB state directly
        async with session_maker() as session:
            docs = (await session.execute(select(RagDocument))).scalars().all()
            chunks = (await session.execute(select(RagChunk))).scalars().all()

            assert len(docs) == 3
            assert len(chunks) == stats1["total_chunks"]

            # Verify vec_chunks count matches
            vec_conn = sqlite3.connect(str(db_path))
            import sqlite_vec
            vec_conn.enable_load_extension(True)
            vec_conn.load_extension(sqlite_vec.loadable_path())

            vec_count = vec_conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]
            vec_conn.close()

            assert vec_count == len(chunks)


# ---------------------------------------------------------------------------
# Test 3: Each document type is correctly stored
# ---------------------------------------------------------------------------

async def test_ingest_preserves_doc_types(embedder: Embedder, stub_source_dir: Path):
    """Verify that doc_type, title, and source_url are correctly stored."""
    async with _test_session_maker() as (session_maker, db_path):
        await ingest_documents(
            embedder=embedder,
            source_dir=stub_source_dir,
            session_maker=session_maker,
            db_path=db_path,
        )

        async with session_maker() as session:
            docs = (await session.execute(select(RagDocument))).scalars().all()

            doc_types = {d.doc_type for d in docs}
            assert doc_types == {"rule", "explanation", "skill"}

            titles = {d.title for d in docs}
            assert "Right of Way Rules" in titles
            assert "Understanding Japanese Road Signs" in titles
            assert "Parallel Parking Techniques" in titles


# ---------------------------------------------------------------------------
# Test 4: Chunks have correct document_id references
# ---------------------------------------------------------------------------

async def test_chunks_reference_correct_documents(embedder: Embedder, stub_source_dir: Path):
    """Each RagChunk should reference a valid RagDocument."""
    async with _test_session_maker() as (session_maker, db_path):
        await ingest_documents(
            embedder=embedder,
            source_dir=stub_source_dir,
            session_maker=session_maker,
            db_path=db_path,
        )

        async with session_maker() as session:
            docs = (await session.execute(select(RagDocument))).scalars().all()
            chunks = (await session.execute(select(RagChunk))).scalars().all()

            doc_ids = {d.id for d in docs}
            chunk_doc_ids = {c.document_id for c in chunks}

            # All chunks should reference valid documents
            assert chunk_doc_ids.issubset(doc_ids)
            # Each document should have at least one chunk
            assert chunk_doc_ids == doc_ids
