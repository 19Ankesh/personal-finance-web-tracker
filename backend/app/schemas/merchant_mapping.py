"""
Pydantic schemas for the MerchantMapping domain.

Schemas:
  MerchantMappingCreate   – add or override a merchant→category mapping
  MerchantMappingUpdate   – change which category a merchant maps to
  MerchantMappingResponse – API response with nested category
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.category import CategoryResponse


class MerchantMappingCreate(BaseModel):
    """Input schema for creating a merchant mapping."""

    merchant_name: str
    category_id: UUID

    @field_validator("merchant_name")
    @classmethod
    def normalise_merchant_name(cls, v: str) -> str:
        """Store merchant names lowercase for case-insensitive lookups."""
        v = v.strip().lower()
        if not v:
            raise ValueError("Merchant name cannot be empty.")
        if len(v) > 255:
            raise ValueError("Merchant name must be 255 characters or fewer.")
        return v


class MerchantMappingUpdate(BaseModel):
    """Input schema for updating a merchant mapping's target category."""

    category_id: UUID | None = None


class MerchantMappingResponse(BaseModel):
    """Merchant mapping data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None = None   # None = global default mapping
    merchant_name: str
    category_id: UUID
    created_at: datetime
    category: CategoryResponse | None = None
