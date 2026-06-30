"""
HDFC Bank statement PDF parser.

Parses the standard HDFC Bank account/savings statement PDF exported
from HDFC NetBanking.

Typical HDFC table structure (7 columns):
  Date | Narration | Chq./Ref.No. | Value Dt | Withdrawal Amt.(Dr) | Deposit Amt.(Cr) | Closing Balance(INR)

Parsing rules:
  - Only debit/withdrawal rows are returned (expense tracking only).
  - Deposit rows (income/credits) are intentionally ignored.
  - Header rows, summary rows, and blank rows are skipped.
  - Malformed rows are logged and silently skipped.
  - Merchant name is extracted from the Narration field.
  - Payment mode is inferred from narration keywords.
"""
import io
import logging
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

import pdfplumber

logger = logging.getLogger(__name__)


# ── Constants ─────────────────────────────────────────────────────────────────

DATE_FORMATS = ["%d/%m/%y", "%d/%m/%Y", "%d-%m-%y", "%d-%m-%Y"]

# Payment mode inference from narration keywords (checked in order)
PAYMENT_MODE_KEYWORDS: dict[str, list[str]] = {
    "upi":          ["upi/", "upi-", "/upi", "-upi", "upi "],
    "net_banking":  ["neft", "rtgs", "imps", "netbanking", "net banking", "inb/", "inb-"],
    "debit_card":   ["pos ", "nfs/", "nfs-", "atm/", "atm-", "atm ", "debit card"],
    "credit_card":  ["cc payment", "credit card"],
}

# Row text patterns that indicate non-transaction rows to skip
SKIP_PATTERNS = [
    r"^opening balance",
    r"^closing balance",
    r"^total",
    r"^date$",
    r"^narration$",
    r"withdrawal amt",
    r"deposit amt",
    r"chq.*ref",
    r"value dt",
]


# ── Internal helpers ──────────────────────────────────────────────────────────

def _parse_date(raw: str) -> Optional[date]:
    """Try multiple date formats; return date or None."""
    raw = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _parse_amount(raw: str) -> Optional[Decimal]:
    """
    Parse an amount string like '1,234.56' into Decimal.
    Returns None if empty or zero.
    """
    if not raw or not raw.strip():
        return None
    cleaned = re.sub(r"[,\s]", "", raw.strip())
    try:
        value = Decimal(cleaned)
        return value if value > Decimal("0") else None
    except InvalidOperation:
        return None


def _infer_payment_mode(narration: str) -> str:
    """Determine payment mode from narration text keywords."""
    lower = narration.lower()
    for mode, keywords in PAYMENT_MODE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return mode
    return "upi"   # Most HDFC digital transactions are UPI


def _extract_merchant(narration: str) -> str:
    """
    Extract a clean, human-readable merchant name from an HDFC narration.

    HDFC narration examples:
      "UPI/CR/123456/SWIGGY/YESB0000001"     → "Swiggy"
      "UPI-DR-987654-ZOMATO LTD-OKSBI-note"  → "Zomato Ltd"
      "POS 123456789 AMAZON SELLER SERV"      → "Amazon Seller Serv"
      "NEFT-HDFC0001234-JOHN DOE-SALARY"      → "John Doe"
      "ATM/WDL/123456/SBI ATM"               → "Sbi Atm"

    Strategy:
      1. Remove long numeric ref numbers (phone / transaction IDs).
      2. Split on common delimiters (-, /, |, @).
      3. Drop known prefix tokens (UPI, NEFT, POS, etc.).
      4. Return first meaningful segment, title-cased.
    """
    # Remove long digit sequences (transaction IDs, phone numbers)
    cleaned = re.sub(r"\b\d{6,}\b", "", narration)
    # Remove bank/IFSC codes (4 letters + 7 digits pattern)
    cleaned = re.sub(r"\b[A-Z]{4}\d{7}\b", "", cleaned)

    parts = re.split(r"[-/|@\\]", cleaned)
    parts = [p.strip() for p in parts if p.strip()]

    SKIP_TOKENS = {
        "upi", "neft", "rtgs", "imps", "pos", "atm", "nfs",
        "inb", "mb", "net", "cr", "dr", "ach", "si", "emi",
        "wdl", "trf",
    }
    meaningful = [
        p for p in parts
        if p.lower() not in SKIP_TOKENS and len(p) > 1 and not p.isdigit()
    ]

    if meaningful:
        return meaningful[0].strip().title()

    # Fallback: first 50 chars of cleaned narration
    return narration.strip()[:50].title() or "Unknown"


