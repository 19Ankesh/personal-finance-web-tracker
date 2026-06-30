"""
Analytics service layer.

All functions run raw SQLAlchemy aggregation queries against the transactions
table. No data is cached — every call hits the database directly.

Shared query pattern:
  - Filter by user_id (row-level isolation)
  - Filter by date_from and date_to (inclusive)
  - Aggregate with func.sum / func.count / func.avg / func.max
"""
import calendar
import logging
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.models import Category, Transaction
from app.schemas.analytics import (
    CategoryBreakdownItem,
    DashboardResponse,
    MonthlyTrendItem,
    PaymentModeItem,
    SummaryResponse,
    TopMerchantItem,
)

logger = logging.getLogger(__name__)


# ── Default date helpers ──────────────────────────────────────────────────────


def _resolve_dates(
    date_from: date | None,
    date_to: date | None,
) -> tuple[date, date]:
    today = date.today()
    return (
        date_from or (today - timedelta(days=180)),
        date_to or today,
    )


def _months_ago(n: int) -> date:
    """
    Return the first day of the month N months before today.

    Handles edge cases (e.g. Jan 31 - 1 month = Dec 31 → Dec 1).
    """
    today = date.today()
    month = today.month - n
    year  = today.year + month // 12
    month = month % 12
    if month <= 0:
        month += 12
        year  -= 1
    return date(year, month, 1)


# ── Individual aggregation functions ─────────────────────────────────────────


def get_summary(
    user_id: UUID,
    db: Session,
    date_from: date | None = None,
    date_to: date | None = None,
) -> SummaryResponse:
    """
    Return KPI numbers for the given date range.

    Computes in one query:
      - Total amount spent
      - Transaction count
      - Average transaction amount
      - Largest single transaction
    """
    df, dt = _resolve_dates(date_from, date_to)

    row = (
        db.query(
            func.coalesce(func.sum(Transaction.amount), Decimal("0.00")).label("total_spent"),
            func.count(Transaction.id).label("tx_count"),
            func.coalesce(func.avg(Transaction.amount), Decimal("0.00")).label("avg_amount"),
            func.coalesce(func.max(Transaction.amount), Decimal("0.00")).label("largest_tx"),
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= df,
            Transaction.transaction_date <= dt,
        )
        .one()
    )

    return SummaryResponse(
        total_spent=round(Decimal(str(row.total_spent)), 2),
        tx_count=row.tx_count,
        avg_amount=round(Decimal(str(row.avg_amount)), 2),
        largest_tx=round(Decimal(str(row.largest_tx)), 2),
        period_from=df,
        period_to=dt,
    )


def get_by_category(
    user_id: UUID,
    db: Session,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[CategoryBreakdownItem]:
    """
    Return spending totals grouped by category, sorted by total desc.

    Uncategorized transactions (category_id = NULL) are grouped together
    under the label "Uncategorized".
    """
    df, dt = _resolve_dates(date_from, date_to)

    rows = (
        db.query(
            func.coalesce(Category.category_name, "Uncategorized").label("category_name"),
            Category.id.label("category_id"),
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= df,
            Transaction.transaction_date <= dt,
        )
        .group_by(Category.category_name, Category.id)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    grand_total = sum(Decimal(str(r.total)) for r in rows) or Decimal("1")

    return [
        CategoryBreakdownItem(
            category_name=r.category_name,
            category_id=r.category_id,
            total=round(Decimal(str(r.total)), 2),
            count=r.count,
            percentage=round(float(Decimal(str(r.total)) / grand_total * 100), 2),
        )
        for r in rows
    ]


def get_monthly_trend(
    user_id: UUID,
    db: Session,
    date_from: date | None = None,
    date_to: date | None = None,
    months: int = 6,
) -> list[MonthlyTrendItem]:
    """
    Return monthly spending totals ordered chronologically.

    When date_from is explicitly provided it is used as-is.
    When date_from is None, `months` controls how far back to go —
    it always computes from the first of the month `months` ago,
    regardless of what date_to is set to.
    """
    # Fix: compute date_from from `months` independently of date_to
    if date_from is None:
        date_from = _months_ago(months)
    date_to = date_to or date.today()

    rows = (
        db.query(
            extract("year",  Transaction.transaction_date).label("year"),
            extract("month", Transaction.transaction_date).label("month"),
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
        )
        .group_by(
            extract("year",  Transaction.transaction_date),
            extract("month", Transaction.transaction_date),
        )
        .order_by(
            extract("year",  Transaction.transaction_date),
            extract("month", Transaction.transaction_date),
        )
        .all()
    )

    return [
        MonthlyTrendItem(
            year=int(r.year),
            month=int(r.month),
            label=f"{calendar.month_abbr[int(r.month)]} {int(r.year)}",
            total=round(Decimal(str(r.total)), 2),
            count=r.count,
        )
        for r in rows
    ]


def get_top_merchants(
    user_id: UUID,
    db: Session,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 10,
) -> list[TopMerchantItem]:
    """Return the top N merchants by total spend, descending."""
    df, dt = _resolve_dates(date_from, date_to)

    rows = (
        db.query(
            Transaction.merchant.label("merchant"),
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= df,
            Transaction.transaction_date <= dt,
        )
        .group_by(Transaction.merchant)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(min(limit, 20))
        .all()
    )

    return [
        TopMerchantItem(
            merchant=r.merchant,
            total=round(Decimal(str(r.total)), 2),
            count=r.count,
        )
        for r in rows
    ]


def get_by_payment_mode(
    user_id: UUID,
    db: Session,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[PaymentModeItem]:
    """Return spending totals grouped by payment mode, sorted by total desc."""
    df, dt = _resolve_dates(date_from, date_to)

    rows = (
        db.query(
            Transaction.payment_mode.label("payment_mode"),
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= df,
            Transaction.transaction_date <= dt,
        )
        .group_by(Transaction.payment_mode)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    grand_total = sum(Decimal(str(r.total)) for r in rows) or Decimal("1")

    return [
        PaymentModeItem(
            payment_mode=r.payment_mode.value if hasattr(r.payment_mode, "value") else str(r.payment_mode),
            total=round(Decimal(str(r.total)), 2),
            count=r.count,
            percentage=round(float(Decimal(str(r.total)) / grand_total * 100), 2),
        )
        for r in rows
    ]


# ── Combined dashboard function ───────────────────────────────────────────────


def get_dashboard(
    user_id: UUID,
    db: Session,
    date_from: date | None = None,
    date_to: date | None = None,
    months: int = 6,
    top_n: int = 10,
) -> DashboardResponse:
    """
    Fetch all dashboard data in five queries and return as one response.

    Fix: monthly_trend now receives the raw date_from/date_to from the request
    (not the resolved values) so the `months` parameter correctly controls
    how far back the trend chart reaches independently of the filter range.
    """
    df, dt = _resolve_dates(date_from, date_to)
    logger.info(
        "Dashboard query: user=%s  period=%s → %s  months=%d", user_id, df, dt, months
    )

    return DashboardResponse(
        period_from=df,
        period_to=dt,
        summary=get_summary(user_id, db, df, dt),
        by_category=get_by_category(user_id, db, df, dt),
        # Pass original date_from (may be None) so `months` param is respected
        monthly_trend=get_monthly_trend(user_id, db, date_from, date_to, months),
        by_payment_mode=get_by_payment_mode(user_id, db, df, dt),
        top_merchants=get_top_merchants(user_id, db, df, dt, top_n),
    )
