"""Ollama LLM client facade."""

import asyncio
import json
import re
from typing import Any

import httpx

from src.config import Settings
from src.llm.exceptions import OllamaResponseError, OllamaUnavailableError


class OllamaClient:
    """Async client for Ollama chat and embedding endpoints."""

    def __init__(self, settings: Settings):
        self.base_url = settings.ollama_url.rstrip("/")
        self.chat_model = settings.ollama_chat_model
        self.embed_model = settings.ollama_embed_model
        self.timeout = settings.ollama_timeout_seconds
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazily create and store a reusable AsyncClient."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    def _strip_think_blocks(self, content: str) -> str:
        return re.sub(
            r"\s*<think>.*?</think>",
            "",
            content,
            flags=re.DOTALL,
        ).strip()

    def _parse_ollama_response(self, body: str) -> str:
        try:
            data = json.loads(body)
            return data["message"]["content"]
        except json.JSONDecodeError:
            lines = [line for line in body.strip().split("\n") if line.strip()]
            last = json.loads(lines[-1])
            return last["message"]["content"]

    async def chat(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.3,
        num_predict: int = 2000,
    ) -> str:
        """Send a chat completion request to Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            temperature: Sampling temperature (default 0.3).
            num_predict: Max tokens to predict (default 2000).

        Returns:
            The assistant's response content as a string.

        Raises:
            OllamaUnavailableError: When the host cannot be reached.
            OllamaResponseError: When Ollama returns an error after retries.
        """
        payload = {
            "model": self.chat_model,
            "messages": messages,
            "temperature": temperature,
            "num_predict": num_predict,
            "stream": False,
        }

        last_error: Exception | None = None
        for attempt in range(3):
            if attempt > 0:
                await asyncio.sleep(0.5 * attempt)
            try:
                client = await self._get_client()
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                if response.status_code >= 500:
                    last_error = httpx.HTTPStatusError(
                        message=f"HTTP {response.status_code}",
                        response=response,
                        request=response.request,
                    )
                    continue
                response.raise_for_status()
                body = response.text
                content = self._parse_ollama_response(body)
                content = self._strip_think_blocks(content)
                return content
            except httpx.ConnectError as e:
                raise OllamaUnavailableError(
                    f"Cannot connect to Ollama at {self.base_url}: {e}"
                ) from e
            except httpx.HTTPStatusError as e:
                last_error = e
                continue
            except httpx.TimeoutException as e:
                raise OllamaResponseError(
                    f"Ollama timed out after {self.timeout}s: {e}"
                ) from e

        raise OllamaResponseError(
            f"Ollama returned error after retries: {last_error}"
        ) from last_error

    async def embed(self, text: str) -> list[float]:
        """Get a text embedding from Ollama (nomic-embed-text).

        Args:
            text: Input text to embed.

        Returns:
            A list of 768 floats (nomic-embed-text dimension).

        Raises:
            OllamaUnavailableError: When the host cannot be reached.
            OllamaResponseError: When Ollama returns an error after retries.
        """
        payload = {
            "model": self.embed_model,
            "prompt": text,
        }

        last_error: Exception | None = None
        for attempt in range(3):
            if attempt > 0:
                await asyncio.sleep(0.5 * attempt)
            try:
                client = await self._get_client()
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload,
                )
                if response.status_code >= 500:
                    last_error = httpx.HTTPStatusError(
                        message=f"HTTP {response.status_code}",
                        response=response,
                        request=response.request,
                    )
                    continue
                response.raise_for_status()
                data = response.json()
                return data["embedding"]
            except httpx.ConnectError as e:
                raise OllamaUnavailableError(
                    f"Cannot connect to Ollama at {self.base_url}: {e}"
                ) from e
            except httpx.HTTPStatusError as e:
                last_error = e
                continue
            except httpx.TimeoutException as e:
                raise OllamaResponseError(
                    f"Ollama timed out after {self.timeout}s: {e}"
                ) from e

        raise OllamaResponseError(
            f"Ollama embedding failed after retries: {last_error}"
        ) from last_error

    async def close(self):
        """Close the underlying HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
