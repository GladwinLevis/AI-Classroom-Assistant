# Installation Guide

This guide details setting up the AI Classroom Assistant platform for local development and Docker containers.

---

## Prerequisites

- **Python**: 3.12+
- **Node.js**: 20+
- **PostgreSQL**: 16+
- **Redis**: 7+
- **Docker**: 24+ & Docker Compose v2+

---

## 1. Local Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

---

## 2. Local Frontend Setup

```bash
# From repository root
npm install

# Start Vite dev server
npm run dev
```

---

## 3. Celery Worker Execution

```bash
cd backend
celery -A app.core.celery.celery_app worker --loglevel=info
```
