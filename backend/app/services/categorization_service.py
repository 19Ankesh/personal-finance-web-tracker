"""
Categorization service layer.

Provides:
  - save_merchant_mapping  – upsert a user-specific merchant → category mapping
  - get_user_merchant_mappings – list all mappings visible to a user
  - delete_merchant_mapping    – remove a user-specific mapping

Upsert semantics for save_merchant_mapping:
  • If the user already has a mapping for this merchant name → UPDATE category.
  • If no user-specific mapping exists → INSERT new row.
  • Global default mappings (user_id = NULL) are never modified.
"""
import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.categorizer import normalize_merchant_name
from app.models.models import Category, MerchantMapping
from app.schemas.merchant_mapping import MerchantMappingResponse

logger = logging.getLogger(__name__)


def save_merchant_mapping(
    user_id: UUID,
    merchant_name: str,
    category_id: UUID,
    db: Session,
) -> MerchantMappingResponse:
    """
    Upsert a user-specific merchant → category mapping.

    Args:
        user_id:       Authenticated user's UUID.
        merchant_name: Raw merchant name (normalized internally).
        category_id:   UUID of the target category.
        db:            Active SQLAlchemy session.

    Returns:
        The created or updated MerchantMappingResponse.

    Raises:
        HTTPException 404 – if category_id does not exist.
    """
    # Validate category exists (can be default or user-owned)
    category: Category | None = (
        db.query(Category).filter(Category.id == category_id).first()
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )

    normalized = normalize_merchant_name(merchant_name)

    # Check for existing user-specific mapping
    existing: MerchantMapping | None = (
        db.query(MerchantMapping)
        .filter(
            MerchantMapping.merchant_name == normalized,
            MerchantMapping.user_id == user_id,
        )
        .first()
    )

    if existing is not None:
        existing.category_id = category_id
        db.commit()
        db.refresh(existing)
        logger.info(
            "Updated merchant mapping: user=%s  merchant=%r  → category=%s",
            user_id, normalized, category_id,
        )
        return MerchantMappingResponse.model_validate(existing)

    # Create new user-specific mapping
    mapping = MerchantMapping(
        user_id=user_id,
        merchant_name=normalized,
        category_id=category_id,
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    logger.info(
        "Created merchant mapping: user=%s  merchant=%r  → category=%s",
        user_id, normalized, category_id,
    )
    return MerchantMappingResponse.model_validate(mapping)


def get_user_merchant_mappings(
    user_id: UUID,
    db: Session,
) -> list[MerchantMappingResponse]:
    """
    Return all merchant mappings visible to a user.

    Includes:
      - User-specific mappings (user_id = current user)  — listed first
      - Global default mappings (user_id = NULL)

    Results are ordered: user-specific first, then alphabetically by merchant.
    """
    mappings: list[MerchantMapping] = (
        db.query(MerchantMapping)
        .filter(
            (MerchantMapping.user_id == user_id)
            | (MerchantMapping.user_id.is_(None))
        )
        .order_by(
            # user-specific first (non-null user_id sorts before NULL)
            MerchantMapping.user_id.is_(None),
            MerchantMapping.merchant_name,
        )
        .all()
    )
    return [MerchantMappingResponse.model_validate(m) for m in mappings]


def delete_merchant_mapping(
    mapping_id: UUID,
    user_id: UUID,
    db: Session,
) -> None:
    """
    Delete a user-specific merchant mapping.

    Only user-specific mappings (user_id = current user) can be deleted.
    Global default mappings (user_id = NULL) are protected.

    Raises:
        HTTPException 404 – mapping not found or not owned by user.
        HTTPException 403 – attempt to delete a global default.
    """
    mapping: MerchantMapping | None = (
        db.query(MerchantMapping)
        .filter(MerchantMapping.id == mapping_id)
        .first()
    )
    if mapping is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant mapping not found.",
        )
    if mapping.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Global default mappings cannot be deleted.",
        )
    if mapping.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant mapping not found.",
        )

    db.delete(mapping)
    db.commit()
    logger.info(
        "Deleted merchant mapping: id=%s  user=%s  merchant=%r",
        mapping_id, user_id, mapping.merchant_name,
    )
