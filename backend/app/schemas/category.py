"""
Pydantic schemas for the Category domain.

Schemas:
  CategoryCreate   – create a category
  CategoryUpdate   – partial update
  CategoryResponse – API response
"""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class CategoryCreate(BaseModel):
    """Input schema for creating a new category."""

    category_name: str
    is_default: bool = False

    @field_validator("category_name")
    @classmethod
    def validate_category_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Category name cannot be empty.")
        if len(v) > 100:
            raise ValueError("Category name must be 100 characters or fewer.")
        return v


class CategoryUpdate(BaseModel):
    """Input schema for partially updating a category."""

    category_name: str | None = None
    is_default: bool | None = None

    @field_validator("category_name")
    @classmethod
    def validate_category_name(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Category name cannot be empty.")
        return v


class CategoryResponse(BaseModel):
    """Public category data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None = None
    category_name: str
    is_default: bool
