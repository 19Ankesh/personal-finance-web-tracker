"""
Pydantic schemas for the Budget domain.

Schemas:
  BudgetCreate   – set a monthly category budget
  BudgetUpdate   – change the budget limit
  BudgetResponse – API response with nested category
"""
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.category import CategoryResponse


class BudgetCreate(BaseModel):
    """Input schema for creating a monthly budget."""

    category_id: UUID
    budget_limit: Decimal
    month: int   # 1–12
    year: int    # e.g. 2025

    @field_validator("budget_limit")
    @classmethod
    def validate_budget_limit(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Budget limit must be greater than zero.")
        return round(v, 2)

    @field_validator("month")
    @classmethod
    def validate_month(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError("Month must be between 1 and 12.")
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        if not 2000 <= v <= 2100:
            raise ValueError("Year must be between 2000 and 2100.")
        return v


class BudgetUpdate(BaseModel):
    """Input schema for updating a budget's limit."""

    budget_limit: Decimal | None = None

    @field_validator("budget_limit")
    @classmethod
    def validate_budget_limit(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= Decimal("0"):
            raise ValueError("Budget limit must be greater than zero.")
        return v


class BudgetResponse(BaseModel):
    """Budget data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    category_id: UUID
    budget_limit: Decimal
    month: int
    year: int
    category: CategoryResponse | None = None
