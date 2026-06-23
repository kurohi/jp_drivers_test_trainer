/**
 * Theme API client.
 *
 * In mock mode (VITE_API_MOCK=true), returns data from mock.ts.
 * In live mode, fetches from the backend via the /api proxy.
 */

import type { ThemeOut } from "@/types";
import {
  mockThemes,
  mockCountByTheme,
} from "./mock";

const isMock = import.meta.env.VITE_API_MOCK === "true";

/** Simulate network latency for mock mode. */
function delay<T>(value: T, ms = 200): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

export interface ThemeWithCount extends ThemeOut {
  question_count: number;
}

export const themesApi = {
  /** List all root themes with question counts. */
  async list(): Promise<ThemeWithCount[]> {
    if (isMock) {
      const themes = mockThemes.map((t) => ({
        ...t,
        question_count: mockCountByTheme(t.id),
      }));
      return delay(themes);
    }

    // Live mode — wired in T22
    const res = await fetch("/api/themes");
    if (!res.ok) throw new Error(`Failed to fetch themes: ${res.statusText}`);
    const themes: ThemeOut[] = await res.json();
    // In live mode, question counts come from a separate endpoint or are embedded
    // For now, return without counts — T22 will wire the real endpoint
    return themes.map((t) => ({ ...t, question_count: 0 }));
  },

  /** Get a single theme by slug. */
  async getBySlug(slug: string): Promise<ThemeOut | null> {
    if (isMock) {
      const theme = mockThemes.find((t) => t.slug === slug) ?? null;
      return delay(theme);
    }

    const res = await fetch(`/api/themes/${slug}`);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`Failed to fetch theme: ${res.statusText}`);
    return res.json();
  },
};