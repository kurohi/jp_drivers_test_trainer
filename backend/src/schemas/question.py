"""Question schemas."""



from pydantic import BaseModel

from .ui_meta import Difficulty


class QuestionListItem(BaseModel):
    """Question summary for list/m(mock-test) UIs — NO answers or explanations."""

    model_config = {"from_attributes": True}

    id: int
    theme_id: int
    prompt_en: str
    prompt_pt: str
    tricky: bool
    tricky_pattern: str | None = None
    difficulty: Difficulty
    translations_status: str  # e.g. "complete", "en_only", "pt_only"
    image_url: str | None = None


class QuestionDetail(QuestionListItem):
    """Full question with answers and explanations — only for admin/review UIs."""

    model_config = {"from_attributes": True}

    answer_en: str
    answer_pt: str
    explanation_en: str
    explanation_pt: str
    image_url: str | None = None  # inherited from QuestionListItem, explicit for clarity
