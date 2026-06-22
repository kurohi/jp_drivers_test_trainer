// Theme types mirrored from backend src/schemas/theme.py

export interface ThemeOut {
  id: number;
  slug: string;
  name_en: string;
  name_pt: string;
  parent_id: number | null;
  sort_order: number;
}

export interface ThemeTreeOut extends ThemeOut {
  children: ThemeTreeOut[];
}
