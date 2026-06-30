"""
FinSense FastAPI application entry point.

Start the development server::

    uvicorn app.main:app --reload

The API docs are available at:
  - Swagger UI : http://localhost:8000/docs
  - ReDoc      : http://localhost:8000/redoc
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth,
    transactions,
    upload,
    merchant_mappings,
    analytics,
    budgets,
    savings_goals,
    categories,
)

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)-8s]  %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="FinSense API",
    description=(
        "**FinSense** – Personal Finance Analytics Platform.\n\n"
        "Track expenses, auto-categorize transactions, visualize spending trends, "
        "and monitor budgets and savings goals.\n\n"
        "## Authentication\n"
        "All protected endpoints require a **Bearer JWT** token.\n"
        "1. `POST /auth/register` or `POST /auth/login` to get a token.\n"
        "2. Click **Authorize** above and enter `Bearer <your_token>`."
    ),
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={"name": "FinSense", "url": "https://github.com/yourname/finsense"},
    license_info={"name": "MIT"},
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow all origins during development.
# In production, restrict to your Vercel frontend URL.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router,              prefix="/auth",              tags=["Authentication"])
app.include_router(transactions.router,      prefix="/transactions",      tags=["Transactions"])
app.include_router(upload.router,            prefix="/upload",            tags=["Upload"])
app.include_router(merchant_mappings.router, prefix="/merchant-mappings", tags=["Merchant Mappings"])
app.include_router(analytics.router,         prefix="/analytics",         tags=["Analytics"])
app.include_router(budgets.router,           prefix="/budgets",           tags=["Budgets"])
app.include_router(savings_goals.router,     prefix="/savings-goals",     tags=["Savings Goals"])
app.include_router(categories.router,        prefix="/categories",        tags=["Categories"])


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"], summary="API health check")
async def health_check() -> dict:
    """Returns 200 OK when the API is running."""
    return {"status": "healthy", "service": "FinSense API", "version": "1.1.0"}
