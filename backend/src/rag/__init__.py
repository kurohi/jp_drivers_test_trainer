"""RAG (Retrieval-Augmented Generation) module.

Components:
- Embedder: async wrapper around OllamaClient.embed() with LRU cache.
- VectorStore: sync sqlite-vec wrapper for upsert/search/delete on vec_chunks.
"""
from __future__ import annotations

from src.rag.embedder import Embedder
from src.rag.vector_store import VectorStore

__all__ = ["Embedder", "VectorStore"]
