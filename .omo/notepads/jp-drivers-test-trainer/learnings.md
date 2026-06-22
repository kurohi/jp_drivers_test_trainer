# JP Drivers Test Trainer — Learnings

## T10: RAG Chunking + Ingest Pipeline (2026-06-23)

### What was built
- `backend/src/rag/chunker.py` — SemanticChunker wrapping chonkie[semantic] with custom Ollama embeddings
- `backend/src/rag/ingest.py` — Two-phase ingest pipeline (async ORM → sync vector store)
- `backend/scripts/ingest.py` — CLI with Ollama pre-flight check
- `data/rag_source_documents/{rule,explanation,skill}/stub_001.json` — 3 test documents
- `tests/test_ingest.py` — 4 TDD tests (row counts, idempotency, doc types, chunk references)

### Key technical decisions
- **Two-phase ingest**: Phase 1 (async) does chunking, embedding, ORM persistence. Phase 2 (sync) does vector store upserts. This avoids "database is locked" errors from aiosqlite + sync sqlite3 fighting over the same file.
- **chonkie BaseEmbeddings**: Custom `_OllamaEmbeddings` must inherit from `chonkie.embeddings.BaseEmbeddings` directly — `__bases__` monkey-patching fails due to C extension deallocator differences.
- **Async/sync bridge**: chonkie's SemanticChunker is sync but needs async embeddings. Solution: run chunker via `asyncio.to_thread()` and use `asyncio.run_coroutine_threadsafe()` in the embeddings class.
- **Tokenizer**: `get_tokenizer()` must return `"character"` not `None` — chonkie's AutoTokenizer rejects NoneType.
- **Lazy loading**: `RagDocument.chunks` uses `lazy="noload"` — must use `selectinload()` when querying for deletion during idempotent re-ingest.
- **Event loop in threads**: `asyncio.get_event_loop()` fails in worker threads — must pass `asyncio.get_running_loop()` from the async context to the thread.

### Dependencies
- Added `chonkie[semantic]>=0.5.0` to pyproject.toml
- Uses T6 Embedder + VectorStore, T8 RagDocument/RagChunk models

### Test results
- All 134 tests pass (4 new ingest tests + 130 existing)
