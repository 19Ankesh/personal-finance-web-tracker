"""
Budgets API router.

Routes:
  POST   /budgets/       — create a monthly category budget
  GET    /budgets/       — list budgets (filter by month/year)
  GET    /budgets/{id}   — get single budget + live spend metrics
  PUT    /budgets/{id}   — update budget limit
  DELETE /budgets/{id}   — delete budget

All endpoints require JWT authentication.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.budget import BudgetCreate, BudgetUpdate
from app.services.budget_service import (
    BudgetWithSpendResponse,
    create_budget,
    delete_budget,
    get_budget,
    list_budgets,
    update_budget,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=BudgetWithSpendResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a monthly budget for a category",
)
async def create(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BudgetWithSpendResponse:
    """
    Set a monthly spending limit for a category.

    - One budget per (category, month, year) per user.
    - Returns 409 if a budget already exists — use PUT to update it.
    - Response includes live `current_spend`, `remaining`, and `utilization_pct`.
    """
    return create_budget(data, current_user.id, db)


@router.get(
    "/",
    response_model=list[BudgetWithSpendResponse],
    summary="List budgets with live spend metrics",
)
async def list_all(
    month: int | None = Query(default=None, ge=1, le=12, description="Filter by month (1–12)"),
    year:  int | None = Query(default=None, ge=2000, le=2100, description="Filter by year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BudgetWithSpendResponse]:
    """
    List all budgets for the current user.

    Each budget includes real-time metrics:
    - `current_spend` — total spent in that category this month
    - `remaining`     — budget_limit minus current_spend
    - `utilization_pct` — percentage of budget used
    """
    return list_budgets(current_user.id, db, month, year)


@router.get(
    "/{budget_id}",
    response_model=BudgetWithSpendResponse,
    summary="Get a single budget with live metrics",
)
async def get(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BudgetWithSpendResponse:
    """Fetch one budget by UUID. Returns 404 if not found or not owned by user."""
    return get_budget(budget_id, current_user.id, db)


@router.put(
    "/{budget_id}",
    response_model=BudgetWithSpendResponse,
    summary="Update a budget's limit",
)
async def update(
    budget_id: UUID,
    data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BudgetWithSpendResponse:
    """Update the spending limit for an existing budget."""
    return update_budget(budget_id, data, current_user.id, db)


@router.delete(
    "/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a budget",
)
async def delete(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Permanently delete a budget. Returns 204 No Content on success."""
    delete_budget(budget_id, current_user.id, db)
