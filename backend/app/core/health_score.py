"""
Financial Health Score calculator.

Produces a 0–100 score from three weighted metrics:

  Budget Adherence   (40 pts) — how consistently the user stays under budgets
  Savings Progress   (30 pts) — average percentage of savings goals reached
  Spending Consistency (30 pts) — how stable monthly spending is month-over-month

Score bands:
  80–100  Excellent
  60–79   Good
  40–59   Average
  0–39    Needs Improvement

All calculations are pure SQL aggregations + Python arithmetic.
No external ML libraries required.
"""
import logging
import statistics
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.models import Budget, SavingsGoal, Transaction

logger = logging.getLogger(__name__)


# ── Response schema ───────────────────────────────────────────────────────────

class HealthScoreResponse(BaseModel):
    score:                int           # 0–100
    band:                 str           # Excellent / Good / Average / Needs Improvement
    band_color:           str           # emerald / blue / amber / red
    budget_adherence:     float         # 0–40 (contribution)
    savings_progress:     float         # 0–30
    spending_consistency: float         # 0–30
    details: dict                       # human-readable breakdown


# ── Band helpers ──────────────────────────────────────────────────────────────

def _band(score: int) -> tuple[str, str]:
    if score >= 80: return "Excellent",          "emerald"
    if score >= 60: return "Good",               "blue"
    if score >= 40: return "Average",            "amber"
    return              "Needs Improvement",  "red"


# ── Component calculators ─────────────────────────────────────────────────────

def _budget_adherence_score(user_id: UUID, db: Session) -> tuple[float, dict]:
    """
    Score (0–40): proportion of budgets where spending stayed ≤ limit.

    Looks at the last 3 months of budgets.
    Full marks (40) if all budgets respected.
    Zero if no budgets set (returns 20 as neutral default).
    """
    from datetime import date
    today = date.today()

    budgets = (
        db.query(Budget)
        .filter(
            Budget.user_id == user_id,
            # Last 3 months
            (Budget.year * 12 + Budget.month) >= (today.year * 12 + today.month - 3),
        )
        .all()
    )

    if not budgets:
        return 20.0, {"note": "No budgets set — score defaulted to 20/40", "total": 0, "respected": 0}

    respected = 0
    for b in budgets:
        spend = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.user_id == user_id,
            Transaction.category_id == b.category_id,
            extract("month", Transaction.transaction_date) == b.month,
            extract("year",  Transaction.transaction_date) == b.year,
        ).scalar() or Decimal("0")

        if Decimal(str(spend)) <= Decimal(str(b.budget_limit)):
            respected += 1

    pct   = respected / len(budgets)
    score = round(pct * 40, 1)
    return score, {
        "total":     len(budgets),
        "respected": respected,
        "pct":       round(pct * 100, 1),
    }


def _savings_progress_score(user_id: UUID, db: Session) -> tuple[float, dict]:
    """
    Score (0–30): average progress across all savings goals.

    progress = current_amount / target_amount × 100
    Full marks (30) if average progress ≥ 100%.
    Zero if no goals set (returns 15 as neutral default).
    """
    goals = db.query(SavingsGoal).filter(SavingsGoal.user_id == user_id).all()

    if not goals:
        return 15.0, {"note": "No savings goals set — score defaulted to 15/30", "total": 0}

    progresses = []
    for g in goals:
        if g.target_amount and Decimal(str(g.target_amount)) > 0:
            pct = float(Decimal(str(g.current_amount)) / Decimal(str(g.target_amount)) * 100)
            progresses.append(min(pct, 100.0))   # cap at 100

    if not progresses:
        return 15.0, {"note": "Goals have zero target amounts", "total": len(goals)}

    avg_pct = statistics.mean(progresses)
    score   = round(avg_pct / 100 * 30, 1)
    return score, {
        "total":       len(goals),
        "avg_pct":     round(avg_pct, 1),
        "progresses":  [round(p, 1) for p in progresses],
    }


def _spending_consistency_score(user_id: UUID, db: Session) -> tuple[float, dict]:
    """
    Score (0–30): how stable monthly spending is over the last 6 months.

    Uses coefficient of variation (CV = std_dev / mean).
    Lower CV = more consistent = higher score.

    CV thresholds:
      CV ≤ 0.10  → 30 pts  (very consistent)
      CV ≤ 0.25  → 24 pts
      CV ≤ 0.40  → 18 pts
      CV ≤ 0.60  → 12 pts
      CV > 0.60  → 6 pts  (very erratic)

    Returns 20 as neutral default if fewer than 2 months of data.
    """
    from datetime import date, timedelta
    six_months_ago = date.today() - timedelta(days=180)

    rows = (
        db.query(
            extract("year",  Transaction.transaction_date).label("yr"),
            extract("month", Transaction.transaction_date).label("mo"),
            func.sum(Transaction.amount).label("total"),
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= six_months_ago,
        )
        .group_by("yr", "mo")
        .all()
    )

    if len(rows) < 2:
        return 20.0, {"note": "Insufficient data (< 2 months) — defaulted to 20/30", "months": len(rows)}

    totals = [float(r.total) for r in rows]
    mean   = statistics.mean(totals)
    std    = statistics.stdev(totals)
    cv     = (std / mean) if mean > 0 else 1.0

    if   cv <= 0.10: score = 30.0
    elif cv <= 0.25: score = 24.0
    elif cv <= 0.40: score = 18.0
    elif cv <= 0.60: score = 12.0
    else:            score =  6.0

    return score, {
        "months":        len(totals),
        "mean_spend":    round(mean, 2),
        "std_dev":       round(std, 2),
        "cv":            round(cv, 3),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def calculate_health_score(user_id: UUID, db: Session) -> HealthScoreResponse:
    """
    Calculate and return the full financial health score for a user.

    Each component is calculated independently then summed.
    Maximum possible score is 100 (40 + 30 + 30).
    """
    budget_pts,      budget_detail      = _budget_adherence_score(user_id, db)
    savings_pts,     savings_detail     = _savings_progress_score(user_id, db)
    consistency_pts, consistency_detail = _spending_consistency_score(user_id, db)

    total = int(round(budget_pts + savings_pts + consistency_pts))
    total = max(0, min(100, total))   # clamp to 0–100

    band, color = _band(total)

    logger.info(
        "Health score: user=%s  score=%d  band=%s  budget=%.1f  savings=%.1f  consistency=%.1f",
        user_id, total, band, budget_pts, savings_pts, consistency_pts,
    )

    return HealthScoreResponse(
        score=total,
        band=band,
        band_color=color,
        budget_adherence=budget_pts,
        savings_progress=savings_pts,
        spending_consistency=consistency_pts,
        details={
            "budget_adherence":     budget_detail,
            "savings_progress":     savings_detail,
            "spending_consistency": consistency_detail,
        },
    )
