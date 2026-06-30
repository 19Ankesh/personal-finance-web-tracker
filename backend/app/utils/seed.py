"""
FinSense database seeder.

Run from the backend/ directory::

    python -m app.utils.seed

What it creates:
  1. 8 default categories (global, user_id = NULL)
  2. 16 default merchant mappings (global, user_id = NULL)
  3. 1 demo user  →  demo@finsense.com / demo123
  4. 500–700 realistic Indian transactions over the last 6 months

The script is idempotent — re-running it when data already exists is safe.
"""
import logging
import random
import sys
import os
from datetime import date, timedelta
from decimal import Decimal

# Allow running as `python -m app.utils.seed` from backend/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.models import (
    Category,
    MerchantMapping,
    PaymentMode,
    Transaction,
    TransactionSource,
    User,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ── Seed configuration ────────────────────────────────────────────────────────

DEFAULT_CATEGORIES: list[str] = [
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Groceries",
    "Entertainment",
    "Health",
    "Education",
]

# merchant_key (lowercase) → category name
MERCHANT_CATEGORY_MAP: dict[str, str] = {
    "swiggy": "Food",
    "zomato": "Food",
    "dominos": "Food",
    "ola": "Transport",
    "uber": "Transport",
    "rapido": "Transport",
    "amazon": "Shopping",
    "flipkart": "Shopping",
    "airtel": "Bills",
    "jio": "Bills",
    "bescom": "Bills",
    "bigbasket": "Groceries",
    "blinkit": "Groceries",
    "pvr": "Entertainment",
    "bookmyshow": "Entertainment",
    "apollo pharmacy": "Health",
}

# Display-friendly merchant names (stored in transaction.merchant)
MERCHANT_DISPLAY: dict[str, str] = {
    "swiggy": "Swiggy",
    "zomato": "Zomato",
    "dominos": "Dominos",
    "ola": "Ola",
    "uber": "Uber",
    "rapido": "Rapido",
    "amazon": "Amazon",
    "flipkart": "Flipkart",
    "airtel": "Airtel",
    "jio": "Jio",
    "bescom": "BESCOM",
    "bigbasket": "BigBasket",
    "blinkit": "Blinkit",
    "pvr": "PVR",
    "bookmyshow": "BookMyShow",
    "apollo pharmacy": "Apollo Pharmacy",
}

# Realistic INR amount ranges per merchant
MERCHANT_AMOUNT_RANGE: dict[str, tuple[int, int]] = {
    "swiggy":          (80,  600),
    "zomato":          (80,  600),
    "dominos":         (150, 800),
    "ola":             (50,  500),
    "uber":            (50,  500),
    "rapido":          (30,  200),
    "amazon":          (200, 5000),
    "flipkart":        (200, 5000),
    "airtel":          (199, 999),
    "jio":             (149, 499),
    "bescom":          (500, 3000),
    "bigbasket":       (300, 2000),
    "blinkit":         (100, 1000),
    "pvr":             (200, 600),
    "bookmyshow":      (150, 500),
    "apollo pharmacy": (50,  2000),
}

# Weighted payment mode distribution
PAYMENT_MODE_WEIGHTS: list[tuple[PaymentMode, int]] = [
    (PaymentMode.UPI,         60),
    (PaymentMode.DEBIT_CARD,  20),
    (PaymentMode.CREDIT_CARD, 15),
    (PaymentMode.CASH,         5),
]

# Weighted source distribution
SOURCE_WEIGHTS: list[tuple[TransactionSource, int]] = [
    (TransactionSource.MANUAL, 50),
    (TransactionSource.CSV,    20),
    (TransactionSource.PDF,    20),
    (TransactionSource.VOICE,  10),
]

DEMO_EMAIL    = "demo@finsense.com"
DEMO_PASSWORD = "demo123"
DEMO_NAME     = "Demo User"


# ── Utilities ─────────────────────────────────────────────────────────────────

def _weighted_choice(distribution: list[tuple]) -> object:
    """Pick one item from a weighted list of (value, weight) pairs."""
    total = sum(w for _, w in distribution)
    r = random.uniform(0, total)
    cumulative = 0
    for item, weight in distribution:
        cumulative += weight
        if r <= cumulative:
            return item
    return distribution[-1][0]


