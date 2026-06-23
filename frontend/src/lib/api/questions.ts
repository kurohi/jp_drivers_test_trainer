/**
 * Question API client.
 *
 * CRITICAL: QuestionListItem must NOT leak answer/explanation fields.
 * Only QuestionDetail (fetched on demand) contains answers.
 *
 * In mock mode (VITE_API_MOCK=true), returns data from mock.ts.
 * In live mode, fetches from the backend via the /api proxy.
 */

import type { QuestionListItem, QuestionDetail } from "@/types";
import {
  mockQuestionList,
  mockQuestionDetails,
  mockCountByTheme,
} from "./mock";
import { request } from "./fetch";

const isMock = import.meta.env.VITE_API_MOCK === "true";

/** Simulate network latency for mock mode. */
function delay<T>(value: T, ms = 200): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

export interface QuestionListResponse {
  items: QuestionListItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export const questionsApi = {
  /**
   * List questions for a theme with pagination.
   * Returns QuestionListItem[] — NO answer/explanation fields.
   */
  async listByTheme(
    themeId: number,
    page: number,
    pageSize: number,
  ): Promise<QuestionListResponse> {
    if (isMock) {
      const all = mockQuestionList.filter((q) => q.theme_id === themeId);
      const total = all.length;
      const totalPages = Math.max(1, Math.ceil(total / pageSize));
      const start = (page - 1) * pageSize;
      const items = all.slice(start, start + pageSize);
      return delay({
        items,
        total,
        page,
        pageSize,
        totalPages,
      });
    }

    const params = new URLSearchParams({
      theme_id: String(themeId),
      limit: String(pageSize),
      offset: String((page - 1) * pageSize),
    });
    const items = await request<QuestionListItem[]>(`/api/questions?${params}`);
    const total = mockCountByTheme(themeId);
    return {
      items,
      total,
      page,
      pageSize,
      totalPages: Math.max(1, Math.ceil(total / pageSize)),
    };
  },

  /**
   * Get a single question detail by ID.
   * This is the ONLY endpoint that returns answer/explanation fields.
   * Called on demand when user clicks "Show explanation".
   */
  async getById(questionId: number): Promise<QuestionDetail | null> {
    if (isMock) {
      const detail = mockQuestionDetails.get(questionId) ?? null;
      return delay(detail, 300); // slightly longer to simulate detail fetch
    }

    return request<QuestionDetail>(`/api/questions/${questionId}`);
  },
};