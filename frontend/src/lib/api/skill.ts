/**
 * Skill-test API client.
 *
 * In mock mode (VITE_API_MOCK=true), returns mock data.
 * In live mode, fetches from the backend via the /api proxy.
 */

import type { SkillModuleOut } from "@/types";
import { mockSkillModules } from "./mock-extended";
import { request } from "./fetch";

const isMock = import.meta.env.VITE_API_MOCK === "true";

/** Simulate network latency for mock mode. */
function delay<T>(value: T, ms = 200): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

/** Lightweight list item (no heavy JSON blobs). */
export interface SkillModuleListItem {
  id: number;
  slug: string;
  name_en: string;
  name_pt: string;
  sort_order: number;
}

export const skillApi = {
  /** List all skill modules (lightweight). */
  async list(): Promise<SkillModuleListItem[]> {
    if (isMock) {
      const items = mockSkillModules.map((m) => ({
        id: m.id,
        slug: m.slug,
        name_en: m.name_en,
        name_pt: m.name_pt,
        sort_order: m.sort_order,
      }));
      return delay(items);
    }

    return request<SkillModuleListItem[]>("/api/skill-test/modules");
  },

  /** Get a single skill module by slug (full detail). */
  async getBySlug(slug: string): Promise<SkillModuleOut | null> {
    if (isMock) {
      const module = mockSkillModules.find((m) => m.slug === slug) ?? null;
      return delay(module);
    }

    return request<SkillModuleOut>(`/api/skill-test/modules/${slug}`);
  },
};