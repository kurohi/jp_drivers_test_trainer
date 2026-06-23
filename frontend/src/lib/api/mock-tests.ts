import type {
  AttemptStartIn,
  AttemptSubmitIn,
  AttemptResultOut,
  QuestionListItem,
} from "@/types";
import {
  mockStartAttempt,
  mockSubmitAttempt,
  mockGetTimeout,
  mockGetCorrectAnswers,
  type MockTestTimeoutResponse,
} from "./mock";
import { request } from "./fetch";

const isMock = import.meta.env.VITE_API_MOCK === "true";

function delay<T>(value: T, ms = 200): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

export interface MockTestStartResult {
  attempt_id: number;
  questions: QuestionListItem[];
  time_limit_seconds: number;
}

export const mockTestsApi = {
  async start(payload: AttemptStartIn): Promise<MockTestStartResult> {
    if (isMock) {
      const result = mockStartAttempt(payload);
      return delay(result, 300);
    }

    return request<MockTestStartResult>("/api/mock-tests", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async submit(
    attemptId: number,
    payload: AttemptSubmitIn,
  ): Promise<AttemptResultOut> {
    if (isMock) {
      const result = mockSubmitAttempt(attemptId, payload);
      if (!result) throw new Error("Attempt not found");
      return delay(result, 400);
    }

    return request<AttemptResultOut>(`/api/mock-tests/${attemptId}/submit`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getTimeout(attemptId: number): Promise<MockTestTimeoutResponse> {
    if (isMock) {
      const result = mockGetTimeout(attemptId);
      if (!result) throw new Error("Attempt not found");
      return delay(result, 100);
    }

    const data = await request<{ remaining_seconds: number; expired: boolean }>(
      `/api/mock-tests/${attemptId}/timeout`,
    );
    return { remaining_seconds: data.remaining_seconds, timed_out: data.expired };
  },

  getCorrectAnswers(
    attemptId: number,
  ): Record<number, "true" | "false"> | null {
    if (isMock) {
      return mockGetCorrectAnswers(attemptId);
    }
    return null;
  },
};