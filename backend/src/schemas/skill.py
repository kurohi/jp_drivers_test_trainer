"""Skill module schemas."""

from pydantic import BaseModel


class SkillModuleOut(BaseModel):
    """Skill module output with all trajectory and guidance data."""

    model_config = {"from_attributes": True}

    id: int
    slug: str
    name_en: str
    name_pt: str
    sort_order: int
    overview_en: str
    overview_pt: str
    svg_path: str  # Path to SVG asset
    correct_trajectory_json: str  # JSON string of correct answer pattern
    wrong_trajectory_json: str  # JSON string of wrong answer pattern
    common_mistakes_json: str  # JSON string of common mistakes list
    checklist_json: str  # JSON string of checklist items
    pro_tip_en: str
    pro_tip_pt: str
