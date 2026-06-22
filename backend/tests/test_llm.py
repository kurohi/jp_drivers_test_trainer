"""TDD tests for LLM provider — RED phase (provider does not exist yet)."""

import pytest
import respx
from httpx import ConnectError, Response

from src.config import Settings
from src.llm.exceptions import OllamaResponseError, OllamaUnavailableError
from src.llm.provider import OllamaClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def settings() -> Settings:
    return Settings(
        ollama_url="http://localhost:11434",
        ollama_chat_model="qwen3.6-256k",
        ollama_embed_model="nomic-embed-text",
        ollama_timeout_seconds=60.0,
    )


@pytest.fixture
def client(settings: Settings) -> OllamaClient:
    return OllamaClient(settings)


# ---------------------------------------------------------------------------
# Test 1: Chat happy path
# ---------------------------------------------------------------------------


@respx.mock
async def test_chat_happy_path(client: OllamaClient):
    """POST /api/chat returns model response as a string."""
    respx.post("http://localhost:11434/api/chat").mock(
        return_value=Response(
            200,
            json={
                "message": {
                    "role": "assistant",
                    "content": "危険物取扱者は、公安机关が交付する危険物取扱者可免状が必要です。",
                }
            },
        ),
    )

    result = await client.chat(
        messages=[{"role": "user", "content": "危険物取扱者の免状は誰が交付しますか？"}],
        temperature=0.3,
        num_predict=2000,
    )

    assert isinstance(result, str)
    assert "危険物取扱者可免状" in result


# ---------------------------------------------------------------------------
# Test 2: Chat think-block stripping
# ---------------------------------------------------------------------------


@respx.mock
async def test_chat_thinks_block_stripped(client: OllamaClient):
    """境外 blocks are stripped from the response content."""
    respx.post("http://localhost:11434/api/chat").mock(
        return_value=Response(
            200,
            json={
                "message": {
                    "role": "assistant",
                    "content": "<think>\n"
                    "Let me think about this question carefully.\n"
                    "The answer involves Article 44 of the Road Traffic Act.\n"
                    "</think>\n"
                    "答えは表議決之手続により行った後に交付されます。",
                }
            },
        ),
    )

    result = await client.chat(
        messages=[{"role": "user", "content": "仮免状はいつまで有効ですか？"}],
    )

    # The境外 block should be removed
    assert "<think>" not in result
    assert "</think>" not in result
    assert "答えは表議決之手続により行った後に交付されます。" in result


# ---------------------------------------------------------------------------
# Test 3: Embed returns 768-dim float list
# ---------------------------------------------------------------------------


@respx.mock
async def test_embed_returns_768_floats(client: OllamaClient):
    """POST /api/embeddings returns a 768-element float list (nomic-embed-text)."""
    embedding = [0.0123 * i for i in range(768)]
    respx.post("http://localhost:11434/api/embeddings").mock(
        return_value=Response(200, json={"embedding": embedding}),
    )

    result = await client.embed(text="日本の信号機の色順序")

    assert isinstance(result, list)
    assert len(result) == 768
    assert all(isinstance(x, float) for x in result)
    assert result[0] == pytest.approx(0.0)
    assert result[767] == pytest.approx(0.0123 * 767)


# ---------------------------------------------------------------------------
# Test 4: 5xx errors retry twice then raise OllamaResponseError
# ---------------------------------------------------------------------------


@respx.mock
async def test_5xx_retries_twice_then_raises(client: OllamaClient):
    """Transient 5xx errors are retried with backoff; after 2 retries raise OllamaResponseError."""
    call_count = 0

    def _five_xx(request):
        nonlocal call_count
        call_count += 1
        return Response(503, json={"error": "model not loaded"})

    respx.post("http://localhost:11434/api/chat").mock(side_effect=_five_xx)

    with pytest.raises(OllamaResponseError) as exc_info:
        await client.chat(messages=[{"role": "user", "content": "hello"}])

    assert call_count == 3  # initial + 2 retries
    assert "503" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test 5: ConnectError → OllamaUnavailableError
# ---------------------------------------------------------------------------


@respx.mock
async def test_connect_error_raises_ollama_unavailable(client: OllamaClient):
    """httpx.ConnectError is wrapped as OllamaUnavailableError."""
    # Simulate a host that refuses connections
    respx.post("http://localhost:11434/api/chat").mock(
        side_effect=ConnectError("Connection refused"),
    )

    with pytest.raises(OllamaUnavailableError) as exc_info:
        await client.chat(messages=[{"role": "user", "content": "hello"}])

    assert "ConnectError" in str(exc_info.value) or "Connection refused" in str(
        exc_info.value
    )
