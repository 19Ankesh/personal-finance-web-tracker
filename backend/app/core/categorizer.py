"""
Merchant categorization engine.

Normalizes a raw merchant name and resolves it to a Category through a
two-level lookup:

  Level 1 – User-specific mapping   (user_id = current user's UUID)
  Level 2 – Global default mapping  (user_id = NULL)
  Level 3 – None                    (caller treats as "Uncategorized")

Normalization pipeline:
  1. Strip leading/trailing whitespace
  2. Convert to lowercase
  3. Remove all characters except letters, digits, spaces, and hyphens
  4. Collapse multiple spaces to a single space
"""
import logging
import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.models import Category, MerchantMapping

logger = logging.getLogger(__name__)


def normalize_merchant_name(merchant_name: str) -> str:
    """
    Produce a canonical lowercase key for merchant lookup.

    This same function must be called both when *saving* and *querying*
    merchant mappings to ensure consistent comparison.

    Examples:
        "  SWIGGY  "          → "swiggy"
        "Apollo Pharmacy"     → "apollo pharmacy"
        "UPI-Zomato-9876"     → "upi-zomato-9876"
        "Amazon.in!"          → "amazonin"   (dots/! removed)
    """
    name = merchant_name.strip().lower()
    # Keep only alphanumeric, spaces, and hyphens
    name = re.sub(r"[^\w\s\-]", "", name)
    # Collapse multiple whitespace characters
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def categorize_merchant(
    merchant_name: str,
    user_id: UUID,
    db: Session,
) -> Category | None:
    """
    Resolve a merchant name to its best-matching Category.

    Lookup order:
      1. User-specific MerchantMapping (user_id = current user)
         → personalised learning from Phase 2 "Save Mapping" flow
      2. Global default MerchantMapping (user_id = NULL)
         → seeded defaults (Swiggy→Food, Uber→Transport, etc.)
      3. Returns None if no mapping exists

    Args:
        merchant_name: Raw merchant string from a transaction or import row.
        user_id:       Authenticated user's UUID.
        db:            Active SQLAlchemy session.

    Returns:
        The matching Category ORM object, or None.
    """
    normalized = normalize_merchant_name(merchant_name)
    logger.debug(
        "categorize_merchant: raw=%r  normalized=%r  user=%s",
        merchant_name, normalized, user_id,
    )

    # ── Level 1: User-specific mapping ───────────────────────────────────────
    user_mapping: MerchantMapping | None = (
        db.query(MerchantMapping)
        .filter(
            MerchantMapping.merchant_name == normalized,
            MerchantMapping.user_id == user_id,
        )
        .first()
    )
    if user_mapping is not None:
        logger.debug(
            "User mapping hit: %r → category_id=%s", normalized, user_mapping.category_id
        )
        return user_mapping.category

    # ── Level 2: Global default mapping ──────────────────────────────────────
    default_mapping: MerchantMapping | None = (
        db.query(MerchantMapping)
        .filter(
            MerchantMapping.merchant_name == normalized,
            MerchantMapping.user_id.is_(None),
        )
        .first()
    )
    if default_mapping is not None:
        logger.debug(
            "Default mapping hit: %r → category_id=%s",
            normalized, default_mapping.category_id,
        )
        return default_mapping.category

    # ── Level 3: No mapping found ─────────────────────────────────────────────
    logger.debug("No mapping found for %r — will be Uncategorized", normalized)
    return None
