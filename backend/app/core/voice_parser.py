"""
Voice expense parser.

Converts a natural language voice transcript into structured transaction fields.

Supported patterns (all case-insensitive):
  "spent 200 on lunch"
  "paid 350 for Uber"
  "Swiggy 450"
  "200 at Zomato"
  "bought groceries for 800"
  "paid 50 rupees for tea"
  "Uber ride cost 350"
  "spent 1500 on Amazon shopping"

Extraction targets:
  - amount   : first positive number found (strips commas, ignores 'rs'/'rupees')
  - merchant : keyword after on/for/at/from or a known merchant name
  - date     : always today (voice logging is real-time)
  - payment_mode: UPI (default for voice)
"""
import logging
import re
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)

# ── Known merchant keywords (for fallback detection) ─────────────────────────

KNOWN_MERCHANTS = [
    "swiggy", "zomato", "dominos", "pizza hut", "kfc", "mcdonald",
    "ola", "uber", "rapido", "namma metro",
    "amazon", "flipkart", "myntra", "meesho",
    "bigbasket", "blinkit", "zepto", "dmart",
    "airtel", "jio", "bsnl", "bescom", "bbmp",
    "pvr", "inox", "bookmyshow",
    "apollo", "medplus", "netmeds",
    "netflix", "spotify", "youtube", "hotstar",
    "gpay", "phonepe", "paytm",
    "irctc", "makemytrip", "oyo",
]

# Preposition patterns that precede merchant name
_MERCHANT_PREPS = r"(?:on|for|at|from|to|via)"

# Noise words to strip from merchant candidates
_NOISE = {
    "the", "a", "an", "some", "my", "our",
    "rs", "rupees", "inr", "₹",
    "spent", "paid", "bought", "purchased", "ordered", "got",
    "cost", "costs", "costing",
    "ride", "order", "bill", "payment", "recharge", "subscription",
}


NUM_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100, "thousand": 1000
}

def _words_to_number(text: str) -> Optional[Decimal]:
    """Parse word numbers like 'three hundred fifty' or 'fifty' to Decimal."""
    words = [w.lower().replace(",", "").replace("-", "") for w in text.split()]
    total = 0
    current = 0
    for w in words:
        if w in NUM_WORDS:
            val = NUM_WORDS[w]
            if val == 100:
                current = (current or 1) * 100
            elif val == 1000:
                total += (current or 1) * 1000
                current = 0
            else:
                current += val
    total += current
    return Decimal(total) if total > 0 else None


def _extract_amount(text: str) -> Optional[Decimal]:
    """
    Find the first number in the text and return it as Decimal.

    Handles:
      "200"      → 200
      "1,500"    → 1500
      "₹350"     → 350
      "rs 450"   → 450
      "fifty"    → 50
    """
    # Remove currency symbols so they don't break number parsing
    cleaned = re.sub(r"[₹$]", "", text)
    # Remove commas inside numbers (1,500 → 1500)
    cleaned = re.sub(r"(\d),(\d{3})", r"\1\2", cleaned)

    matches = re.findall(r"\d+(?:\.\d{1,2})?", cleaned)
    for m in matches:
        try:
            val = Decimal(m)
            if val > 0:
                return round(val, 2)
        except Exception:
            continue

    # Try converting spoken number words
    return _words_to_number(text)


def _extract_merchant(text: str) -> str:
    """
    Extract a merchant name from the voice transcript.

    Strategy:
      1. Check for a known merchant name anywhere in the text.
      2. Look for words after prepositions (on/for/at/from).
      3. Fall back to the first meaningful non-numeric word.
    """
    lower = text.lower()

    # Strategy 1: known merchant substring match
    for m in KNOWN_MERCHANTS:
        if m in lower:
            return m.title()

    # Strategy 2: word(s) after a preposition
    prep_match = re.search(
        rf"{_MERCHANT_PREPS}\s+([a-zA-Z][a-zA-Z\s]{{1,30}}?)(?:\s+(?:for|at|on|from|cost|costs|\d)|$)",
        text,
        re.IGNORECASE,
    )
    if prep_match:
        candidate = prep_match.group(1).strip()
        words = [w for w in candidate.split() if w.lower() not in _NOISE]
        if words:
            return " ".join(words[:3]).title()

    # Strategy 3: first non-noise, non-numeric word
    words = text.split()
    for word in words:
        clean = re.sub(r"[^a-zA-Z]", "", word)
        if clean and clean.lower() not in _NOISE and not clean.isdigit() and len(clean) > 2:
            return clean.title()

    return "Unknown"


