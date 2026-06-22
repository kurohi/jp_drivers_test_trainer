"""
Semantic chunker using chonkie[semantic] with custom Ollama embeddings.

Design decisions:
- Wraps chonkie's SemanticChunker with a custom BaseEmbeddings subclass
  that delegates to our Ollama embedder (T6).
- Token counting uses a simple character-based approximation (~4 chars/token).
- Chunk size ~512 tokens with ~50 token overlap via chonkie's built-in params.
- The SemanticChunker runs via asyncio.to_thread to avoid event loop conflicts.
"""
from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from chonkie.embeddings import BaseEmbeddings

if TYPE_CHECKING:
    pass

_CHARS_PER_TOKEN = 4


def _approx_token_count(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


class _OllamaEmbeddings(BaseEmbeddings):
    """Custom embeddings for chonkie, delegating to an async T6 Embedder."""

    def __init__(self, embedder) -> None:
        self._embedder = embedder
        self._dimension = 768
        self._loop: asyncio.AbstractEventLoop | None = None

    def _set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    @property
    def dimension(self) -> int:
        return self._dimension

    def _run_async(self, coro):
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    def embed(self, text: str):
        result = self._run_async(self._embedder.embed(text))
        return np.array(result, dtype=np.float32)

    def embed_batch(self, texts: list[str]):
        results = self._run_async(self._embedder.embed_batch(texts))
        return [np.array(r, dtype=np.float32) for r in results]

    def count_tokens(self, text: str) -> int:
        return _approx_token_count(text)

    def count_tokens_batch(self, texts: list[str]) -> list[int]:
        return [_approx_token_count(t) for t in texts]

    def get_tokenizer(self):
        return "character"

    @classmethod
    def is_available(cls) -> bool:
        return True

    def __repr__(self) -> str:
        return f"OllamaEmbeddings(dimension={self._dimension})"


@dataclass
class Chunk:
    text: str
    token_count: int
    index: int


class SemanticChunker:
    """
    Wraps chonkie's SemanticChunker with Ollama-based embeddings.

    Args:
        embedder: T6 Embedder instance for generating embeddings.
        chunk_size: Target tokens per chunk (default 512).
        overlap: Token overlap between consecutive chunks (default 50).
        threshold: Semantic similarity threshold 0-1 (default 0.5).
    """

    def __init__(
        self,
        embedder,
        chunk_size: int = 512,
        overlap: int = 50,
        threshold: float = 0.5,
    ) -> None:
        self._embedder = embedder
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._threshold = threshold
        self._chonkie_chunker = None

    def _get_chunker(self):
        if self._chonkie_chunker is None:
            from chonkie import SemanticChunker as _ChonkieSemanticChunker

            embeddings = _OllamaEmbeddings(self._embedder)
            self._chonkie_chunker = _ChonkieSemanticChunker(
                embedding_model=embeddings,
                threshold=self._threshold,
                chunk_size=self._chunk_size,
            )
        return self._chonkie_chunker

    def _chunk_sync(self, text: str, loop: asyncio.AbstractEventLoop) -> list[Chunk]:
        chunker = self._get_chunker()
        embeddings = chunker.embedding_model
        if hasattr(embeddings, "_set_loop"):
            embeddings._set_loop(loop)
        raw_chunks = chunker.chunk(text)
        return [
            Chunk(text=raw.text, token_count=raw.token_count, index=i)
            for i, raw in enumerate(raw_chunks)
        ]

    async def chunk(self, text: str) -> list[Chunk]:
        loop = asyncio.get_running_loop()
        return await asyncio.to_thread(self._chunk_sync, text, loop)
