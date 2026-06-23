"""RAG Teacher service — orchestrate retrieval, LLM generation, and answer parsing."""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.llm.exceptions import OllamaUnavailableError
from src.llm.prompts import RAG_TEACHER_SYSTEM, RAG_TEACHER_USER_TEMPLATE
from src.llm.answer_parser import parse_rag_answer
from src.llm.provider import OllamaClient
from src.rag.retriever import Retriever, RetrievedChunk
from src.schemas.rag import RagAnswerOut, RagSourceOut

if TYPE_CHECKING:
    pass

# Refusal message when no relevant chunks are found
REFUSAL_MESSAGE = (
    "I cannot answer that — please check that your question relates to "
    "the JP driver's test."
)


class RagTeacherService:
    """Orchestrates RAG retrieval → LLM generation → structured answer.

    Args:
        retriever: The Retriever instance for fetching relevant chunks.
        ollama_client: OllamaClient for chat completions.
        min_distance: Maximum Euclidean distance threshold for chunk relevance.
    """

    def __init__(
        self,
        retriever: Retriever,
        ollama_client: OllamaClient,
        min_distance: float = 0.2,
    ) -> None:
        self._retriever = retriever
        self._ollama_client = ollama_client
        self._min_distance = min_distance

    async def ask(
        self,
        question: str,
        language: str = "en",
        k: int = 5,
    ) -> RagAnswerOut:
        """Answer a user question using RAG over the JP driver's test corpus.

        Args:
            question: The user's question.
            language: "en" or "pt" — passed to the LLM for response language.
            k: Number of chunks to retrieve.

        Returns:
            RagAnswerOut with answer text and source citations.

        Raises:
            OllamaUnavailableError: When Ollama cannot be reached.
        """
        # Step 1: Retrieve relevant chunks
        retrieved = await self._retriever.retrieve(
            query=question, k=k, min_distance=self._min_distance
        )

        # Step 2: Refusal if nothing relevant found
        if not retrieved:
            return RagAnswerOut(answer=REFUSAL_MESSAGE, sources=[])

        # Step 3: Build context block with index labels
        context_block = self._build_context_block(retrieved)

        # Step 4: Build chunk_pool for source resolution (index → RagSourceOut)
        chunk_pool = self._build_chunk_pool(retrieved)

        # Step 5: Build messages for the LLM
        system_prompt = RAG_TEACHER_SYSTEM
        user_prompt = RAG_TEACHER_USER_TEMPLATE.format(
            context_block=context_block,
            user_question=question,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Step 6: Call Ollama
        try:
            raw_answer = await self._ollama_client.chat(
                messages=messages,
                temperature=0.3,
                num_predict=2000,
            )
        except OllamaUnavailableError:
            raise

        # Step 7: Parse the answer
        return parse_rag_answer(raw_answer, chunk_pool)

    @staticmethod
    def _build_context_block(retrieved: list[RetrievedChunk]) -> str:
        """Build a numbered context block from retrieved chunks.

        Format:
        [0] (from: Title) — chunk text
        [1] (from: Title) — chunk text
        ...
        """
        lines = []
        for i, item in enumerate(retrieved):
            title = item.document.title
            text = item.chunk.chunk_text
            lines.append(f"[{i}] (from: {title})\n{text}")
        return "\n\n".join(lines)

    @staticmethod
    def _build_chunk_pool(
        retrieved: list[RetrievedChunk],
    ) -> dict[int, RagSourceOut]:
        """Build a mapping of chunk index → RagSourceOut for source resolution."""
        pool: dict[int, RagSourceOut] = {}
        for i, item in enumerate(retrieved):
            pool[i] = RagSourceOut(
                source_url=item.document.source_url or "",
                title=item.document.title,
                snippet=item.chunk.chunk_text[:200],
            )
        return pool
