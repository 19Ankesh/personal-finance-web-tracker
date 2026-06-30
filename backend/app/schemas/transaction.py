"""
Pydantic schemas for the Transaction domain.

Schemas:
  TransactionCreate       – create a transaction
  TransactionUpdate       – partial update
  TransactionResponse     – full transaction with nested category
  TransactionListResponse – paginated list response
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.models import PaymentMode, TransactionSource
from app.schemas.category import CategoryResponse


class TransactionCreate(BaseModel):
    """Input schema for creating a new transaction."""

    merchant: str
    amount: Decimal
    transaction_date: date
    payment_mode: PaymentMode = PaymentMode.UPI
    source: TransactionSource = TransactionSource.MANUAL
    notes: str | None = None
    category_id: UUID | None = None

    @field_validator("merchant")
    @classmethod
    def validate_merchant(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Merchant name cannot be empty.")
        if len(v) > 255:
            raise ValueError("Merchant name must be 255 characters or fewer.")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Amount must be greater than zero.")
        return round(v, 2)


class TransactionUpdate(BaseModel):
    """Input schema for partially updating a transaction."""

    merchant: str | None = None
    amount: Decimal | None = None
    transaction_date: date | None = None
    payment_mode: PaymentMode | None = None
    source: TransactionSource | None = None
    notes: str | None = None
    category_id: UUID | None = None

    @field_validator("merchant")
    @classmethod
    def validate_merchant(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Merchant name cannot be empty.")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= Decimal("0"):
            raise ValueError("Amount must be greater than zero.")
        return v


class TransactionResponse(BaseModel):
    """Full transaction representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    category_id: UUID | None = None
    merchant: str
    amount: Decimal
    transaction_date: date
    payment_mode: PaymentMode
    source: TransactionSource
    notes: str | None = None
    created_at: datetime
    category: CategoryResponse | None = None


class TransactionListResponse(BaseModel):
    """Paginated list of transactions."""

    items: List[TransactionResponse]
    total: int
    skip: int
    limit: int
