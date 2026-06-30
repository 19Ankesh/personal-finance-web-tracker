"""
Pydantic schemas for file upload responses and merchant mapping endpoints.
"""
from typing import List

from pydantic import BaseModel

from app.schemas.transaction import TransactionResponse


class UploadSummaryResponse(BaseModel):
    """
    Returned after a successful CSV or PDF upload.

    Gives a breakdown of what was parsed vs imported, and how many
    transactions were automatically categorized.
    """

    total_parsed: int
    """Number of debit rows found in the uploaded file."""

    total_imported: int
    """Number of transactions successfully saved to the database."""

    total_skipped: int
    """Rows that were malformed or failed validation (not saved)."""

    categorized: int
    """Transactions that were automatically assigned a category."""

    uncategorized: int
    """Transactions saved without a category (user must assign manually)."""

    source: str
    """Import source: 'csv' or 'pdf'."""

    transactions: List[TransactionResponse]
    """The newly created transaction objects."""
