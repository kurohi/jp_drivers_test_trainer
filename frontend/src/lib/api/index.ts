/**
 * Unified API client — PI4M-style `api = { themes, questions }` object pattern.
 *
 * Switches between mock and live mode based on VITE_API_MOCK env variable.
 * Mock mode returns realistic data for offline development.
 * Live mode will be fully wired in T22.
 */

import { themesApi } from "./themes";
import { questionsApi } from "./questions";

export const api = {
  themes: themesApi,
  questions: questionsApi,
};