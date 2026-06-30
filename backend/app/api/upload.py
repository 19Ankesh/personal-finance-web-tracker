"""
Upload API router.

Routes:
  POST /upload/csv  – Upload a bank statement CSV file
  POST /upload/pdf  – Upload an HDFC bank statement PDF file

Flow for each upload:
  1. Read uploaded file bytes
  2. Parse using the appropriate parser (CSV or PDF)
  3. For each parsed row, run the categorization engine
  4. Bulk-insert Transaction records into the database
  5. Return UploadSummaryResponse with counts and created transactions

All endpoints require JWT authentication.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.categorizer import categorize_merchant
from app.core.parser_csv import parse_csv
from app.core.parser_pdf import parse_hdfc_pdf
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.models import PaymentMode, Transaction, TransactionSource, User
from app.schemas.transaction import TransactionResponse
from app.schemas.upload import UploadSummaryResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Allowed MIME types
_CSV_CONTENT_TYPES = {"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain"}
_PDF_CONTENT_TYPES = {"application/pdf"}
_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _payment_mode_from_str(mode_str: str) -> PaymentMode:
    """Safely convert a string to PaymentMode enum, defaulting to UPI."""
    try:
        return PaymentMode(mode_str)
    except ValueError:
        return PaymentMode.UPI


async def _process_rows(
    parsed_rows: list[dict],
    source: TransactionSource,
    current_user: User,
    db: Session,
) -> UploadSummaryResponse:
    """
    Categorize and persist a list of parsed transaction rows.

    Args:
        parsed_rows:  Output from parse_csv() or parse_hdfc_pdf().
        source:       TransactionSource.CSV or TransactionSource.PDF.
        current_user: Authenticated user.
        db:           Active database session.

    Returns:
        UploadSummaryResponse with counts and created transactions.
    """
    imported: list[Transaction] = []
    skipped = 0
    categorized = 0

    for row in parsed_rows:
        try:
            # Auto-categorize merchant
            category = categorize_merchant(
                merchant_name=row["merchant"],
                user_id=current_user.id,
                db=db,
            )
            category_id = category.id if category else None
            if category_id is not None:
                categorized += 1

            txn = Transaction(
                user_id=current_user.id,
                category_id=category_id,
                merchant=row["merchant"],
                amount=row["amount"],
                transaction_date=row["date"],
                payment_mode=_payment_mode_from_str(row["payment_mode"]),
                source=source,
                notes=row.get("notes"),
            )
            db.add(txn)
            imported.append(txn)

        except Exception as exc:
            logger.warning("Skipped row during import: %s | row=%s", exc, row)
            skipped += 1

    db.commit()

    # Refresh all to populate IDs and relationships
    for txn in imported:
        db.refresh(txn)

    source_label = "csv" if source == TransactionSource.CSV else "pdf"
    logger.info(
        "Upload complete: source=%s parsed=%d imported=%d skipped=%d categorized=%d",
        source_label, len(parsed_rows), len(imported), skipped, categorized,
    )

    return UploadSummaryResponse(
        total_parsed=len(parsed_rows),
        total_imported=len(imported),
        total_skipped=skipped,
        categorized=categorized,
        uncategorized=len(imported) - categorized,
        source=source_label,
        transactions=[TransactionResponse.model_validate(t) for t in imported],
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/csv",
    response_model=UploadSummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a bank statement CSV",
)
async def upload_csv(
    file: UploadFile = File(..., description="Bank statement CSV file (max 10 MB)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadSummaryResponse:
    """
    Import transactions from a CSV bank statement.

    Supported banks: HDFC, ICICI, and generic CSV formats with
    Date / Description / Withdrawal columns.

    - Only **debit/withdrawal** rows are imported.
    - Each merchant is automatically matched against known mappings.
    - Unrecognized merchants are saved as **Uncategorized** — assign them
      via `POST /merchant-mappings/` to auto-categorize future imports.
    """
    # Validate file size
    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the 10 MB size limit.",
        )

    # Parse
    try:
        parsed_rows = parse_csv(content)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    if not parsed_rows:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No debit transactions found in the uploaded CSV.",
        )

    return await _process_rows(
        parsed_rows=parsed_rows,
        source=TransactionSource.CSV,
        current_user=current_user,
        db=db,
    )


@router.post(
    "/pdf",
    response_model=UploadSummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an HDFC bank statement PDF",
)
async def upload_pdf(
    file: UploadFile = File(..., description="HDFC bank statement PDF (max 10 MB)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadSummaryResponse:
    """
    Import transactions from an HDFC Bank account statement PDF.

    The PDF must be the standard HDFC NetBanking export format with
    the 7-column transaction table.

    - Only **debit/withdrawal** rows are imported.
    - Merchants are auto-categorized using the mapping engine.
    - Unrecognized merchants are saved as **Uncategorized**.
    """
    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the 10 MB size limit.",
        )

    # Validate PDF magic bytes
    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file does not appear to be a valid PDF.",
        )

    try:
        parsed_rows = parse_hdfc_pdf(content)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    if not parsed_rows:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No debit transactions found in the uploaded PDF.",
        )

    return await _process_rows(
        parsed_rows=parsed_rows,
        source=TransactionSource.PDF,
        current_user=current_user,
        db=db,
    )
