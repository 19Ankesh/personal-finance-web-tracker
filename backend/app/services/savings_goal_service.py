"""
Savings Goal service layer.

Provides full CRUD for savings goals. The ``progress_percentage``
computed field is handled by the Pydantic schema (SavingsGoalResponse),
so this service just manages persistence.
"""
import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import SavingsGoal
from app.schemas.savings_goal import (
    SavingsGoalCreate,
    SavingsGoalResponse,
    SavingsGoalUpdate,
)

logger = logging.getLogger(__name__)


def _fetch_goal(goal_id: UUID, user_id: UUID, db: Session) -> SavingsGoal:
    goal: SavingsGoal | None = (
        db.query(SavingsGoal)
        .filter(SavingsGoal.id == goal_id, SavingsGoal.user_id == user_id)
        .first()
    )
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Savings goal not found.",
        )
    return goal


def create_savings_goal(
    data: SavingsGoalCreate,
    user_id: UUID,
    db: Session,
) -> SavingsGoalResponse:
    """Create a new savings goal for the authenticated user."""
    goal = SavingsGoal(
        user_id=user_id,
        goal_name=data.goal_name,
        target_amount=data.target_amount,
        current_amount=data.current_amount,
        target_date=data.target_date,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    logger.info(
        "Savings goal created: id=%s user=%s name=%r target=%s",
        goal.id, user_id, goal.goal_name, goal.target_amount,
    )
    return SavingsGoalResponse.model_validate(goal)


def list_savings_goals(
    user_id: UUID,
    db: Session,
) -> list[SavingsGoalResponse]:
    """Return all savings goals for the user, newest first."""
    goals: list[SavingsGoal] = (
        db.query(SavingsGoal)
        .filter(SavingsGoal.user_id == user_id)
        .order_by(SavingsGoal.created_at.desc())
        .all()
    )
    return [SavingsGoalResponse.model_validate(g) for g in goals]


def get_savings_goal(
    goal_id: UUID,
    user_id: UUID,
    db: Session,
) -> SavingsGoalResponse:
    """Fetch a single savings goal (must belong to user)."""
    goal = _fetch_goal(goal_id, user_id, db)
    return SavingsGoalResponse.model_validate(goal)


def update_savings_goal(
    goal_id: UUID,
    data: SavingsGoalUpdate,
    user_id: UUID,
    db: Session,
) -> SavingsGoalResponse:
    """
    Partially update a savings goal.

    Common use case: update current_amount as the user saves money.
    All fields are optional — only provided fields are changed.
    """
    goal = _fetch_goal(goal_id, user_id, db)
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    logger.info("Savings goal updated: id=%s user=%s", goal_id, user_id)
    return SavingsGoalResponse.model_validate(goal)


def delete_savings_goal(
    goal_id: UUID,
    user_id: UUID,
    db: Session,
) -> None:
    """Permanently delete a savings goal."""
    goal = _fetch_goal(goal_id, user_id, db)
    db.delete(goal)
    db.commit()
    logger.info("Savings goal deleted: id=%s user=%s", goal_id, user_id)
