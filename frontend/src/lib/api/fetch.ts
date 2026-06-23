import type {
  ThemeOut,
  QuestionListItem,
  QuestionDetail,
  AttemptStartIn,
  AttemptSubmitIn,
  AttemptResultOut,
  RagQueryIn,
  RagAnswerOut,
  SkillModuleOut,
  StudyPlanGenerateIn,
  StudyPlanOut,
} from "@/types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const mergedHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> | undefined),
  };
  if (!options?.body) {
    delete mergedHeaders["Content-Type"];
  }
  const res = await fetch(url, {
    ...options,
    headers: mergedHeaders,
  });

  if (res.status === 503) {
    const detail = await res.json().catch(() => ({}));
    throw new ApiError(503, "Service unavailable", detail);
  }

  if (res.status === 404) {
    return null as T;
  }

  if (!res.ok) {
    throw new ApiError(res.status, res.statusText);
  }

  const text = await res.text();
  if (!text) return null as T;
  return JSON.parse(text) as T;
}

export interface ThemeWithCount extends ThemeOut {
  question_count: number;
}

export interface QuestionListResponse {
  items: QuestionListItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface MockTestStartResult {
  attempt_id: number;
  questions: QuestionListItem[];
  time_limit_seconds: number;
}

export interface MockTestTimeoutResponse {
  remaining_seconds: number;
  timed_out: boolean;
}

export interface SkillModuleListItem {
  id: number;
  slug: string;
  name_en: string;
  name_pt: string;
  sort_order: number;
}

export interface RagApiError {
  status: number;
  detail: {
    error: string;
    host?: string;
    message?: string;
  };
}

export const liveApi = {
  themes: {
    async list(language?: string): Promise<ThemeWithCount[]> {
      const params = language ? `?language=${language}` : "";
      const themes = await request<ThemeOut[]>(`/api/themes${params}`);
      return themes.map((t) => ({ ...t, question_count: 0 }));
    },

    async getBySlug(slug: string): Promise<ThemeOut | null> {
      return request<ThemeOut>(`/api/themes/${slug}`);
    },
  },

  questions: {
    async listByTheme(
      themeId: number,
      page: number,
      pageSize: number,
      language?: string,
    ): Promise<QuestionListResponse> {
      const params = new URLSearchParams({
        theme_id: String(themeId),
        limit: String(pageSize),
        offset: String((page - 1) * pageSize),
      });
      if (language) params.set("language", language);
      const items = await request<QuestionListItem[]>(`/api/questions?${params}`);
      const total = items.length;
      return {
        items,
        total,
        page,
        pageSize,
        totalPages: Math.max(1, Math.ceil(total / pageSize)),
      };
    },

    async getById(questionId: number): Promise<QuestionDetail | null> {
      return request<QuestionDetail>(`/api/questions/${questionId}`);
    },
  },

  rag: {
    async ask(query: RagQueryIn): Promise<RagAnswerOut> {
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
  },

  skill: {
    async list(): Promise<SkillModuleListItem[]> {
      return request<SkillModuleListItem[]>("/api/skill-test/modules");
    },

    async getBySlug(slug: string): Promise<SkillModuleOut | null> {
      return request<SkillModuleOut>(`/api/skill-test/modules/${slug}`);
    },
  },

  studyPlans: {
    async generate(input: StudyPlanGenerateIn): Promise<StudyPlanOut> {
      return request<StudyPlanOut>("/api/study-plans/generate", {
        method: "POST",
        body: JSON.stringify(input),
      });
    },

    async history(limit = 10): Promise<StudyPlanOut[]> {
      return request<StudyPlanOut[]>(`/api/study-plans/history?limit=${limit}`);
    },
  },

  mockTests: {
    async start(payload: AttemptStartIn): Promise<MockTestStartResult> {
      const data = await request<{
        attempt_id: number;
        questions: QuestionListItem[];
        time_limit_seconds: number;
      }>("/api/mock-tests", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      return {
        attempt_id: data.attempt_id,
        questions: data.questions,
        time_limit_seconds: data.time_limit_seconds,
      };
    },

    async submit(
      attemptId: number,
      payload: AttemptSubmitIn,
    ): Promise<AttemptResultOut> {
      return request<AttemptResultOut>(`/api/mock-tests/${attemptId}/submit`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },

    async getTimeout(attemptId: number): Promise<MockTestTimeoutResponse> {
      const data = await request<{
        remaining_seconds: number;
        expired: boolean;
      }>(`/api/mock-tests/${attemptId}/timeout`);
      return {
        remaining_seconds: data.remaining_seconds,
        timed_out: data.expired,
      };
    },

    getCorrectAnswers(
      _attemptId: number,
    ): Record<number, "true" | "false"> | null {
      return null;
    },
  },
};
