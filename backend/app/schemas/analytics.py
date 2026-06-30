"""
Pydantic schemas for the Analytics domain.

Used by:
  GET /analytics/summary
  GET /analytics/by-category
  GET /analytics/monthly-trend
  GET /analytics/top-merchants
  GET /analytics/by-payment-mode
  GET /dashboard   (combined response)
"""
from calendar import month_abbr
from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, computed_field


# ── Individual response schemas ───────────────────────────────────────────────


class SummaryResponse(BaseModel):
    """High-level KPI numbers for a date range."""

    total_spent: Decimal
    tx_count: int
    avg_amount: Decimal
    largest_tx: Decimal
    period_from: date
    period_to: date


class CategoryBreakdownItem(BaseModel):
    """Spending total for one category."""

    category_name: str
    category_id: UUID | None = None
    total: Decimal
    count: int
    percentage: float   # share of period total (0–100)


class MonthlyTrendItem(BaseModel):
    """Spending total for one calendar month."""

    year: int
    month: int
    label: str          # e.g. "Jun 2025"
    total: Decimal
    count: int


class TopMerchantItem(BaseModel):
    """One merchant ranked by total spend."""

    merchant: str
    total: Decimal
    count: int


class PaymentModeItem(BaseModel):
    """Spending split for one payment mode."""

    payment_mode: str
    total: Decimal
    count: int
    percentage: float   # share of period total (0–100)


# ── Combined dashboard response ───────────────────────────────────────────────


class DashboardResponse(BaseModel):
    """
    All dashboard data in one response.

    Returned by GET /dashboard so the frontend makes a single request
    instead of five separate calls.
    """

    period_from: date
    period_to: date
    summary: SummaryResponse
    by_category: list[CategoryBreakdownItem]
    monthly_trend: list[MonthlyTrendItem]
    by_payment_mode: list[PaymentModeItem]
    top_merchants: list[TopMerchantItem]
