#!/usr/bin/env python3
"""
CLI script for the RAG ingest pipeline.

Usage:
    uv run python scripts/ingest.py

Checks Ollama availability before running. If Ollama is down, prints a
clear error and exits non-zero with no partial state in the database.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure src/ is on the path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import httpx
from config import Settings
from llm.exceptions import OllamaUnavailableError
from llm.provider import OllamaClient
from rag.embedder import Embedder
from rag.ingest import ingest_documents


def _check_ollama(settings: Settings) -> None:
    """
    Verify Ollama is reachable before starting ingest.

    Raises SystemExit with a clear message if Ollama is unavailable.
    """
    try:
        client = httpx.Client(timeout=5.0)
        response = client.get(f"{settings.ollama_url}/api/tags")
        response.raise_for_status()
    except httpx.ConnectError:
        print(
            f"ERROR: Cannot connect to Ollama at {settings.ollama_url}.\n"
            f"Please ensure Ollama is running: ollama serve\n"
            f"Aborting ingest — no data was modified.",
            file=sys.stderr,
        )
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(
            f"ERROR: Ollama returned HTTP {e.response.status_code}.\n"
            f"Aborting ingest — no data was modified.",
            file=sys.stderr,
        )
        sys.exit(1)


async def _main() -> None:
    settings = Settings()

    # Pre-flight check: Ollama must be reachable
    _check_ollama(settings)

    # Create Ollama client + embedder
    ollama = OllamaClient(settings)
    embedder = Embedder(ollama_client=ollama, batch_delay_seconds=0.0)

    try:
        print("Starting RAG ingest pipeline...")
        stats = await ingest_documents(embedder)
        print(f"Ingest complete:")
        print(f"  Documents ingested: {stats['docs_ingested']}")
        print(f"  Chunks created:     {stats['chunks_created']}")
        print(f"  Total documents:    {stats['total_docs']}")
        print(f"  Total chunks:       {stats['total_chunks']}")
    except OllamaUnavailableError as e:
        print(
            f"ERROR: Ollama became unavailable during ingest: {e}\n"
            f"Ingest aborted — no partial data was committed.",
            file=sys.stderr,
        )
        sys.exit(1)
    finally:
        await ollama.close()


if __name__ == "__main__":
    asyncio.run(_main())
