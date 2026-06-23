/**
 * RAG Teacher API client.
 *
 * In mock mode (VITE_API_MOCK=true), returns mock data.
 * In live mode, POSTs to /api/rag/ask via the /api proxy.
 */

import type { RagQueryIn, RagAnswerOut } from "@/types";
import { mockRagAnswer, mockRagRefusal } from "./mock-extended";
import { request, ApiError, type RagApiError } from "./fetch";

const isMock = import.meta.env.VITE_API_MOCK === "true";

/** Simulate network latency for mock mode. */
function delay<T>(value: T, ms = 400): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

/** Keywords that are out-of-scope for the RAG teacher (mock refusal logic). */
const outOfScopeKeywords = [
  "weather", "recipe", "movie", "game", "sport", "politics",
  "celebrity", "music", "travel", "shopping", "cooking", "fashion",
];

export const ragApi = {
  /**
   * Ask the RAG teacher a question.
   * Returns RagAnswerOut with answer text and sources.
   * Returns refusal (sources=[]) for out-of-scope questions.
   * Throws RagApiError on HTTP 503 (Ollama down).
   */
  async ask(query: RagQueryIn): Promise<RagAnswerOut> {
    if (isMock) {
      const lowerQ = query.question.toLowerCase();
      const isOutOfScope = outOfScopeKeywords.some((kw) =>
        lowerQ.includes(kw),
      );
      return delay(isOutOfScope ? mockRagRefusal : mockRagAnswer);
    }

    try {
      return await request<RagAnswerOut>("/api/rag/ask", {
        method: "POST",
        body: JSON.stringify(query),
      });
    } catch (e) {
      if (e instanceof ApiError && e.status === 503) {
        const ragError: RagApiError = {
          status: 503,
          detail: (e.detail as RagApiError["detail"]) || { error: "ollama_unavailable" },
        };
        throw ragError;
      }
      throw e;
    }
  },
};