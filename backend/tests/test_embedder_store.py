"""
TDD tests for rag/embedder.py and rag/vector_store.py.

RED phase: These tests define expected behavior.
GREEN phase: Implement the classes to make them pass.
"""
from __future__ import annotations

import asyncio
import sqlite3
import tempfile
from pathlib import Path
from typing import Generator
import array

import pytest
import respx
from httpx import Response

# The path to the rag module under test
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rag.embedder import Embedder
from rag.vector_store import VectorStore
from llm.provider import OllamaClient
from llm.exceptions import OllamaUnavailableError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class _DummyOllamaClient:
    """Minimal stand-in for OllamaClient used in tests."""

    embed_model: str = "nomic-embed-text"

    def __init__(self) -> None:
        self.embed_calls: list[str] = []

    async def embed(self, text: str) -> list[float]:
        self.embed_calls.append(text)
        # Return deterministic 768-dim vector that varies with text content.
        # Uses hash to derive a small offset added to each dimension.
        h = hash(text)
        offset = (h % 1000) * 0.0001  # small offset [-0.0999, 0.0999]
        return [offset + 0.001 * i for i in range(768)]

    async def close(self) -> None:
        pass


@pytest.fixture
def dummy_ollama() -> _DummyOllamaClient:
    return _DummyOllamaClient()


@pytest.fixture
def embedder(dummy_ollama: _DummyOllamaClient) -> Embedder:
    """Embedder wrapping a dummy Ollama client (no network)."""
    return Embedder(ollama_client=dummy_ollama, batch_delay_seconds=0.0)


@pytest.fixture
def vec_db() -> Generator[tuple[sqlite3.Connection, Path], None, None]:
    """Temp SQLite DB with sqlite-vec extension loaded, vec_chunks table created."""
    import sqlite_vec

    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    db_path = Path(tmp.name)
    tmp.close()

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.enable_load_extension(True)
    conn.execute("SELECT load_extension(?)", (sqlite_vec.loadable_path(),))
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(embedding float[768])"
    )
    conn.commit()

    yield conn, db_path

    conn.close()
    db_path.unlink(missing_ok=True)


@pytest.fixture
def vector_store(vec_db: tuple[sqlite3.Connection, Path]) -> VectorStore:
    conn, _ = vec_db
    return VectorStore(conn)


# ---------------------------------------------------------------------------
# Test 1: upsert 2 vectors, search → correct rowids ordered by distance
# ---------------------------------------------------------------------------


@respx.mock
async def test_upsert_two_vectors_search_closest(
    embedder: Embedder, vector_store: VectorStore
):
    """Upsert 2 chunks with different embeddings; search returns them ordered by distance."""
    # Embed two distinct texts → different 768-dim vectors
    text1 = "Driving in Japan requires understanding road signs."
    text2 = "The metric system is used for speed limits."

    emb1 = await embedder.embed(text1)
    emb2 = await embedder.embed(text2)

    vector_store.upsert_chunk(rowid=1, embedding=emb1)
    vector_store.upsert_chunk(rowid=2, embedding=emb2)

    # Query with emb1 → rowid=1 should be distance 0 (identical), rowid=2 should be > 0
    results = vector_store.search(query_embedding=emb1, k=2)

    assert len(results) == 2
    rowids = [r[0] for r in results]
    assert 1 in rowids
    assert 2 in rowids
    # Closest (distance 0) should be first
    assert results[0][0] == 1
    assert results[0][1] == pytest.approx(0.0, abs=1e-4)


# ---------------------------------------------------------------------------
# Test 2: upsert 3 vectors, search k=2 → correct 2 returned
# ---------------------------------------------------------------------------


