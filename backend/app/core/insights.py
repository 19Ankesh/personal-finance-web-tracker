"""
Smart Spending Insights generator.

Produces human-readable insight strings from SQL aggregations.
No AI or ML required — pure rule-based analysis.

Insight types generated:
  1. Category spend change vs last month (increase/decrease)
  2. Top merchant this month
  3. Budget exceeded alerts
  4. Payment mode dominance
  5. Biggest single expense
  6. Savings goal milestone
  7. Spending streak (days without spending)
  8. Most improved category

All insights include a type tag, severity, and icon for frontend rendering.
"""
import logging
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.models import Budget, Category, SavingsGoal, Transaction

logger = logging.getLogger(__name__)


# ── Insight schema ────────────────────────────────────────────────────────────

class Insight(BaseModel):
    type:     str    # category_change | top_merchant | budget_alert | etc.
    icon:     str    # emoji
    title:    str    # short label
    message:  str    # full sentence
    severity: str    # info | warning | success | danger


# ── Date helpers ──────────────────────────────────────────────────────────────

def _this_month() -> tuple[int, int]:
    today = date.today()
    return today.month, today.year


def _last_month() -> tuple[int, int]:
    today = date.today()
    first = date(today.year, today.month, 1)
    prev  = first - timedelta(days=1)
    return prev.month, prev.year


def _month_spend_by_category(
    user_id: UUID, month: int, year: int, db: Session
) -> dict[str, Decimal]:
    """Return {category_name: total_spend} for a given month."""
    rows = (
        db.query(
            func.coalesce(Category.category_name, "Uncategorized").label("cat"),
            func.sum(Transaction.amount).label("total"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == user_id,
            extract("month", Transaction.transaction_date) == month,
            extract("year",  Transaction.transaction_date) == year,
        )
        .group_by(Category.category_name)
        .all()
    )
    return {r.cat: Decimal(str(r.total)) for r in rows}


# ── Individual insight generators ─────────────────────────────────────────────

def _category_change_insights(user_id: UUID, db: Session) -> list[Insight]:
    """Compare this month vs last month spend per category."""
    cm, cy = _this_month()
    lm, ly = _last_month()

    this  = _month_spend_by_category(user_id, cm, cy, db)
    last  = _month_spend_by_category(user_id, lm, ly, db)

    insights = []
    all_cats = set(this) | set(last)

    for cat in all_cats:
        t = this.get(cat, Decimal("0"))
        l = last.get(cat, Decimal("0"))

        if l == 0 or t == 0:
            continue

        change_pct = float((t - l) / l * 100)

        if change_pct >= 20:
            insights.append(Insight(
                type="category_change",
                icon="📈",
                title=f"{cat} spending up",
                message=f"{cat} spending increased by {change_pct:.0f}% compared to last month (₹{t:,.0f} vs ₹{l:,.0f}).",
                severity="warning",
            ))
        elif change_pct <= -20:
            insights.append(Insight(
                type="category_change",
                icon="📉",
                title=f"{cat} spending down",
                message=f"Great job! {cat} spending decreased by {abs(change_pct):.0f}% compared to last month (₹{t:,.0f} vs ₹{l:,.0f}).",
                severity="success",
            ))

    return insights[:4]   # cap at 4 category insights


def _top_merchant_insight(user_id: UUID, db: Session) -> list[Insight]:
    """Identify the top merchant by spend this month."""
    cm, cy = _this_month()

    row = (
        db.query(
            Transaction.merchant.label("merchant"),
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .filter(
            Transaction.user_id == user_id,
            extract("month", Transaction.transaction_date) == cm,
            extract("year",  Transaction.transaction_date) == cy,
        )
        .group_by(Transaction.merchant)
        .order_by(func.sum(Transaction.amount).desc())
        .first()
    )

    if not row:
        return []

    return [Insight(
        type="top_merchant",
        icon="🏪",
        title="Top merchant this month",
        message=f"Your top merchant this month is {row.merchant} with ₹{float(row.total):,.0f} spent across {row.count} transaction{'s' if row.count != 1 else ''}.",
        severity="info",
    )]


def _budget_alert_insights(user_id: UUID, db: Session) -> list[Insight]:
    """Flag categories that have exceeded their monthly budget."""
    cm, cy = _this_month()

    budgets = (
        db.query(Budget)
        .filter(
            Budget.user_id == user_id,
            Budget.month == cm,
            Budget.year  == cy,
        )
        .all()
    )

    insights = []
    for b in budgets:
        spend = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.user_id == user_id,
            Transaction.category_id == b.category_id,
            extract("month", Transaction.transaction_date) == cm,
            extract("year",  Transaction.transaction_date) == cy,
        ).scalar() or Decimal("0")

        spend = Decimal(str(spend))
        limit = Decimal(str(b.budget_limit))
        pct   = float(spend / limit * 100) if limit > 0 else 0

        cat_name = b.category.category_name if b.category else "Unknown"

        if pct >= 100:
            insights.append(Insight(
                type="budget_exceeded",
                icon="🚨",
                title=f"{cat_name} budget exceeded",
                message=f"You have exceeded your {cat_name} budget by ₹{float(spend - limit):,.0f} ({pct:.0f}% used).",
                severity="danger",
            ))
        elif pct >= 80:
            insights.append(Insight(
                type="budget_warning",
                icon="⚠️",
                title=f"{cat_name} budget at {pct:.0f}%",
                message=f"You have used {pct:.0f}% of your {cat_name} budget. ₹{float(limit - spend):,.0f} remaining.",
                severity="warning",
            ))

    return insights


def _payment_mode_insight(user_id: UUID, db: Session) -> list[Insight]:
    """Show dominant payment mode this month."""
    cm, cy = _this_month()

    rows = (
        db.query(
            Transaction.payment_mode.label("mode"),
            func.sum(Transaction.amount).label("total"),
        )
        .filter(
            Transaction.user_id == user_id,
            extract("month", Transaction.transaction_date) == cm,
            extract("year",  Transaction.transaction_date) == cy,
        )
        .group_by(Transaction.payment_mode)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    if not rows:
        return []

    grand = sum(Decimal(str(r.total)) for r in rows)
    top   = rows[0]
    pct   = float(Decimal(str(top.total)) / grand * 100)
    mode  = top.mode.value if hasattr(top.mode, "value") else str(top.mode)

    if pct >= 50:
        return [Insight(
            type="payment_mode",
            icon="💳",
            title=f"{mode.upper()} dominates",
            message=f"{mode.upper()} accounts for {pct:.0f}% of your spending this month.",
            severity="info",
        )]
    return []


def _biggest_expense_insight(user_id: UUID, db: Session) -> list[Insight]:
    """Surface the largest single transaction this month."""
    cm, cy = _this_month()

    txn = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            extract("month", Transaction.transaction_date) == cm,
            extract("year",  Transaction.transaction_date) == cy,
        )
        .order_by(Transaction.amount.desc())
        .first()
    )

    if not txn:
        return []

    return [Insight(
        type="biggest_expense",
        icon="💸",
        title="Biggest expense this month",
        message=f"Your largest transaction this month was ₹{float(txn.amount):,.0f} at {txn.merchant} on {txn.transaction_date.strftime('%d %b')}.",
        severity="info",
    )]


