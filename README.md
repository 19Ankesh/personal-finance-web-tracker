# FinSense – Personal Finance Analytics Platform

A full-stack personal finance analytics platform for Indian users.

## Tech Stack

- **Backend**: FastAPI, PostgreSQL (Supabase), SQLAlchemy, Alembic, Pydantic, Pandas, pdfplumber
- **Frontend**: React, Vite, Tailwind CSS v3, Recharts, Axios, React Router
- **Auth**: JWT (python-jose + bcrypt)
- **Deploy**: Vercel (frontend) · Render (backend) · Supabase (database)

## Features

- PDF/CSV bank statement import 
- Auto-categorization engine with self-learning merchant mappings
- Voice expense logging (Web Speech API)
- Interactive dashboard with 4 chart types
- Monthly budget tracking with live spend metrics
- Savings goal tracker with progress rings
- Financial health score
- Smart spending insights
- JWT authentication with user-isolated data

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # fill in DATABASE_URL and SECRET_KEY
alembic upgrade head
python -m app.utils.seed     # seed demo data
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
# create .env.local with: VITE_API_URL=http://localhost:8000
npm run dev
```



## Project Structure

```
FinSense-v2/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── core/         # Parsers, categorizer, security
│   │   ├── db/           # SQLAlchemy engine + session
│   │   ├── models/       # ORM models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic layer
│   │   └── utils/        # Seed data generator
│   └── alembic/          # DB migrations
└── frontend/
    └── src/
        ├── api/           # Axios API clients
        ├── components/    # Reusable UI components + charts
        ├── context/       # Auth context
        ├── hooks/         # Custom React hooks
        ├── pages/         # Route-level page components
        └── utils/         # Formatters, constants
```