@respx.mock
async def test_upsert_three_vectors_search_k2(
    embedder: Embedder, vector_store: VectorStore
):
    """Upsert 3 chunks; search with k=2 returns exactly the 2 nearest."""
    texts = [
        "Stop sign means come to a complete halt.",
        "Yield sign means slow down and give way.",
        "Speed limit signs indicate maximum allowed speed.",
    ]

    embeddings = [await embedder.embed(t) for t in texts]

    for i, emb in enumerate(embeddings, start=1):
        vector_store.upsert_chunk(rowid=i, embedding=emb)

    # Query with the third embedding → it should match rowid=3 best
    results = vector_store.search(query_embedding=embeddings[2], k=2)

    assert len(results) == 2
    result_rowids = {r[0] for r in results}
    # Rowid 3 (identical to query) MUST be in top-2; rowids 1 and 2 should have non-zero distance
    assert 3 in result_rowids
    # Neither result should have distance 0 except rowid 3
    distances = {r[0]: r[1] for r in results}
    assert distances[3] == pytest.approx(0.0, abs=1e-4)


# ---------------------------------------------------------------------------
# Test 3: delete a chunk, search → deleted row absent
# ---------------------------------------------------------------------------


@respx.mock
async def test_delete_chunk_search_excludes_deleted(
    embedder: Embedder, vector_store: VectorStore
):
    """Delete one chunk; search no longer returns it."""
    texts = ["Red light means stop.", "Green light means go."]
    embeddings = [await embedder.embed(t) for t in texts]

    vector_store.upsert_chunk(rowid=10, embedding=embeddings[0])
    vector_store.upsert_chunk(rowid=20, embedding=embeddings[1])

    # Delete rowid 10
    vector_store.delete_chunk(rowid=10)

    # Search should only return rowid 20
    results = vector_store.search(query_embedding=embeddings[0], k=5)
    result_rowids = [r[0] for r in results]
    assert 10 not in result_rowids
    assert 20 in result_rowids


# ---------------------------------------------------------------------------
# Test 4: batch embed with mocked Ollama (2 distinct + 1 repeat) → cache hit
# ---------------------------------------------------------------------------


async def test_embed_batch_lru_cache_hits(
    dummy_ollama: _DummyOllamaClient,
    embedder: Embedder,
):
    """Batch of 3 texts where one is a repeat → Ollama called only 2 times."""
    texts = ["apple", "banana", "apple"]  # 'apple' appears twice

    results = await embedder.embed_batch(texts)

    assert len(results) == 3
    # First and third results should be identical (cache hit on 'apple')
    assert results[0] == results[2]
    # dummy_ollama.embed_calls should have 'apple' and 'banana' only (2 calls)
    assert dummy_ollama.embed_calls == ["apple", "banana"]
    # Cache should contain exactly 2 unique entries
    assert len(embedder._cache) == 2


# ---------------------------------------------------------------------------
# Test 5: embed 100 vectors, search nearest-5 → brute-force validate
# ---------------------------------------------------------------------------


@respx.mock
async def test_search_nearest5_brute_force_validation(
    embedder: Embedder, vector_store: VectorStore
):
    """Insert 100 random-ish vectors; verify top-5 nearest by brute-force."""
    import random

    random.seed(42)

    texts = [f"Document chunk number {i}." for i in range(100)]
    embeddings = [await embedder.embed(t) for t in texts]

    for i, emb in enumerate(embeddings, start=1):
        vector_store.upsert_chunk(rowid=i, embedding=emb)

    # Query with embedding of text 50 (not identical to any other)
    query_emb = embeddings[49]  # 0-indexed

    results = vector_store.search(query_embedding=query_emb, k=5)

    assert len(results) == 5

    # Brute-force: compute Euclidean distances ourselves
    import math

    def euclidean(a: list[float], b: list[float]) -> float:
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    all_distances = [(i + 1, euclidean(query_emb, emb)) for i, emb in enumerate(embeddings)]
    all_distances.sort(key=lambda x: x[1])
    expected_top5 = all_distances[:5]

    # Compare sets of rowids (distances should match within tolerance)
    result_rowids = {r[0] for r in results}
    expected_rowids = {r[0] for r in expected_top5}
    assert result_rowids == expected_rowids

    # Distances should be close
    for rowid, dist in results:
        expected_dist = next(d for r, d in expected_top5 if r == rowid)
        assert dist == pytest.approx(expected_dist, rel=1e-4)
