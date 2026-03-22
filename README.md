# Insight Engine

> **Strategic Intelligence Platform** — Cross-domain innovation discovery via GraphRAG.
>
> Ingests 229,498 scientific papers across 12 domains, builds a unified knowledge graph,
> and uses GraphRAG to surface cross-domain breakthroughs that no keyword search can find.

---

## The Problem

Global R&D is siloed. A battery-longevity breakthrough in aerospace may directly solve an
unsolved problem in cardiology — but no one ever makes the connection.
Insight Engine is the matchmaker.

## Four Intelligence Modules

| Module | Nickname | What It Does |
|--------|----------|--------------|
| Cross-Pollination Discovery | The Matchmaker | Finds technologies from Domain A that solve problems in Domain B |
| Trend Velocity Tracking | The Early Warning System | Detects technologies being cited across multiple industries before mainstream |
| Patent Portfolio De-Risking | The Shield | Surfaces prior art via graph topology, not keyword similarity |
| Automated Gap Analysis | The Opportunity Finder | Uses unconnected graph nodes to flag research white-spaces |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Next.js 14 — localhost:3000                    │
│  Sigma.js graph viz | Dark enterprise UI        │
└────────────────┬────────────────────────────────┘
                 │ HTTP
┌────────────────▼────────────────────────────────┐
│  FastAPI — localhost:8000                       │
│  /auth /query /graph/explore /trending          │
│  JWT auth | Prometheus metrics | Celery workers │
└──┬──────┬──────┬──────┬──────┬──────────────────┘
   │      │      │      │      │
 Postgres Neo4j Qdrant Ollama MLflow
 :5432   :7687  :6333  :11434  :5000
 users   graph  vecs   Mistral track
```

**Query flow:** User query → NER → nomic-embed-text → Qdrant ANN (seed entities) →
Neo4j graph traversal (1–4 hops cross-domain) → Mistral 7B synthesis → cited answer.

### Key Numbers

| Metric | Value |
|--------|-------|
| Papers ingested | 229,498 (12 domains, arXiv) |
| Entities extracted | 10,779,699 (47/doc avg) |
| Graph entity nodes | 1,529,916 |
| Graph edges (RELATES_TO) | 1,583,613 |
| Cross-domain edges | 1,837,582 |
| Qdrant vectors | 1,529,916 (768-dim cosine) |
| Query latency (p95) | ~32s (embed 1s + Qdrant 0.2s + Neo4j 12s + Mistral 14s) |

---

## Quick Start

### Prerequisites

- Docker Desktop with WSL2 backend
- NVIDIA GPU (RTX 4060+ recommended, 8GB VRAM minimum)
- WSL2 Ubuntu 22.04/24.04
- Python 3.11 (`sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.11`)

### 1. Clone and configure

```bash
git clone <repo-url> insight-engine
cd insight-engine

# Create environment file
cp .env.example .env
# Edit .env — set NEO4J_PASSWORD, POSTGRES_PASSWORD, SECRET_KEY, etc.
```

### 2. Pull LLM models via Ollama

```bash
# Ollama runs in Docker (defined in docker-compose.yml)
docker compose up -d ollama
docker exec ie-ollama ollama pull mistral:v0.3
docker exec ie-ollama ollama pull nomic-embed-text
```

### 3. Start all services

```bash
# Create volume directories
mkdir -p volumes/{neo4j/{data,logs,plugins},qdrant,redis,mlflow,grafana,prometheus,airflow,postgres,pgadmin}

# Start everything
docker compose up -d

# Verify health
docker compose ps
```

### 4. Set up Python environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements/api.txt
pip install -r requirements/mlops.txt
```

### 5. Apply database migrations

```bash
source .venv/bin/activate
export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/insight_engine"
alembic upgrade head
```

### 6. Run the NLP pipeline (first time only)

```bash
source .venv/bin/activate
dvc repro   # runs: fetch_arxiv → ner → relations → graph_loader → quality_check
```

### 7. Open the app

Visit **http://localhost:3000** → Sign up → Start discovering.

---

## Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Sign up on first visit |
| API docs | http://localhost:8000/docs | — |
| Neo4j browser | http://localhost:7474 | neo4j / `$NEO4J_PASSWORD` |
| Qdrant UI | http://localhost:6333/dashboard | — |
| MLflow | http://localhost:5000 | — |
| Grafana | http://localhost:3001 | admin / `$GRAFANA_PASSWORD` |
| Prometheus | http://localhost:9090 | — |
| pgAdmin | http://localhost:5050 | `$PGADMIN_EMAIL` / `$PGADMIN_PASSWORD` |
| Airflow | http://localhost:8080 | admin / admin |

---

## Demo Query

After setup, try this query in the dashboard:

> *"What aerospace materials could improve cardiac implant durability?"*

Expected result: 20+ cross-domain paths connecting `titanium alloy`, `carbon fiber composite`,
`fatigue resistance` → `biocompatibility`, `implant longevity`. Mistral synthesizes a cited answer.

---

## Project Structure

