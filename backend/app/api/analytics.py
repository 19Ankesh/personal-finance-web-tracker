"""
Analytics API router.

Routes:
  GET /analytics/dashboard        — all analytics in one request (recommended)
  GET /analytics/summary          — KPI numbers
  GET /analytics/by-category      — category breakdown
  GET /analytics/monthly-trend    — monthly totals
  GET /analytics/top-merchants    — top N merchants
  GET /analytics/by-payment-mode  — payment mode breakdown
  GET /analytics/health-score     — financial health score (Phase 4)
  GET /analytics/insights         — smart spending insights (Phase 4)

All endpoints require JWT authentication and are scoped to the current user.
"""
import logging
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.health_score import HealthScoreResponse, calculate_health_score
from app.core.insights import Insight, generate_insights
from app.db.session import get_db
from app.models.models import User
from app.schemas.analytics import (
    CategoryBreakdownItem,
    DashboardResponse,
    MonthlyTrendItem,
    PaymentModeItem,
    SummaryResponse,
    TopMerchantItem,
)
from app.services.analytics_service import (
    get_by_category,
    get_by_payment_mode,
    get_dashboard,
    get_monthly_trend,
    get_summary,
    get_top_merchants,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_DATE_FROM_DESC = "Start date (inclusive). Defaults to 6 months ago."
_DATE_TO_DESC   = "End date (inclusive). Defaults to today."


# ── Combined dashboard ────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardResponse, summary="Full dashboard data in one request", tags=["Dashboard"])
async def dashboard(
    date_from: date | None = Query(default=None, description=_DATE_FROM_DESC),
    date_to:   date | None = Query(default=None, description=_DATE_TO_DESC),
    months: int = Query(default=6, ge=1, le=24),
    top_n:  int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    return get_dashboard(user_id=current_user.id, db=db, date_from=date_from, date_to=date_to, months=months, top_n=top_n)


# ── Individual analytics ──────────────────────────────────────────────────────

@router.get("/summary", response_model=SummaryResponse, summary="Spending KPI summary", tags=["Analytics"])
async def summary(
    date_from: date | None = Query(default=None),
    date_to:   date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SummaryResponse:
    return get_summary(current_user.id, db, date_from, date_to)


@router.get("/by-category", response_model=list[CategoryBreakdownItem], summary="Spending breakdown by category", tags=["Analytics"])
async def by_category(
    date_from: date | None = Query(default=None),
    date_to:   date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CategoryBreakdownItem]:
    return get_by_category(current_user.id, db, date_from, date_to)


@router.get("/monthly-trend", response_model=list[MonthlyTrendItem], summary="Monthly spending trend", tags=["Analytics"])
async def monthly_trend(
    date_from: date | None = Query(default=None),
    date_to:   date | None = Query(default=None),
    months: int = Query(default=6, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MonthlyTrendItem]:
    return get_monthly_trend(current_user.id, db, date_from, date_to, months)


@router.get("/top-merchants", response_model=list[TopMerchantItem], summary="Top merchants by spend", tags=["Analytics"])
async def top_merchants(
    date_from: date | None = Query(default=None),
    date_to:   date | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TopMerchantItem]:
    return get_top_merchants(current_user.id, db, date_from, date_to, limit)


@router.get("/by-payment-mode", response_model=list[PaymentModeItem], summary="Spending breakdown by payment mode", tags=["Analytics"])
async def by_payment_mode(
    date_from: date | None = Query(default=None),
    date_to:   date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PaymentModeItem]:
    return get_by_payment_mode(current_user.id, db, date_from, date_to)


# ── Phase 4: Health Score + Insights ─────────────────────────────────────────

@router.get(
    "/health-score",
    response_model=HealthScoreResponse,
    summary="Financial health score (0–100)",
    tags=["Analytics"],
)
async def health_score(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HealthScoreResponse:
    """
    Calculate and return the user's financial health score.

    Score is derived from:
    - Budget adherence (40 pts)
    - Savings goal progress (30 pts)
    - Spending consistency (30 pts)
    """
    return calculate_health_score(current_user.id, db)


@router.get(
    "/insights",
    response_model=list[Insight],
    summary="Smart spending insights",
    tags=["Analytics"],
)
async def insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Insight]:
    """
    Generate personalized spending insights for the current user.

    Returns up to 10 insights covering:
    - Category spend changes vs last month
    - Budget alerts (80% and 100% thresholds)
    - Top merchant this month
    - Biggest single expense
    - Payment mode dominance
    - Savings goal milestones
    """
    return generate_insights(current_user.id, db)
