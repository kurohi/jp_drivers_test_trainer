import type { ThemeOut } from "@/types";
import {
  mockThemes,
  mockCountByTheme,
} from "./mock";
import { request, type ThemeWithCount } from "./fetch";
import { useUIStore } from "@/store/ui";

const isMock = import.meta.env.VITE_API_MOCK === "true";

function delay<T>(value: T, ms = 200): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

export type { ThemeWithCount };

export const themesApi = {
  async list(): Promise<ThemeWithCount[]> {
    if (isMock) {
      const themes = mockThemes.map((t) => ({
        ...t,
        question_count: mockCountByTheme(t.id),
      }));
      return delay(themes);
    }

    const language = useUIStore.getState().language;
    const params = language ? `?language=${language}` : "";
    const themes = await request<ThemeOut[]>(`/api/themes${params}`);
    return themes.map((t) => ({ ...t, question_count: 0 }));
  },

  async getBySlug(slug: string): Promise<ThemeOut | null> {
    if (isMock) {
      const theme = mockThemes.find((t) => t.slug === slug) ?? null;
      return delay(theme);
    }

    const language = useUIStore.getState().language;
    const params = language ? `?language=${language}` : "";
    return request<ThemeOut>(`/api/themes/${slug}${params}`);
  },
};