```
insight-engine/
├── src/
│   ├── ingestion/          ← arXiv fetcher (229K papers, 12 domains)
│   ├── nlp/                ← spaCy NER + rule-based relation extraction
│   ├── graph/              ← Neo4j loader, Qdrant embeddings, GraphRAG engine
│   ├── pipeline/           ← Data quality gate
│   ├── backend/            ← FastAPI app, auth, DB models, CRUD
│   └── workers/            ← Celery async tasks
├── src/frontend/           ← Next.js 14 app (App Router, Sigma.js, shadcn/ui)
├── dags/                   ← Airflow DAG (6-stage pipeline)
├── tests/
│   ├── unit/               ← test_security.py, test_schemas.py, test_quality_check.py
│   └── integration/        ← test_api_health.py (requires running services)
├── config/
│   ├── prometheus.yml
│   └── grafana/dashboards/ ← api-dashboard.json, graphrag-dashboard.json
├── scripts/
│   └── register_pipeline.py ← MLflow Model Registry
├── data/                   ← DVC-tracked (raw → processed → graph)
├── metrics/                ← DVC pipeline metrics (JSON)
├── docker-compose.yml      ← All 13 services
├── dvc.yaml                ← 5-stage reproducible pipeline
├── params.yaml             ← DVC-tracked hyperparameters + quality thresholds
└── .env.example            ← Copy to .env, fill credentials
```

---

## MLOps

| Tool | Purpose | URL |
|------|---------|-----|
| DVC | Data + pipeline versioning | `dvc repro`, `dvc metrics show` |
| MLflow | Experiment tracking + Model Registry | http://localhost:5000 |
| Prometheus | Metrics scraping (request rate, latency, GraphRAG quality) | http://localhost:9090 |
| Grafana | Dashboards — API metrics + GraphRAG quality | http://localhost:3001 |
| Airflow | Pipeline DAG scheduling | http://localhost:8080 |

### Grafana Dashboards

- **Insight Engine — API**: Request rate, P95/P50 latency, requests per endpoint
- **Insight Engine — GraphRAG Quality**: Cross-domain paths, seed entities, confidence score, citations

### Register best model to MLflow registry

```bash
source .venv/bin/activate
python scripts/register_pipeline.py
```

---

## Running Tests

```bash
source .venv/bin/activate

# Unit tests (no services required)
pytest tests/unit/ -v

# Integration tests (requires docker compose up -d api)
pytest tests/integration/ -v -m integration
```

---

## CI/CD (GitHub Actions)

### Flow

```
feature-branch ──PR──► develop   (ci.yml runs — all checks must pass before merge)
                  │
develop        ──PR──► main      (ci.yml runs again — all checks must pass before merge)
                  │
main (merged)  ────────────────► release.yml: tests → build → push to ghcr.io
```

### Workflows

| File | Trigger | Jobs |
|------|---------|------|
| `ci.yml` | PR to `develop` or `main`, push to `develop` | Unit tests, black/isort, bandit, tsc/eslint, DVC validation |
| `release.yml` | Push to `main` only | Same tests → **then** build + push `api:latest` + `frontend:latest` to ghcr.io |

Docker images are **only published after all tests pass** (`needs: [test, lint, security, frontend]`).
Every release overwrites `:latest` and also tags `:sha-<commit>` for rollback.

### Branch protection (configure in GitHub repo settings)

**`develop` branch:**
- Require PR before merging
- Required status checks: `Python Unit Tests`, `Python Lint`, `Security Scan`, `Frontend TypeScript + ESLint`, `DVC + Params Validation`

**`main` branch:**
- Require PR before merging (from `develop` only)
- Same required status checks as `develop`

### Registry

Images are published to **GitHub Container Registry** (free, no extra setup):
```
ghcr.io/<your-username>/insight-engine-api:latest
ghcr.io/<your-username>/insight-engine-frontend:latest
```

Pull locally after a release:
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin
docker pull ghcr.io/<username>/insight-engine-api:latest
docker pull ghcr.io/<username>/insight-engine-frontend:latest
```

### Secrets required

None. Unit tests use test values from `tests/conftest.py`. Docker push uses the auto-provided `GITHUB_TOKEN`.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| LLM | Mistral 7B v0.3 via Ollama (4.1GB, RTX 4060) |
| Embeddings | nomic-embed-text v1.5 (768-dim, via Ollama) |
| Graph DB | Neo4j 5 Community |
| Vector DB | Qdrant 1.9 |
| NLP | spaCy 3.7 + SciSpacy en_core_sci_lg |
| API | FastAPI 0.111 + Pydantic v2 + SQLAlchemy 2.0 async |
| Auth | JWT (HS256) + bcrypt + single-use refresh tokens |
| Frontend | Next.js 14 App Router + Sigma.js + shadcn/ui + Tailwind |
| MLOps | DVC 3 + MLflow 2 + Prometheus + Grafana + Airflow 2.9 |
| Database | PostgreSQL 16 (users/auth) |

Full version pinning: [`.claude/docs/stack.md`](.claude/docs/stack.md)

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```
NEO4J_PASSWORD=         # Neo4j auth
POSTGRES_USER=          # PostgreSQL user
POSTGRES_PASSWORD=      # PostgreSQL password
SECRET_KEY=             # JWT signing key (32+ random chars)
GRAFANA_PASSWORD=       # Grafana admin password
PGADMIN_EMAIL=          # pgAdmin login email
PGADMIN_PASSWORD=       # pgAdmin login password
```

**Never commit `.env`** — it is gitignored. Only `.env.example` goes into git.