def _detect_payment_mode(text: str) -> str:
    """Detect payment mode from the transcript, defaulting to upi."""
    lower = text.lower()
    if "cash" in lower:
        return "cash"
    if "credit" in lower or "cc" in lower:
        return "credit_card"
    if "debit" in lower:
        return "debit_card"
    if any(w in lower for w in ["net banking", "netbanking", "neft", "imps", "rtgs"]):
        return "net_banking"
    return "upi"


MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

def _detect_date(text: str) -> date:
    """Detect relative date words or absolute dates and return date, defaulting to today."""
    lower = text.lower()
    today = date.today()

    # 1. Day before yesterday
    if "day before yesterday" in lower:
        return today - timedelta(days=2)

    # 2. Yesterday
    if "yesterday" in lower:
        return today - timedelta(days=1)

    # 3. Last month relative day (e.g., "15th of last month" or "15 last month")
    last_month_match = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?last\s+month", lower)
    if last_month_match:
        try:
            day = int(last_month_match.group(1))
            if 1 <= day <= 31:
                year = today.year
                month = today.month - 1
                if month == 0:
                    month = 12
                    year -= 1
                return date(year, month, day)
        except ValueError:
            pass

    # 4. Specific Month and Day
    # Pattern A: "June 25", "June 25th", "June 2"
    pattern_a = re.search(
        r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?\b",
        lower
    )
    # Pattern B: "25 June", "25th June", "25th of June"
    pattern_b = re.search(
        r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b",
        lower
    )

    month_val = None
    day_val = None

    if pattern_a:
        month_str = pattern_a.group(1)
        day_str = pattern_a.group(2)
        month_val = MONTHS.get(month_str[:3])
        day_val = int(day_str)
    elif pattern_b:
        day_str = pattern_b.group(1)
        month_str = pattern_b.group(2)
        month_val = MONTHS.get(month_str[:3])
        day_val = int(day_str)

    if month_val is not None and day_val is not None:
        try:
            # Try to build the date for this year
            target_date = date(today.year, month_val, day_val)
            # If the resolved date is in the future, assume it was last year
            if target_date > today:
                target_date = date(today.year - 1, month_val, day_val)
            return target_date
        except ValueError:
            pass

    return today


def parse_voice_text(text: str) -> dict:
    """
    Parse a voice transcript into transaction fields.

    Args:
        text: Raw transcript string from Web Speech API.

    Returns:
        dict with keys:
          amount        – Decimal or None
          merchant      – str
          transaction_date – date
          payment_mode  – str
          notes         – str (original transcript)
          parse_ok      – bool
          error         – str | None
    """
    text = text.strip()
    logger.info("Voice parser: input=%r", text)

    amount   = _extract_amount(text)
    merchant = _extract_merchant(text)
    txn_date = _detect_date(text)
    pay_mode = _detect_payment_mode(text)

    if amount is None:
        logger.warning("Voice parser: could not extract amount from %r", text)
        return {
            "amount":           None,
            "merchant":         merchant,
            "transaction_date": txn_date,
            "payment_mode":     pay_mode,
            "notes":            text,
            "parse_ok":         False,
            "error":            "Could not find an amount in your message. Try saying 'spent 200 on lunch'.",
        }

    logger.info(
        "Voice parser: amount=%s  merchant=%r  date=%s  mode=%s",
        amount, merchant, txn_date, pay_mode
    )
    return {
        "amount":           amount,
        "merchant":         merchant,
        "transaction_date": txn_date,
        "payment_mode":     pay_mode,
        "notes":            text,
        "parse_ok":         True,
        "error":            None,
    }
