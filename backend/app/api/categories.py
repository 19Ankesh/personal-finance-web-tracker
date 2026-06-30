"""
Categories API router.

Routes:
  GET /categories/ – list all categories visible to the current user
                     (global defaults + user-created categories)

All endpoints require JWT authentication.
"""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.models import Category, User
from app.schemas.category import CategoryResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=list[CategoryResponse],
    summary="List all categories visible to the current user",
)
async def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CategoryResponse]:
    """
    Return all categories available to the user:

    - **Global defaults** (user_id = NULL, is_default = True) — seeded with the app.
    - **User-created** categories (user_id = current user).

    Results are ordered: defaults first, then user-created, alphabetically within each group.
    """
    categories: list[Category] = (
        db.query(Category)
        .filter(
            (Category.user_id == current_user.id) | (Category.user_id.is_(None))
        )
        .order_by(
            Category.user_id.is_(None).desc(),   # global defaults first
            Category.category_name.asc(),
        )
        .all()
    )
    return [CategoryResponse.model_validate(c) for c in categories]
