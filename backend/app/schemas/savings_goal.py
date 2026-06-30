"""
Pydantic schemas for the SavingsGoal domain.

Schemas:
  SavingsGoalCreate   – set a new savings target
  SavingsGoalUpdate   – update goal details or current amount
  SavingsGoalResponse – API response including progress percentage
"""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field, field_validator


class SavingsGoalCreate(BaseModel):
    """Input schema for creating a savings goal."""

    goal_name: str
    target_amount: Decimal
    current_amount: Decimal = Decimal("0.00")
    target_date: date | None = None

    @field_validator("goal_name")
    @classmethod
    def validate_goal_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Goal name cannot be empty.")
        if len(v) > 255:
            raise ValueError("Goal name must be 255 characters or fewer.")
        return v

    @field_validator("target_amount")
    @classmethod
    def validate_target_amount(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Target amount must be greater than zero.")
        return round(v, 2)

    @field_validator("current_amount")
    @classmethod
    def validate_current_amount(cls, v: Decimal) -> Decimal:
        if v < Decimal("0"):
            raise ValueError("Current amount cannot be negative.")
        return round(v, 2)


class SavingsGoalUpdate(BaseModel):
    """Input schema for partially updating a savings goal."""

    goal_name: str | None = None
    target_amount: Decimal | None = None
    current_amount: Decimal | None = None
    target_date: date | None = None

    @field_validator("goal_name")
    @classmethod
    def validate_goal_name(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Goal name cannot be empty.")
        return v

    @field_validator("target_amount")
    @classmethod
    def validate_target_amount(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= Decimal("0"):
            raise ValueError("Target amount must be greater than zero.")
        return v

    @field_validator("current_amount")
    @classmethod
    def validate_current_amount(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < Decimal("0"):
            raise ValueError("Current amount cannot be negative.")
        return v


class SavingsGoalResponse(BaseModel):
    """Savings goal data returned by the API, including computed progress."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    goal_name: str
    target_amount: Decimal
    current_amount: Decimal
    target_date: date | None = None
    created_at: datetime

    @computed_field  # type: ignore[misc]
    @property
    def progress_percentage(self) -> float:
        """Percentage of target amount already saved (0–100+)."""
        if self.target_amount == Decimal("0"):
            return 0.0
        return round(float(self.current_amount / self.target_amount * 100), 2)
