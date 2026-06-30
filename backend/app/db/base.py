"""
SQLAlchemy declarative base.
All ORM models must inherit from this Base so that Alembic
can detect the full schema in one metadata object.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Central base class for all SQLAlchemy models.

    ``__allow_unmapped__ = True`` tells SQLAlchemy 2.0's Annotated Declarative
    scanner to ignore relationship attributes that use plain Python type hints
    (e.g. ``transactions: list = relationship(...)``) instead of the newer
    ``Mapped[List[...]]`` generic form.  This keeps the model code readable
    without requiring verbose Mapped[] annotations on every relationship.
    """

    __allow_unmapped__ = True