def _is_skip_row(cells: list[str]) -> bool:
    """Return True if this row is a header, summary, or blank row."""
    text = " ".join(cells).lower().strip()
    if not text:
        return True
    return any(re.search(p, text) for p in SKIP_PATTERNS)


# ── Public API ────────────────────────────────────────────────────────────────

def parse_hdfc_pdf(file_bytes: bytes) -> list[dict]:
    """
    Parse a bank statement PDF (HDFC, ICICI, etc.) and return debit transactions.
    Auto-detects the table columns dynamically.
    """
    transactions: list[dict] = []

    # Persistent column indices in case of table continuation across pages
    date_idx: Optional[int] = None
    desc_idx: Optional[int] = None
    debit_idx: Optional[int] = None

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()

                if not tables:
                    logger.debug("PDF page %d: no tables found", page_num)
                    continue

                for table in tables:
                    for row in table:
                        if not row:
                            continue

                        # Normalise all cells to strings
                        cells = [str(c).strip() if c is not None else "" for c in row]

                        # Detect header row
                        cells_lower = [c.lower() for c in cells]
                        if any("date" in c for c in cells_lower) and any(any(w in c for w in ("narration", "description", "particulars", "details", "remark")) for c in cells_lower):
                            # Detect date column
                            date_idx = next((i for i, c in enumerate(cells_lower) if "date" in c), None)
                            # Detect description column
                            desc_idx = next((i for i, c in enumerate(cells_lower) if any(w in c for w in ("narration", "description", "particulars", "details", "remark"))), None)
                            # Detect debit/withdrawal column
                            debit_idx = next((i for i, c in enumerate(cells_lower) if any(w in c for w in ("withdrawal", "debit", " dr", "(dr)", "amount (inr)", "amount"))), None)

                            # Fallback if debit index wasn't found but there's a column with "withdrawal" or similar
                            if debit_idx is None:
                                debit_idx = next((i for i, c in enumerate(cells_lower) if "amt" in c or "amount" in c or "withdrawal" in c), None)

                            continue

                        # Skip header detection rows or other meta rows
                        if _is_skip_row(cells):
                            continue

                        # If indices are not detected yet, we can't parse
                        if date_idx is None or debit_idx is None:
                            continue

                        desc_col_idx = desc_idx if desc_idx is not None else (date_idx + 1 if date_idx + 1 < len(cells) else 1)

                        if len(cells) <= max(date_idx, desc_col_idx, debit_idx):
                            continue

                        date_str = cells[date_idx]
                        narration = cells[desc_col_idx]
                        withdrawal = cells[debit_idx]

                        txn_date = _parse_date(date_str)
                        if txn_date is None:
                            continue

                        amount = _parse_amount(withdrawal)
                        if amount is None:
                            continue

                        transactions.append({
                            "date":         txn_date,
                            "merchant":     _extract_merchant(narration),
                            "amount":       amount,
                            "payment_mode": _infer_payment_mode(narration),
                            "notes":        narration.strip()[:500],
                        })

    except ValueError:
        raise
    except Exception as exc:
        logger.error("PDF parsing error: %s", exc)
        raise ValueError(f"Could not parse PDF: {exc}") from exc

    logger.info("PDF parsed: %d debit transactions extracted", len(transactions))
    return transactions
