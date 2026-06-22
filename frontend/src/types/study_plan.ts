// Study plan types mirrored from backend src/schemas/study_plan.py

export type StudyPlanSource = "default-beginner" | "llm-generated";

export interface WeakThemeStat {
  theme_id: number;
  name_en: string;
  wrong_count: number;
  total_attempts: number;
}

export interface PlanDay {
  date: string; // ISO8601 date string
  theme_ids: number[];
  question_count: number;
  focus_note_en: string;
  focus_note_pt: string;
}

export interface StudyPlanGenerateIn {
  available_days: number;
  hours_per_day: number;
}

export interface StudyPlanOut {
  id: number;
  created_at: string; // ISO8601 datetime string
  source: StudyPlanSource;
  days: PlanDay[];
}
