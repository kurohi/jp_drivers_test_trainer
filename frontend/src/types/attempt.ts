// Attempt types mirrored from backend src/schemas/attempt.py

import type { Language } from "./ui_meta";

export type UserAnswer = "true" | "false";

export interface AnswerItem {
  question_id: number;
  user_answer: UserAnswer;
  time_spent_ms: number | null;
}

export interface AttemptStartIn {
  language: Language;
  theme_ids: number[] | null;
  question_count: number;
  tricky_ratio: number;
  time_limit_seconds: number;
  seed: number | null;
}

export interface AttemptSubmitIn {
  answers: AnswerItem[];
}

export interface AttemptAnswerOut {
  question_id: number;
  is_correct: boolean;
  user_answer: UserAnswer;
  correct_answer: UserAnswer;
  prompt_en?: string;
  prompt_pt?: string;
  image_url?: string | null;
  explanation_en: string;
  explanation_pt: string;
}

export interface AttemptResultOut {
  attempt_id: number;
  score: number;
  max_score: number;
  passed: boolean;
  tricky_ratio_actual: number;
  boundary_score: number;
  answers: AttemptAnswerOut[];
}
