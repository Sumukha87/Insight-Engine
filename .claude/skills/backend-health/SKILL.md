---
name: backend-health
description: Check FastAPI backend — import validation, DB connection, auth flow, endpoint listing
---

# Backend Health Check

Verify the FastAPI backend is healthy and all components wire together correctly.

## 1. Import Validation
Test that main.py and all its dependencies import without errors:
```bash
source .venv/bin/activate && export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:-insight_engine}:${POSTGRES_PASSWORD:-changeme_postgres}@localhost:5432/insight_engine" && export SECRET_KEY="${SECRET_KEY:-test}" && python3 -c "from src.backend.main import app; print(f'FastAPI app loaded: {len(app.routes)} routes')"
```

## 2. List All Routes
```bash
source .venv/bin/activate && export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:-insight_engine}:${POSTGRES_PASSWORD:-changeme_postgres}@localhost:5432/insight_engine" && export SECRET_KEY="${SECRET_KEY:-test}" && python3 -c "
from src.backend.main import app
for route in app.routes:
    if hasattr(route, 'methods'):
        for m in route.methods:
            print(f'{m:7s} {route.path}')
"
```

## 3. DB Connection
Check that the async engine can reach Postgres:
```bash
source .venv/bin/activate && export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:-insight_engine}:${POSTGRES_PASSWORD:-changeme_postgres}@localhost:5432/insight_engine" && export SECRET_KEY="${SECRET_KEY:-test}" && python3 -c "
import asyncio
from src.backend.db.session import engine
async def check():
    async with engine.connect() as conn:
        r = await conn.execute(__import__('sqlalchemy').text('SELECT 1'))
        print(f'DB connection: OK (result={r.scalar()})')
asyncio.run(check())
"
```

## 4. Model Consistency
Verify SQLAlchemy models match the DB schema:
```bash
source .venv/bin/activate && export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:-insight_engine}:${POSTGRES_PASSWORD:-changeme_postgres}@localhost:5432/insight_engine" && alembic check 2>&1 || echo "Run 'alembic revision --autogenerate' if models have changed"
```

## Summary
| Component | Status | Details |
|-----------|--------|---------|
