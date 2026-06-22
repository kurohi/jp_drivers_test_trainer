// Skill module types mirrored from backend src/schemas/skill.py

export interface SkillModuleOut {
  id: number;
  slug: string;
  name_en: string;
  name_pt: string;
  sort_order: number;
  overview_en: string;
  overview_pt: string;
  svg_path: string;
  correct_trajectory_json: string;
  wrong_trajectory_json: string;
  common_mistakes_json: string;
  checklist_json: string;
  pro_tip_en: string;
  pro_tip_pt: string;
}
