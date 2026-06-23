"""Theme API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.api.repositories.theme_repo import ThemeRepo
from src.schemas.theme import ThemeOut, ThemeTreeOut

router = APIRouter()


def _theme_to_out(theme) -> ThemeOut:
    """Convert ORM Theme to ThemeOut."""
    return ThemeOut(
        id=theme.id,
        slug=theme.slug,
        name_en=theme.name_en,
        name_pt=theme.name_pt,
        parent_id=theme.parent_id,
        sort_order=theme.sort_order,
    )


def _theme_to_tree_out(theme) -> ThemeTreeOut:
    """Convert ORM Theme (with children) to ThemeTreeOut."""
    return ThemeTreeOut(
        id=theme.id,
        slug=theme.slug,
        name_en=theme.name_en,
        name_pt=theme.name_pt,
        parent_id=theme.parent_id,
        sort_order=theme.sort_order,
        children=[_theme_to_tree_out(c) for c in theme.children],
    )


@router.get("/", response_model=list[ThemeOut])
async def list_themes(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[ThemeOut]:
    """List all themes (paginated). Returns root themes with flat list."""
    repo = ThemeRepo(session)
    all_themes = await repo.list_root_themes()
    # Paginate in-memory since root themes are few
    paginated = all_themes[offset : offset + limit]
    return [_theme_to_out(t) for t in paginated]


@router.get("/{slug}", response_model=ThemeOut)
async def get_theme(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> ThemeOut:
    """Get a single theme by slug, including sub-themes info."""
    repo = ThemeRepo(session)
    theme = await repo.get_by_slug(slug)
    if theme is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme not found")
    return _theme_to_out(theme)


@router.get("/{slug}/tree", response_model=ThemeTreeOut)
async def get_theme_tree(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> ThemeTreeOut:
    """Get a theme with its full child hierarchy."""
    repo = ThemeRepo(session)
    # Fetch the full tree and find the matching root
    tree = await repo.get_theme_tree()
    for root in tree:
        if root.slug == slug:
            return _theme_to_tree_out(root)
        # Search children
        found = _find_theme_in_tree(root, slug)
        if found:
            return _theme_to_tree_out(found)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme not found")


def _find_theme_in_tree(theme, slug: str):
    """Recursively search for a theme by slug in the tree."""
    for child in theme.children:
        if child.slug == slug:
            return child
        found = _find_theme_in_tree(child, slug)
        if found:
            return found
    return None
