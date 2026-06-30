"""
Savings Goals API router.

Routes:
  POST   /savings-goals/       — create a savings goal
  GET    /savings-goals/       — list all goals
  GET    /savings-goals/{id}   — get single goal (includes progress_percentage)
  PUT    /savings-goals/{id}   — update goal
  DELETE /savings-goals/{id}   — delete goal

All endpoints require JWT authentication.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.savings_goal import (
    SavingsGoalCreate,
    SavingsGoalResponse,
    SavingsGoalUpdate,
)
from app.services.savings_goal_service import (
    create_savings_goal,
    delete_savings_goal,
    get_savings_goal,
    list_savings_goals,
    update_savings_goal,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=SavingsGoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a savings goal",
)
async def create(
    data: SavingsGoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavingsGoalResponse:
    """
    Create a new savings target.

    - `target_date` is optional (open-ended goals are allowed).
    - Response includes `progress_percentage` computed from
      `current_amount / target_amount × 100`.
    """
    return create_savings_goal(data, current_user.id, db)


@router.get(
    "/",
    response_model=list[SavingsGoalResponse],
    summary="List all savings goals",
)
async def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SavingsGoalResponse]:
    """Return all savings goals for the current user, newest first."""
    return list_savings_goals(current_user.id, db)


@router.get(
    "/{goal_id}",
    response_model=SavingsGoalResponse,
    summary="Get a single savings goal",
)
async def get(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavingsGoalResponse:
    """Fetch one savings goal by UUID. Returns 404 if not found or not owned."""
    return get_savings_goal(goal_id, current_user.id, db)


@router.put(
    "/{goal_id}",
    response_model=SavingsGoalResponse,
    summary="Update a savings goal",
)
async def update(
    goal_id: UUID,
    data: SavingsGoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavingsGoalResponse:
    """
    Partially update a savings goal.

    All fields are optional. Common use case:

    ```json
    { "current_amount": 15000.00 }
    ```

    Updates only `current_amount`; all other fields remain unchanged.
    """
    return update_savings_goal(goal_id, data, current_user.id, db)


@router.delete(
    "/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a savings goal",
)
async def delete(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Permanently delete a savings goal. Returns 204 No Content on success."""
    delete_savings_goal(goal_id, current_user.id, db)
