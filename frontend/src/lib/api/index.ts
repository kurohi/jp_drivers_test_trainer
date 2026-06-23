import { themesApi } from "./themes";
import { questionsApi } from "./questions";
import { ragApi } from "./rag";
import { skillApi } from "./skill";
import { studyPlanApi } from "./study-plans";
import { mockTestsApi } from "./mock-tests";
import { liveApi } from "./fetch";

const isMock = import.meta.env.VITE_API_MOCK === "true";

/**
 * Unified API client.
 *
 * When VITE_API_MOCK=true  → returns data from mock.ts (offline/CI mode)
 * When VITE_API_MOCK=false → fetches from the live backend at :8000
 */
export const api = isMock
  ? {
      themes: themesApi,
      questions: questionsApi,
      rag: ragApi,
      skill: skillApi,
      studyPlans: studyPlanApi,
      mockTests: mockTestsApi,
    }
  : liveApi;