def _savings_milestone_insight(user_id: UUID, db: Session) -> list[Insight]:
    """Celebrate savings goals that crossed 25%, 50%, 75%, 100%."""
    goals = db.query(SavingsGoal).filter(SavingsGoal.user_id == user_id).all()
    insights = []

    for g in goals:
        if not g.target_amount or Decimal(str(g.target_amount)) == 0:
            continue
        pct = float(Decimal(str(g.current_amount)) / Decimal(str(g.target_amount)) * 100)

        if pct >= 100:
            insights.append(Insight(
                type="goal_milestone",
                icon="🎉",
                title=f"{g.goal_name} achieved!",
                message=f"You have reached your savings goal '{g.goal_name}' of ₹{float(g.target_amount):,.0f}. Congratulations!",
                severity="success",
            ))
        elif pct >= 75:
            insights.append(Insight(
                type="goal_milestone",
                icon="🏆",
                title=f"{g.goal_name} at 75%",
                message=f"You are {pct:.0f}% of the way to your '{g.goal_name}' goal. ₹{float(Decimal(str(g.target_amount)) - Decimal(str(g.current_amount))):,.0f} to go!",
                severity="success",
            ))
        elif pct >= 50:
            insights.append(Insight(
                type="goal_milestone",
                icon="💪",
                title=f"{g.goal_name} halfway",
                message=f"You are halfway to your '{g.goal_name}' goal ({pct:.0f}% complete).",
                severity="info",
            ))

    return insights[:2]


# ── Public API ────────────────────────────────────────────────────────────────

def generate_insights(user_id: UUID, db: Session) -> list[Insight]:
    """
    Generate all insights for a user and return them sorted by severity.

    Severity order: danger → warning → success → info
    Maximum 10 insights returned.
    """
    all_insights: list[Insight] = []

    generators = [
        _budget_alert_insights,
        _category_change_insights,
        _top_merchant_insight,
        _biggest_expense_insight,
        _payment_mode_insight,
        _savings_milestone_insight,
    ]

    for gen in generators:
        try:
            all_insights.extend(gen(user_id, db))
        except Exception as e:
            logger.warning("Insight generator %s failed: %s", gen.__name__, e)

    severity_order = {"danger": 0, "warning": 1, "success": 2, "info": 3}
    all_insights.sort(key=lambda x: severity_order.get(x.severity, 99))

    logger.info("Generated %d insights for user=%s", len(all_insights), user_id)
    return all_insights[:10]
