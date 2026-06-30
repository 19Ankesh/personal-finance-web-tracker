"""
Budget service layer.

Provides full CRUD for monthly category budgets plus real-time spend
calculation so the API always returns how much has been spent vs the limit.

Business rules:
  - One budget per (user, category, month, year) — enforced in create.
  - current_spend is computed live from the transactions table.
  - remaining = budget_limit - current_spend  (can be negative = over budget)
  - utilization_pct = current_spend / budget_limit × 100
"""
import logging
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import extract, func
from sqlalchemy.orm import Session, joinedload

from app.models.models import Budget, Category, Transaction
from app.schemas.budget import BudgetCreate, BudgetResponse, BudgetUpdate

logger = logging.getLogger(__name__)


# ── Extended response schema (defined here to avoid circular imports) ─────────

from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.schemas.budget import BudgetResponse
from app.schemas.category import CategoryResponse


class BudgetWithSpendResponse(BudgetResponse):
    """
    Budget data enriched with live spend metrics.

    Extends BudgetResponse with four computed fields derived by joining
    the budgets table with the transactions table.
    """

    category_name: str = "Uncategorized"
    current_spend: Decimal = Decimal("0.00")
    remaining: Decimal = Decimal("0.00")
    utilization_pct: float = 0.0


# ── Internal helpers ──────────────────────────────────────────────────────────


def _fetch_budget(budget_id: UUID, user_id: UUID, db: Session) -> Budget:
    budget: Budget | None = (
        db.query(Budget)
        .options(joinedload(Budget.category))          # ← eager load category
        .filter(Budget.id == budget_id, Budget.user_id == user_id)
        .first()
    )
    if budget is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found.",
        )
    return budget


def _compute_spend(budget: Budget, db: Session) -> Decimal:
    """Sum all transactions for this user+category+month+year."""
    result = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == budget.user_id,
            Transaction.category_id == budget.category_id,
            extract("month", Transaction.transaction_date) == budget.month,
            extract("year",  Transaction.transaction_date) == budget.year,
        )
        .scalar()
    )
    return Decimal(str(result)) if result is not None else Decimal("0.00")


def _enrich(budget: Budget, db: Session) -> BudgetWithSpendResponse:
    """Attach live spend metrics to a Budget ORM object."""
    current_spend = _compute_spend(budget, db)
    limit = Decimal(str(budget.budget_limit))
    remaining = limit - current_spend
    utilization = float(current_spend / limit * 100) if limit > 0 else 0.0
    # category is already eagerly loaded — safe to access on a closed session
    category_name = budget.category.category_name if budget.category else "Uncategorized"

    base = BudgetResponse.model_validate(budget)
    return BudgetWithSpendResponse(
        **base.model_dump(),
        category_name=category_name,
        current_spend=round(current_spend, 2),
        remaining=round(remaining, 2),
        utilization_pct=round(utilization, 2),
    )


# ── CRUD operations ───────────────────────────────────────────────────────────


def create_budget(data: BudgetCreate, user_id: UUID, db: Session) -> BudgetWithSpendResponse:
    """
    Create a monthly budget for a category.

    Raises:
        HTTPException 404 – if category does not exist.
        HTTPException 409 – if a budget already exists for this category/month/year.
    """
    # Validate category
    category: Category | None = (
        db.query(Category).filter(Category.id == data.category_id).first()
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )

    # Uniqueness check
    existing: Budget | None = (
        db.query(Budget)
        .filter(
            Budget.user_id == user_id,
            Budget.category_id == data.category_id,
            Budget.month == data.month,
            Budget.year == data.year,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A budget for this category already exists for "
                f"{data.month:02d}/{data.year}. Use PUT to update it."
            ),
        )

    budget = Budget(
        user_id=user_id,
        category_id=data.category_id,
        budget_limit=data.budget_limit,
        month=data.month,
        year=data.year,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    # Reload with category eagerly
    budget = _fetch_budget(budget.id, user_id, db)
    logger.info("Budget created: id=%s user=%s %02d/%d", budget.id, user_id, data.month, data.year)
    return _enrich(budget, db)


def list_budgets(
    user_id: UUID,
    db: Session,
    month: int | None = None,
    year: int | None = None,
) -> list[BudgetWithSpendResponse]:
    """
    List all budgets for a user, optionally filtered by month and/or year.

    Each budget includes live current_spend and utilization metrics.
    """
    query = (
        db.query(Budget)
        .options(joinedload(Budget.category))          # ← eager load category
        .filter(Budget.user_id == user_id)
    )
    if month is not None:
        query = query.filter(Budget.month == month)
    if year is not None:
        query = query.filter(Budget.year == year)
    budgets = query.order_by(Budget.year.desc(), Budget.month.desc()).all()
    return [_enrich(b, db) for b in budgets]


def get_budget(budget_id: UUID, user_id: UUID, db: Session) -> BudgetWithSpendResponse:
    """Fetch a single budget with live spend metrics."""
    budget = _fetch_budget(budget_id, user_id, db)
    return _enrich(budget, db)


def update_budget(
    budget_id: UUID,
    data: BudgetUpdate,
    user_id: UUID,
    db: Session,
) -> BudgetWithSpendResponse:
    """Update a budget's limit. Only budget_limit can be changed."""
    budget = _fetch_budget(budget_id, user_id, db)
    if data.budget_limit is not None:
        budget.budget_limit = data.budget_limit
    db.commit()
    db.refresh(budget)
    # Reload with category eagerly after refresh
    budget = _fetch_budget(budget.id, user_id, db)
    logger.info("Budget updated: id=%s user=%s new_limit=%s", budget_id, user_id, data.budget_limit)
    return _enrich(budget, db)


def delete_budget(budget_id: UUID, user_id: UUID, db: Session) -> None:
    """Delete a budget permanently."""
    budget = _fetch_budget(budget_id, user_id, db)
    db.delete(budget)
    db.commit()
    logger.info("Budget deleted: id=%s user=%s", budget_id, user_id)
