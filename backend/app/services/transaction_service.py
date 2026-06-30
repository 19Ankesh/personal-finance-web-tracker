"""
Transaction service layer.

All business logic for transaction CRUD, filtering, and search lives here.
Routers call these functions and never touch the DB directly.
"""
import logging
from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.models import Category, PaymentMode, Transaction, TransactionSource
from app.schemas.transaction import (
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)

logger = logging.getLogger(__name__)


# ── Internal helpers ──────────────────────────────────────────────────────────


def _fetch_transaction(
    transaction_id: UUID,
    user_id: UUID,
    db: Session,
) -> Transaction:
    """
    Return the transaction owned by ``user_id``, or raise 404.

    This helper enforces row-level ownership — users can never access
    another user's transactions even if they know the UUID.
    """
    txn: Transaction | None = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
        .first()
    )
    if txn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found.",
        )
    return txn


def _validate_category(
    category_id: UUID,
    user_id: UUID,
    db: Session,
) -> None:
    """
    Ensure ``category_id`` belongs to the user or is a global default.

    Raises:
        HTTPException 404 – if the category does not exist or is not accessible.
    """
    category: Category | None = (
        db.query(Category)
        .filter(
            Category.id == category_id,
            or_(Category.user_id == user_id, Category.user_id.is_(None)),
        )
        .first()
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )


# ── CRUD operations ───────────────────────────────────────────────────────────


def create_transaction(
    data: TransactionCreate,
    user_id: UUID,
    db: Session,
) -> TransactionResponse:
    """Create and persist a new transaction for ``user_id``."""
    if data.category_id is not None:
        _validate_category(data.category_id, user_id, db)

    txn = Transaction(
        user_id=user_id,
        category_id=data.category_id,
        merchant=data.merchant.strip(),
        amount=data.amount,
        transaction_date=data.transaction_date,
        payment_mode=data.payment_mode,
        source=data.source,
        notes=data.notes,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    logger.info("Transaction created: id=%s user=%s merchant=%s", txn.id, user_id, txn.merchant)
    return TransactionResponse.model_validate(txn)


def get_transaction(
    transaction_id: UUID,
    user_id: UUID,
    db: Session,
) -> TransactionResponse:
    """Fetch a single transaction by ID (must belong to ``user_id``)."""
    txn = _fetch_transaction(transaction_id, user_id, db)
    return TransactionResponse.model_validate(txn)


def update_transaction(
    transaction_id: UUID,
    data: TransactionUpdate,
    user_id: UUID,
    db: Session,
) -> TransactionResponse:
    """
    Partially update a transaction.

    Only fields present in the request body are updated (model_dump exclude_unset).
    """
    txn = _fetch_transaction(transaction_id, user_id, db)

    update_fields = data.model_dump(exclude_unset=True)

    if "category_id" in update_fields and update_fields["category_id"] is not None:
        _validate_category(update_fields["category_id"], user_id, db)

    for field, value in update_fields.items():
        setattr(txn, field, value)

    db.commit()
    db.refresh(txn)
    logger.info("Transaction updated: id=%s user=%s", txn.id, user_id)
    return TransactionResponse.model_validate(txn)


def delete_transaction(
    transaction_id: UUID,
    user_id: UUID,
    db: Session,
) -> None:
    """Delete a transaction (must belong to ``user_id``)."""
    txn = _fetch_transaction(transaction_id, user_id, db)
    db.delete(txn)
    db.commit()
    logger.info("Transaction deleted: id=%s user=%s", transaction_id, user_id)


# ── List / search / filter ────────────────────────────────────────────────────


def list_transactions(
    user_id: UUID,
    db: Session,
    skip: int = 0,
    limit: int = 20,
    category_id: UUID | None = None,
    payment_mode: PaymentMode | None = None,
    merchant: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
) -> TransactionListResponse:
    """
    Return a paginated, filtered list of transactions for ``user_id``.

    Filters (all optional, combinable):
      - category_id   – exact category match
      - payment_mode  – exact payment mode match
      - merchant      – case-insensitive partial match on merchant name
      - date_from     – transactions on or after this date
      - date_to       – transactions on or before this date
      - search        – case-insensitive substring search in merchant + notes

    Results are ordered by transaction_date DESC, created_at DESC.
    ``limit`` is capped at 100 regardless of the requested value.
    """
    query = db.query(Transaction).filter(Transaction.user_id == user_id)

    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)

    if payment_mode is not None:
        query = query.filter(Transaction.payment_mode == payment_mode)

    if merchant is not None:
        query = query.filter(Transaction.merchant.ilike(f"%{merchant.strip()}%"))

    if date_from is not None:
        query = query.filter(Transaction.transaction_date >= date_from)

    if date_to is not None:
        query = query.filter(Transaction.transaction_date <= date_to)

    if search is not None:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Transaction.merchant.ilike(term),
                Transaction.notes.ilike(term),
            )
        )

    total: int = query.count()

    transactions: list[Transaction] = (
        query.order_by(
            Transaction.transaction_date.desc(),
            Transaction.created_at.desc(),
        )
        .offset(skip)
        .limit(min(limit, 100))
        .all()
    )

    return TransactionListResponse(
        items=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        skip=skip,
        limit=limit,
    )