# ── Seeder ────────────────────────────────────────────────────────────────────

def seed_database() -> None:
    """Run the full seed process inside a single transaction."""
    db = SessionLocal()
    try:
        # ── Idempotency guard ─────────────────────────────────────────────────
        if db.query(User).filter(User.email == DEMO_EMAIL).first():
            logger.info("Database already seeded — nothing to do.")
            return

        logger.info("Starting FinSense seed process...")

        # ── 1. Default categories ─────────────────────────────────────────────
        logger.info("Creating %d default categories...", len(DEFAULT_CATEGORIES))
        category_map: dict[str, Category] = {}

        for name in DEFAULT_CATEGORIES:
            cat = Category(user_id=None, category_name=name, is_default=True)
            db.add(cat)

        db.flush()  # Flush to get IDs without committing

        # Build name → Category map after flush
        for name in DEFAULT_CATEGORIES:
            cat = (
                db.query(Category)
                .filter(Category.category_name == name, Category.user_id.is_(None))
                .first()
            )
            category_map[name] = cat
            logger.info("  [category] %-15s id=%s", name, cat.id)

        # ── 2. Default merchant mappings ──────────────────────────────────────
        logger.info(
            "Creating %d default merchant mappings...", len(MERCHANT_CATEGORY_MAP)
        )
        for merchant_key, cat_name in MERCHANT_CATEGORY_MAP.items():
            mapping = MerchantMapping(
                user_id=None,
                merchant_name=merchant_key,
                category_id=category_map[cat_name].id,
            )
            db.add(mapping)

        db.flush()
        logger.info("  Merchant mappings created.")

        # ── 3. Demo user ──────────────────────────────────────────────────────
        logger.info("Creating demo user: %s", DEMO_EMAIL)
        demo_user = User(
            name=DEMO_NAME,
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        db.add(demo_user)
        db.flush()
        logger.info("  Demo user id: %s", demo_user.id)

        # ── 4. Transactions ───────────────────────────────────────────────────
        num_transactions = random.randint(500, 700)
        logger.info("Generating %d transactions over the last 6 months...", num_transactions)

        merchant_keys = list(MERCHANT_CATEGORY_MAP.keys())
        today      = date.today()
        start_date = today - timedelta(days=180)

        batch: list[Transaction] = []
        for _ in range(num_transactions):
            merchant_key     = random.choice(merchant_keys)
            merchant_display = MERCHANT_DISPLAY[merchant_key]
            category         = category_map[MERCHANT_CATEGORY_MAP[merchant_key]]

            lo, hi  = MERCHANT_AMOUNT_RANGE[merchant_key]
            raw_amt = random.uniform(lo, hi)
            # Round to nearest integer for clean Indian amounts (most are whole numbers)
            amount  = Decimal(str(round(raw_amt, 2)))

            days_offset = random.randint(0, 180)
            txn_date    = start_date + timedelta(days=days_offset)

            payment_mode = _weighted_choice(PAYMENT_MODE_WEIGHTS)
            source       = _weighted_choice(SOURCE_WEIGHTS)

            batch.append(
                Transaction(
                    user_id=demo_user.id,
                    category_id=category.id,
                    merchant=merchant_display,
                    amount=amount,
                    transaction_date=txn_date,
                    payment_mode=payment_mode,
                    source=source,
                    notes=None,
                )
            )

        db.add_all(batch)
        db.commit()

        logger.info("=" * 55)
        logger.info("✅  Seed complete!")
        logger.info("    Transactions : %d", num_transactions)
        logger.info("    Categories   : %d", len(DEFAULT_CATEGORIES))
        logger.info("    Merchants    : %d", len(MERCHANT_CATEGORY_MAP))
        logger.info("    Demo login   : %s / %s", DEMO_EMAIL, DEMO_PASSWORD)
        logger.info("=" * 55)

    except Exception as exc:
        db.rollback()
        logger.error("Seed failed: %s", exc)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
