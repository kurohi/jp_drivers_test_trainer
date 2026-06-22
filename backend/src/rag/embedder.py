"""
Async Embedder wrapping OllamaClient.embed() with an LRU cache.

Design decisions:
- LRU cache uses a simple dict with manual pruning at maxsize=512.
  Cache key is hash(text) so re-embedding the same string returns cached list.
- Batch embedding applies an optional asyncio.sleep delay between calls
  (configurable via batch_delay_seconds).
- embedder is async; VectorStore is sync — bridge in service layer with asyncio.to_thread.
"""
from __future__ import annotations

import asyncio
import hashlib
from collections import OrderedDict
from typing import Protocol, TypeVar

T = TypeVar("T")


class OllamaEmbedder(Protocol):
    """Protocol for an Ollama client that can embed text."""

    async def embed(self, text: str) -> list[float]:
        """Return a 768-dim embedding for the given text."""
        ...


# ---------------------------------------------------------------------------
# LRU cache implementation
# ---------------------------------------------------------------------------

LRU_MAXSIZE = 512


class _LRUCache:
    """Simple LRU cache keyed by hash(text) → embedding list[float].

    Uses OrderedDict for O(1) move-to-end on access and eviction of oldest.
    """

    def __init__(self, maxsize: int = LRU_MAXSIZE) -> None:
        self._data: OrderedDict[int, list[float]] = OrderedDict()
        self._maxsize = maxsize

    def get(self, key: int) -> list[float] | None:
        """Return cached value and move to end (most-recently-used)."""
        if key not in self._data:
            return None
        # Move to end to mark as recently used
        self._data.move_to_end(key)
        return self._data[key]

    def set(self, key: int, value: list[float]) -> None:
        """Store value; evict oldest entry if at capacity."""
        if key in self._data:
            self._data.move_to_end(key)
            self._data[key] = value
            return
        if len(self._data) >= self._maxsize:
            # Pop oldest (first) entry
            self._data.popitem(last=False)
        self._data[key] = value

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: int) -> bool:
        return key in self._data


# ---------------------------------------------------------------------------
# Embedder
# ---------------------------------------------------------------------------


class Embedder:
    """
    Async text embedder with LRU cache.

    Wraps an OllamaClient (or any object implementing OllamaEmbedder) and
    adds caching to avoid redundant embed calls for identical text.

    Args:
        ollama_client: The underlying Ollama client to delegate to.
        batch_delay_seconds: Delay (in seconds) between each embed call in
            embed_batch to respect rate limits. Set to 0 to disable.
    """

    def __init__(
        self,
        ollama_client: OllamaEmbedder,
        batch_delay_seconds: float = 0.1,
    ) -> None:
        self._client = ollama_client
        self._batch_delay = batch_delay_seconds
        self._cache = _LRUCache(maxsize=LRU_MAXSIZE)

    @staticmethod
    def _text_hash(text: str) -> int:
        """Stable hash of text for cache key (hash is platform-dependent)."""
        # Use sha256 for deterministic cross-run key
        h = hashlib.sha256(text.encode("utf-8")).digest()
        return int.from_bytes(h[:8], byteorder="big", signed=False)

    async def embed(self, text: str) -> list[float]:
        """
        Embed a single text string.

        Args:
            text: Input text to embed.

        Returns:
            768-dim float list from the underlying Ollama embedder.
        """
        key = self._text_hash(text)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        result = await self._client.embed(text)
        self._cache.set(key, result)
        return result

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Embed multiple texts, respecting the configured batch delay.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of 768-dim embedding lists, one per input text.
        """
        results: list[list[float]] = []
        for i, text in enumerate(texts):
            results.append(await self.embed(text))
            if self._batch_delay > 0 and i < len(texts) - 1:
                await asyncio.sleep(self._batch_delay)
        return results
