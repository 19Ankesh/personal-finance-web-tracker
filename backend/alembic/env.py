"""
Alembic environment configuration.

This file is executed by Alembic whenever you run migration commands.
It:
  - Loads DATABASE_URL from the .env file
  - Imports all ORM models so Alembic can detect schema changes
  - Supports both offline (SQL script generation) and online (live DB) modes
"""
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# ── Path setup ────────────────────────────────────────────────────────────────
# Add the backend/ directory to sys.path so `app.*` imports resolve correctly
# when running `alembic` from the backend/ directory.
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# ── Load environment ──────────────────────────────────────────────────────────
load_dotenv(BACKEND_DIR / ".env")

# ── Import models ─────────────────────────────────────────────────────────────
# ALL models must be imported here so Alembic can detect additions/removals.
from app.db.base import Base  # noqa: E402
from app.models.models import (  # noqa: E402, F401
    Budget,
    Category,
    MerchantMapping,
    SavingsGoal,
    Transaction,
    User,
)

# ── Alembic config object ─────────────────────────────────────────────────────
config = context.config

# Inject DATABASE_URL from env (overrides the placeholder in alembic.ini)
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Create a .env file in the backend/ directory."
    )
config.set_main_option("sqlalchemy.url", database_url)

# Set up loggers defined in alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ── Migration runners ─────────────────────────────────────────────────────────


def run_migrations_offline() -> None:
    """
    Offline mode: generate SQL migration scripts without connecting to the DB.

    Useful for reviewing migrations or running them manually.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Online mode: connect to the database and apply migrations directly.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
