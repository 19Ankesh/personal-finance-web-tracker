"""
Bank statement CSV parser.

Supports common Indian bank statement CSV formats:
  - HDFC Bank
  - ICICI Bank
  - Generic (auto-detected columns)

The parser auto-detects column positions by scanning header names, so it
is tolerant of minor variations across banks.

Column detection priority:
  date  → looks for 'date' in header
  desc  → looks for 'narration', 'description', 'particulars', 'details', 'remarks'
  debit → looks for 'withdrawal', 'debit', 'dr'

Only debit/withdrawal rows are returned. Credit/deposit rows are skipped.
"""
import io
import logging
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


# ── Constants ─────────────────────────────────────────────────────────────────

DATE_FORMATS = [
    "%d/%m/%y", "%d/%m/%Y",
    "%d-%m-%y", "%d-%m-%Y",
    "%Y-%m-%d", "%m/%d/%Y",
]

PAYMENT_MODE_KEYWORDS: dict[str, list[str]] = {
    "upi":          ["upi/", "upi-", "/upi", "-upi", "upi "],
    "net_banking":  ["neft", "rtgs", "imps", "netbanking", "net banking", "inb/"],
    "debit_card":   ["pos ", "nfs/", "nfs-", "atm/", "atm-", "atm ", "debit card"],
    "credit_card":  ["cc payment", "credit card"],
}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _parse_date(raw: str) -> Optional[date]:
    raw = str(raw).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _parse_amount(value) -> Optional[Decimal]:
    """Parse a possibly comma-formatted amount string to Decimal."""
    if pd.isna(value):
        return None
    cleaned = re.sub(r"[,\s]", "", str(value).strip())
    if not cleaned or cleaned.lower() in ("nan", "none", ""):
        return None
    try:
        d = Decimal(cleaned)
        return d if d > Decimal("0") else None
    except InvalidOperation:
        return None


def _infer_payment_mode(description: str) -> str:
    lower = description.lower()
    for mode, keywords in PAYMENT_MODE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return mode
    return "upi"


def _extract_merchant(description: str) -> str:
    """Extract a clean merchant name from a bank statement description."""
    cleaned = re.sub(r"\b\d{6,}\b", "", description)
    cleaned = re.sub(r"\b[A-Z]{4}\d{7}\b", "", cleaned)

    parts = re.split(r"[-/|@\\]", cleaned)
    parts = [p.strip() for p in parts if p.strip()]

    SKIP_TOKENS = {
        "upi", "neft", "rtgs", "imps", "pos", "atm", "nfs",
        "inb", "mb", "net", "cr", "dr", "ach", "si", "emi", "trf",
    }
    meaningful = [
        p for p in parts
        if p.lower() not in SKIP_TOKENS and len(p) > 1 and not p.isdigit()
    ]
    if meaningful:
        return meaningful[0].strip().title()
    return description.strip()[:50].title() or "Unknown"


def _detect_columns(df: pd.DataFrame) -> dict[str, str | None]:
    """
    Auto-detect column names for date, description, and debit amount.

    Returns:
        dict with keys: date_col, desc_col, debit_col  (values are actual
        DataFrame column names, or None if not found).
    """
    cols_lower: dict[str, str] = {c.lower().strip(): c for c in df.columns}

    date_col: str | None = next(
        (cols_lower[k] for k in cols_lower if "date" in k), None
    )
    desc_col: str | None = next(
        (
            cols_lower[k] for k in cols_lower
            if any(w in k for w in ("narration", "description", "particulars", "details", "remark"))
        ),
        None,
    )
    debit_col: str | None = next(
        (
            cols_lower[k] for k in cols_lower
            if any(w in k for w in ("withdrawal", "debit", " dr", "(dr)"))
        ),
        None,
    )

    return {"date_col": date_col, "desc_col": desc_col, "debit_col": debit_col}


# ── Public API ────────────────────────────────────────────────────────────────

def parse_csv(file_bytes: bytes) -> list[dict]:
    """
    Parse a bank statement CSV file and return debit transactions.

    The parser attempts to read the CSV skipping 0, 1, or 2 header rows to
    handle banks that prepend account info before the table starts.

    Args:
        file_bytes: Raw bytes of the uploaded CSV file.

    Returns:
        List of dicts, each with:
          ``date``         – :class:`datetime.date`
          ``merchant``     – str
          ``amount``       – :class:`decimal.Decimal` (positive)
          ``payment_mode`` – str
          ``notes``        – str (raw description, max 500 chars)

    Raises:
        ValueError: If the file cannot be parsed or required columns are missing.
    """
    df: pd.DataFrame | None = None

    # Try reading with increasing skip-row counts to handle junk header lines
    for skip in range(3):
        try:
            candidate = pd.read_csv(
                io.BytesIO(file_bytes),
                skiprows=skip,
                dtype=str,
                on_bad_lines="skip",
                encoding="utf-8",
            )
            if len(candidate.columns) >= 4:
                df = candidate
                break
        except Exception:
            continue

    if df is None:
        # Try latin-1 encoding (some Indian bank exports)
        try:
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                dtype=str,
                on_bad_lines="skip",
                encoding="latin-1",
            )
        except Exception as exc:
            raise ValueError(f"Could not read CSV file: {exc}") from exc

    # Strip column names of extra whitespace
    df.columns = [str(c).strip() for c in df.columns]

    cols = _detect_columns(df)

    if cols["date_col"] is None:
        raise ValueError(
            "Could not find a 'Date' column in the CSV. "
            "Please ensure the file has a column named 'Date'."
        )
    if cols["debit_col"] is None:
        raise ValueError(
            "Could not find a 'Withdrawal'/'Debit' column in the CSV. "
            "Please ensure the file has a 'Withdrawal Amt' or 'Debit' column."
        )

    # Fallback: use second column as description if not detected
    desc_col: str = cols["desc_col"] or df.columns[1]

    transactions: list[dict] = []

    for _, row in df.iterrows():
        date_raw  = str(row.get(cols["date_col"], "")).strip()
        desc_raw  = str(row.get(desc_col, "")).strip()
        debit_raw = row.get(cols["debit_col"])

        txn_date = _parse_date(date_raw)
        if txn_date is None:
            continue

        amount = _parse_amount(debit_raw)
        if amount is None:
            # Row has no debit — it's a credit/deposit or blank; skip it
            continue

        transactions.append({
            "date":         txn_date,
            "merchant":     _extract_merchant(desc_raw),
            "amount":       amount,
            "payment_mode": _infer_payment_mode(desc_raw),
            "notes":        desc_raw[:500],
        })

    logger.info("CSV parsed: %d debit transactions extracted", len(transactions))
    return transactions
