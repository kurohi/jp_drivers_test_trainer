"""
Sync VectorStore wrapping sqlite-vec (vec0) virtual table operations.

Design decisions:
- Requires a sqlite3.Connection with sqlite-vec extension already loaded.
  If vec_chunks table is not found, raises VectorStoreError.
- All operations are synchronous (sqlite-vec is a C extension, not async-safe).
- Bridge to async embedder via asyncio.to_thread in the service layer.
"""
from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class VectorStoreError(Exception):
    """Raised when VectorStore encounters a sqlite-vec operational error."""


class VectorStore:
    """
    Sync sqlite-vec wrapper for the vec_chunks virtual table.

    Args:
        conn: A sqlite3.Connection with sqlite-vec loaded and vec_chunks
            virtual table present.

    Raises:
        VectorStoreError: If the connection is invalid or vec_chunks is missing.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

        # Verify vec_chunks exists by checking the sqlite_master table
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='vec_chunks'"
        )
        if cur.fetchone() is None:
            raise VectorStoreError(
                "vec_chunks virtual table not found. "
                "Ensure sqlite_vec extension is loaded and the table exists."
            )

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def upsert_chunk(self, rowid: int, embedding: list[float]) -> None:
        """
        Insert or replace a vector for the given rowid.

        Args:
            rowid: Integer identifier (maps to rag_chunks.id).
            embedding: 768-dim float list (nomic-embed-text dimension).

        Raises:
            VectorStoreError: On sqlite-vec insert failure.
        """
        # sqlite-vec expects embedding as a compact blob (Float32Array)
        embedding_blob = embedding_to_blob(embedding)

        # Use INSERT OR REPLACE — sqlite-vec handles REPLACE as delete + insert
        # on virtual tables (which is why we don't just INSERT)
        try:
            self._conn.execute(
                "INSERT OR REPLACE INTO vec_chunks(rowid, embedding) VALUES (?, ?)",
                (rowid, embedding_blob),
            )
            self._conn.commit()
        except sqlite3.Error as e:
            raise VectorStoreError(f"upsert_chunk failed: {e}") from e

    def search(
        self, query_embedding: list[float], k: int = 5
    ) -> list[tuple[int, float]]:
        """
        Find the k nearest vectors to the query embedding (Euclidean distance).

        Args:
            query_embedding: 768-dim query vector.
            k: Maximum number of results to return (default 5).

        Returns:
            List of (rowid, distance) tuples ordered by ascending distance.

        Raises:
            VectorStoreError: On sqlite-vec search failure.
        """
        query_blob = embedding_to_blob(query_embedding)
        try:
            cur = self._conn.execute(
                "SELECT rowid, distance FROM vec_chunks "
                "WHERE embedding MATCH ? ORDER BY distance LIMIT ?",
                (query_blob, k),
            )
            rows = cur.fetchall()
            return [(int(rowid), float(distance)) for rowid, distance in rows]
        except sqlite3.Error as e:
            raise VectorStoreError(f"search failed: {e}") from e

    def delete_chunk(self, rowid: int) -> None:
        """
        Delete the vector for the given rowid.

        Args:
            rowid: Integer identifier of the chunk to delete.

        Raises:
            VectorStoreError: On sqlite delete failure.
        """
        try:
            self._conn.execute("DELETE FROM vec_chunks WHERE rowid = ?", (rowid,))
            self._conn.commit()
        except sqlite3.Error as e:
            raise VectorStoreError(f"delete_chunk failed: {e}") from e


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import array


def embedding_to_blob(embedding: list[float]) -> bytes:
    """
    Convert a 768-dim float list to a compact Float32 blob for sqlite-vec.

    sqlite-vec's MATCH operator reads the blob as a Float32Array.
    """
    arr = array.array("f", embedding)  # 'f' = float32
    return arr.tobytes()
