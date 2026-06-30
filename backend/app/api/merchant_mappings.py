"""
Merchant Mappings API router.

Routes:
  GET    /merchant-mappings/       – list all mappings visible to the user
  POST   /merchant-mappings/       – create or update a user-specific mapping
  DELETE /merchant-mappings/{id}   – delete a user-specific mapping

This is the "Ask User Category → Save Mapping → Auto Categorize Future" flow
described in the Phase 2 roadmap.

All endpoints require JWT authentication.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.merchant_mapping import (
    MerchantMappingCreate,
    MerchantMappingResponse,
)
from app.services.categorization_service import (
    delete_merchant_mapping,
    get_user_merchant_mappings,
    save_merchant_mapping,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=list[MerchantMappingResponse],
    summary="List all merchant mappings visible to the current user",
)
async def list_mappings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MerchantMappingResponse]:
    """
    Return all merchant → category mappings the user can see:

    - **User-specific** mappings (created by this user) — listed first.
    - **Global default** mappings (seeded with the app) — listed after.

    Use these to understand what is already categorized and to identify
    gaps where new mappings should be added.
    """
    return get_user_merchant_mappings(current_user.id, db)


@router.post(
    "/",
    response_model=MerchantMappingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save or update a merchant → category mapping",
)
async def save_mapping(
    data: MerchantMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MerchantMappingResponse:
    """
    Create or update a personal merchant → category mapping.

    - If a mapping for this merchant already exists for your account,
      its category is **updated** (upsert).
    - If no mapping exists, a new one is **created**.
    - The merchant name is automatically **normalised to lowercase**.
    - Global default mappings are never modified.

    After saving, all future imports containing this merchant name will be
    automatically categorized.
    """
    return save_merchant_mapping(
        user_id=current_user.id,
        merchant_name=data.merchant_name,
        category_id=data.category_id,
        db=db,
    )


@router.delete(
    "/{mapping_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user-specific merchant mapping",
)
async def delete_mapping(
    mapping_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Permanently delete a personal merchant mapping.

    Only **user-specific** mappings can be deleted.
    Global default mappings return **403 Forbidden**.
    """
    delete_merchant_mapping(mapping_id, current_user.id, db)
