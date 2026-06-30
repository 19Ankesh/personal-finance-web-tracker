"""
Transaction API router.

All endpoints require JWT authentication.

Routes:
  POST   /transactions/voice    – create a transaction from voice transcript
  POST   /transactions/         – create a transaction (manual)
  GET    /transactions/         – list with filters + pagination
  GET    /transactions/{id}     – get single transaction
  PUT    /transactions/{id}     – update transaction
  DELETE /transactions/{id}     – delete transaction
"""
import logging
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.categorizer import categorize_merchant
from app.core.deps import get_current_user
from app.core.voice_parser import parse_voice_text
from app.db.session import get_db
from app.models.models import Category, PaymentMode, TransactionSource, User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from app.services.transaction_service import (
    create_transaction,
    delete_transaction,
    get_transaction,
    list_transactions,
    update_transaction,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Voice schemas ─────────────────────────────────────────────────────────────

class VoiceLogRequest(BaseModel):
    text: str

class VoiceLogResponse(BaseModel):
    parse_ok:    bool
    error:       str | None = None
    merchant:    str | None = None
    amount:      Decimal | None = None
    category:    str | None = None
    transaction: TransactionResponse | None = None

class VoiceParseResponse(BaseModel):
    parse_ok:         bool
    error:            str | None = None
    merchant:         str | None = None
    amount:           Decimal | None = None
    transaction_date: date | None = None
    payment_mode:     str | None = None
    category_id:      UUID | None = None
    category_name:    str | None = None
    notes:            str | None = None


# ── Voice endpoints (must be before /{transaction_id} to avoid routing clash) ──

@router.post(
    "/voice",
    response_model=VoiceLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log an expense from a voice transcript",
)
async def voice_log(
    data: VoiceLogRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VoiceLogResponse:
    """
    Parse a natural language voice transcript and create a transaction.

    Supported phrases:
      "spent 200 on lunch"  |  "paid 350 for Uber"
      "Swiggy 450"          |  "bought groceries for 800"

    Returns parse_ok=False with an error message if no amount found.
    """
    if not data.text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Voice transcript cannot be empty.",
        )

    parsed = parse_voice_text(data.text)

    if not parsed["parse_ok"]:
        return VoiceLogResponse(
            parse_ok=False,
            error=parsed["error"],
            merchant=parsed["merchant"],
        )

    category      = categorize_merchant(parsed["merchant"], current_user.id, db)
    if not category:
        # Check if any database category is explicitly mentioned in the voice text
        db_categories = db.query(Category).all()
        lower_text = data.text.lower()
        for cat in db_categories:
            cat_name_lower = cat.category_name.lower()
            if cat_name_lower in lower_text:
                category = cat
                break
            # Synonym matches for common categories
            if cat_name_lower == "food" and any(w in lower_text for w in ["dining", "restaurant", "lunch", "dinner", "breakfast", "cafe", "tea", "coffee"]):
                category = cat
                break
            if cat_name_lower == "transport" and any(w in lower_text for w in ["cab", "auto", "taxi", "travel", "fuel", "petrol", "diesel"]):
                category = cat
                break
            if cat_name_lower == "entertainment" and any(w in lower_text for w in ["movie", "show", "game", "netflix", "ott"]):
                category = cat
                break

    category_id   = category.id             if category else None
    category_name = category.category_name  if category else "Uncategorized"

    txn = create_transaction(
        TransactionCreate(
            merchant=parsed["merchant"],
            amount=parsed["amount"],
            transaction_date=parsed["transaction_date"],
            payment_mode=PaymentMode(parsed["payment_mode"]),
            source=TransactionSource.VOICE,
            notes=parsed["notes"],
            category_id=category_id,
        ),
        current_user.id,
        db,
    )

    logger.info(
        "Voice transaction: merchant=%r amount=%s category=%s user=%s",
        parsed["merchant"], parsed["amount"], category_name, current_user.id,
    )

    return VoiceLogResponse(
        parse_ok=True,
        merchant=parsed["merchant"],
        amount=parsed["amount"],
        category=category_name,
        transaction=txn,
    )


@router.post(
    "/voice/parse",
    response_model=VoiceParseResponse,
    summary="Parse a voice transcript without saving",
)
async def voice_parse(
    data: VoiceLogRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VoiceParseResponse:
    """
    Parse a voice transcript into fields (merchant, amount, category, mode) without database insertion.
    Allows user validation/editing on frontend.
    """
    if not data.text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Voice transcript cannot be empty.",
        )

    parsed = parse_voice_text(data.text)

    if not parsed["parse_ok"]:
        return VoiceParseResponse(
            parse_ok=False,
            error=parsed["error"],
            merchant=parsed["merchant"],
            amount=None,
            transaction_date=date.today(),
            payment_mode="upi",
            category_id=None,
            category_name="Uncategorized",
            notes=data.text,
        )

    category      = categorize_merchant(parsed["merchant"], current_user.id, db)
    if not category:
        # Check if any database category is explicitly mentioned in the voice text
        db_categories = db.query(Category).all()
        lower_text = data.text.lower()
        for cat in db_categories:
            cat_name_lower = cat.category_name.lower()
            if cat_name_lower in lower_text:
                category = cat
                break
            # Synonym matches for common categories
            if cat_name_lower == "food" and any(w in lower_text for w in ["dining", "restaurant", "lunch", "dinner", "breakfast", "cafe", "tea", "coffee"]):
                category = cat
                break
            if cat_name_lower == "transport" and any(w in lower_text for w in ["cab", "auto", "taxi", "travel", "fuel", "petrol", "diesel"]):
                category = cat
                break
            if cat_name_lower == "entertainment" and any(w in lower_text for w in ["movie", "show", "game", "netflix", "ott"]):
                category = cat
                break

    category_id   = category.id             if category else None
    category_name = category.category_name  if category else "Uncategorized"

    return VoiceParseResponse(
        parse_ok=True,
        error=None,
        merchant=parsed["merchant"],
        amount=parsed["amount"],
        transaction_date=parsed["transaction_date"],
        payment_mode=parsed["payment_mode"],
        category_id=category_id,
        category_name=category_name,
        notes=parsed["notes"],
    )


# ── Standard CRUD ─────────────────────────────────────────────────────────────

@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED, summary="Create a new transaction")
async def create(data: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> TransactionResponse:
    return create_transaction(data, current_user.id, db)


@router.get("/", response_model=TransactionListResponse, summary="List transactions with optional filters")
async def list_all(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    category_id: UUID | None = Query(default=None),
    payment_mode: PaymentMode | None = Query(default=None),
    merchant: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionListResponse:
    return list_transactions(
        user_id=current_user.id, db=db, skip=skip, limit=limit,
        category_id=category_id, payment_mode=payment_mode, merchant=merchant,
        date_from=date_from, date_to=date_to, search=search,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse, summary="Get a single transaction")
async def get(transaction_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> TransactionResponse:
    return get_transaction(transaction_id, current_user.id, db)


@router.put("/{transaction_id}", response_model=TransactionResponse, summary="Update a transaction")
async def update(transaction_id: UUID, data: TransactionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> TransactionResponse:
    return update_transaction(transaction_id, data, current_user.id, db)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a transaction")
async def delete(transaction_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    delete_transaction(transaction_id, current_user.id, db)
