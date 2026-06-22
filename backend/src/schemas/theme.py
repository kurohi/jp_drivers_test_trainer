"""Theme schemas."""

from typing import Optional

from pydantic import BaseModel


class ThemeOut(BaseModel):
    """Flat theme output."""

    model_config = {"from_attributes": True}

    id: int
    slug: str
    name_en: str
    name_pt: str
    parent_id: int | None = None
    sort_order: int


class ThemeTreeOut(ThemeOut):
    """Hierarchical theme with children."""

    children: list["ThemeTreeOut"] = []


# Forward ref resolved
ThemeTreeOut.model_rebuild()
