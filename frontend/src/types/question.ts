// Question types mirrored from backend src/schemas/question.py
// CRITICAL: QuestionListItem must NOT have answer_en/answer_pt/explanation_en/explanation_pt

import type { Difficulty } from "./ui_meta";

export interface QuestionListItem {
  id: number;
  theme_id: number;
  prompt_en: string;
  prompt_pt: string;
  tricky: boolean;
  tricky_pattern: string | null;
  difficulty: Difficulty;
  translations_status: string;
  image_url?: string | null;
}

export interface QuestionDetail extends QuestionListItem {
  answer_en: string;
  answer_pt: string;
  explanation_en: string;
  explanation_pt: string;
}
