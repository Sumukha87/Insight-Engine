---
name: db-status
description: Check PostgreSQL database status — tables, row counts, migration state, and connection health
---

# Database Status Check

Check PostgreSQL health, schema, and data. Run these in parallel where possible:

## 1. Connection Health
```bash
docker exec ie-postgres pg_isready -U ${POSTGRES_USER:-insight_engine} -d insight_engine
```

## 2. Alembic Migration State
```bash
source .venv/bin/activate && export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:-insight_engine}:${POSTGRES_PASSWORD:-changeme_postgres}@localhost:5432/insight_engine" && alembic current
```
Also show pending migrations:
```bash
alembic heads
```

## 3. Table Row Counts
Run via psql inside the Docker container:
```bash
docker exec ie-postgres psql -U ${POSTGRES_USER:-insight_engine} -d insight_engine -c "
SELECT schemaname, relname AS table_name, n_live_tup AS row_count
FROM pg_stat_user_tables
ORDER BY relname;
"
```

## 4. Table Schema Check
```bash
docker exec ie-postgres psql -U ${POSTGRES_USER:-insight_engine} -d insight_engine -c "\dt+"
```

## Summary
Present as:

| Table | Rows | Size | Notes |
|-------|------|------|-------|

Also note: pgAdmin GUI at http://localhost:5050
