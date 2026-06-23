/**
 * Study-plan API client.
 *
 * In mock mode (VITE_API_MOCK=true), returns mock data.
 * In live mode, fetches from the backend via the /api proxy.
 */

import type { StudyPlanGenerateIn, StudyPlanOut } from "@/types";
import {
  generateMockStudyPlan,
  mockStudyPlanHistory,
} from "./mock-extended";
import { request } from "./fetch";

const isMock = import.meta.env.VITE_API_MOCK === "true";

/** Simulate network latency for mock mode. */
function delay<T>(value: T, ms = 500): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

export const studyPlanApi = {
  /** Generate a new study plan. */
  async generate(input: StudyPlanGenerateIn): Promise<StudyPlanOut> {
    if (isMock) {
      return delay(generateMockStudyPlan(input.available_days));
    }

    return request<StudyPlanOut>("/api/study-plans/generate", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  /** Get study plan history. */
  async history(limit = 10): Promise<StudyPlanOut[]> {
    if (isMock) {
      return delay(mockStudyPlanHistory.slice(0, limit));
    }

    return request<StudyPlanOut[]>(`/api/study-plans/history?limit=${limit}`);
  },
};