import { create } from "zustand";
import type { QuestionListItem, AttemptResultOut } from "@/types";

interface MockTestState {
  attemptId: number | null;
  questions: QuestionListItem[];
  timeLimitSeconds: number;
  result: AttemptResultOut | null;
  setAttempt: (data: {
    attemptId: number;
    questions: QuestionListItem[];
    timeLimitSeconds: number;
  }) => void;
  setResult: (result: AttemptResultOut) => void;
  reset: () => void;
}

export const useMockTestStore = create<MockTestState>()((set) => ({
  attemptId: null,
  questions: [],
  timeLimitSeconds: 1800,
  result: null,
  setAttempt: (data) =>
    set({
      attemptId: data.attemptId,
      questions: data.questions,
      timeLimitSeconds: data.timeLimitSeconds,
      result: null,
    }),
  setResult: (result) => set({ result }),
  reset: () =>
    set({
      attemptId: null,
      questions: [],
      timeLimitSeconds: 1800,
      result: null,
    }),
}));