"""
FinSense SQLAlchemy ORM models.

All 6 tables are defined here to support the full 6-phase roadmap:
  users, categories, transactions, merchant_mappings, budgets, savings_goals

Design decisions:
  - UUID primary keys throughout (Supabase / distributed-safe)
  - user_id = NULL on categories/merchant_mappings → global defaults
  - Decimal (Numeric) for all financial columns — never float
  - Enum types stored as native PostgreSQL enums
  - Indexes on all common filter/join columns
"""
import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


# ── Enumerations ──────────────────────────────────────────────────────────────


class PaymentMode(str, enum.Enum):
    """Payment channel used for a transaction."""

    UPI = "upi"
    DEBIT_CARD = "debit_card"
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    NET_BANKING = "net_banking"
    OTHER = "other"


class TransactionSource(str, enum.Enum):
    """How the transaction was captured into FinSense."""

    MANUAL = "manual"
    VOICE = "voice"
    CSV = "csv"
    PDF = "pdf"


# ── Models ────────────────────────────────────────────────────────────────────


class User(Base):
    """Registered FinSense user."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    transactions: list = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    categories: list = relationship(
        "Category", back_populates="user", cascade="all, delete-orphan"
    )
    merchant_mappings: list = relationship(
        "MerchantMapping", back_populates="user", cascade="all, delete-orphan"
    )
    budgets: list = relationship(
        "Budget", back_populates="user", cascade="all, delete-orphan"
    )
    savings_goals: list = relationship(
        "SavingsGoal", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class Category(Base):
    """
    Spending category (e.g. Food, Transport).

    Global defaults have user_id = NULL and is_default = True.
    User-created categories have user_id set to the owning user's UUID.
    """

    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    category_name = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    user = relationship("User", back_populates="categories")
    transactions: list = relationship("Transaction", back_populates="category")
    merchant_mappings: list = relationship(
        "MerchantMapping", back_populates="category"
    )
    budgets: list = relationship("Budget", back_populates="category")

    __table_args__ = (Index("ix_categories_user_id", "user_id"),)

    def __repr__(self) -> str:
        return (
            f"<Category id={self.id} name={self.category_name!r} "
            f"default={self.is_default}>"
        )


class Transaction(Base):
    """
    A single financial transaction.

    ``category_id`` is nullable — transactions ingested via CSV/PDF may be
    uncategorized until the categorization engine processes them (Phase 2).
    ``source`` tracks how the transaction entered the system.
    """

    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    merchant = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    transaction_date = Column(Date, nullable=False)
    payment_mode = Column(
        SAEnum(PaymentMode, name="paymentmode", create_type=True),
        nullable=False,
        default=PaymentMode.UPI,
    )
    source = Column(
        SAEnum(TransactionSource, name="transactionsource", create_type=True),
        nullable=False,
        default=TransactionSource.MANUAL,
    )
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")

    __table_args__ = (
        Index("ix_transactions_user_id", "user_id"),
        Index("ix_transactions_transaction_date", "transaction_date"),
        Index("ix_transactions_merchant", "merchant"),
        Index("ix_transactions_category_id", "category_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} merchant={self.merchant!r} "
            f"amount={self.amount} date={self.transaction_date}>"
        )


class MerchantMapping(Base):
    """
    Maps a normalised merchant name to a category.

    Global mappings (shipped with the app) have user_id = NULL.
    User-learned mappings have user_id set (Phase 2 self-learning engine).
    merchant_name is always stored lowercase for case-insensitive lookups.
    """

    __tablename__ = "merchant_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    merchant_name = Column(String(255), nullable=False)  # stored lowercase
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    user = relationship("User", back_populates="merchant_mappings")
    category = relationship("Category", back_populates="merchant_mappings")

    __table_args__ = (
        Index("ix_merchant_mappings_user_id", "user_id"),
        Index("ix_merchant_mappings_merchant_name", "merchant_name"),
    )

    def __repr__(self) -> str:
        return (
            f"<MerchantMapping merchant={self.merchant_name!r} "
            f"category_id={self.category_id} user_id={self.user_id}>"
        )


class Budget(Base):
    """
    Monthly budget limit for a specific category.

    Supports Phase 4 budget tracking: 80 % warning, 100 % exceeded alert.
    A user can have one budget per (category, month, year) combination.
    """

    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    budget_limit = Column(Numeric(12, 2), nullable=False)
    month = Column(Integer, nullable=False)  # 1–12
    year = Column(Integer, nullable=False)   # e.g. 2025

    # ── Relationships ─────────────────────────────────────────────────────────
    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")

    __table_args__ = (
        Index("ix_budgets_user_id_month_year", "user_id", "month", "year"),
    )

    def __repr__(self) -> str:
        return (
            f"<Budget user_id={self.user_id} category_id={self.category_id} "
            f"{self.month:02d}/{self.year} limit={self.budget_limit}>"
        )


class SavingsGoal(Base):
    """
    A savings target the user wants to reach by a specific date.

    ``current_amount`` is updated by the Phase 5 savings-tracking service.
    ``target_date`` is optional — some goals are open-ended.
    """

    __tablename__ = "savings_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    goal_name = Column(String(255), nullable=False)
    target_amount = Column(Numeric(12, 2), nullable=False)
    current_amount = Column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    target_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    user = relationship("User", back_populates="savings_goals")

    __table_args__ = (Index("ix_savings_goals_user_id", "user_id"),)

    def __repr__(self) -> str:
        return (
            f"<SavingsGoal id={self.id} name={self.goal_name!r} "
            f"target={self.target_amount} current={self.current_amount}>"
        )
