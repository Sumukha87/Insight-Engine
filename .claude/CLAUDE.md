# Insight-Engine — Project Context

> Strategic Intelligence Platform. Cross-domain innovation discovery via GraphRAG.
> Solo dev. Windows 11 + Ubuntu WSL2 + VS Code + Docker Desktop. RTX 4060 8GB VRAM.

## What This Is

1. Project Overview
Insight-Engine is a B2B SaaS platform that ingests scientific papers and patent filings, builds a
unified knowledge graph across all domains, and uses GraphRAG to surface cross-domain innovation
opportunities that no keyword search or standard vector RAG can find.
The core thesis: Global R&D is siloed. A battery-longevity breakthrough in aerospace may
directly solve an unsolved problem in cardiology — but no one ever makes the connection.
Insight-Engine is the matchmaker.
Four Intelligence Modules
ModuleNicknameWhat It DoesCross-Pollination DiscoveryThe MatchmakerFinds technologies from Domain A that solve problems in Domain BTrend Velocity TrackingThe Early Warning SystemDetects technologies being cited across multiple industries before mainstreamPatent Portfolio De-RiskingThe ShieldSurfaces prior art via graph topology, not keyword similarityAutomated Gap AnalysisThe Opportunity FinderUses unconnected graph nodes to flag research white-spaces

## Architecture (5 layers)

```
L5  FastAPI + Next.js 14          ← query API + React UI
L4  Neo4j Community (Docker)      ← knowledge graph + Cypher
L3  Qdrant (Docker)               ← vector embeddings
L2  NLP Pipeline                  ← spaCy/SciSpacy NER + relation extraction
L1  Ingestion                     ← PubMed, arXiv, USPTO bulk data → Grobid parse
```

All services run locally via Docker Compose. LLM runs via Ollama (Mistral 7B or Llama 3.1 8B).
MLOps: DVC for data versioning, MLflow for experiment tracking, Prometheus + Grafana for monitoring.

See @docs/architecture.md for full system design.
See @docs/stack.md for every tool, version, and why it was chosen.

## SECURITY — TOP PRIORITY

Security is the single most important rule in this project. Every other rule is secondary.

### Absolute Prohibitions
- **NEVER hardcode secrets, passwords, API keys, or tokens in source code.** Not in Python, not in TypeScript, not in config files, not in tests, not even as examples with real-looking values. Use env vars via `os.environ` or `process.env.NEXT_PUBLIC_*`.
- **NEVER commit `.env` files.** `.env` is gitignored. Only `.env.example` with placeholder values goes into git.
- **NEVER use SQL string interpolation.** Always use parameterized queries — SQLAlchemy ORM or `$param` in Cypher. No f-strings, no `.format()`, no `%s` for building queries.
- **NEVER store raw tokens in the database.** Store SHA-256 hashes only (access_token_hash, token_hash, key_hash).
- **NEVER expose stack traces or internal errors to API clients.** Use HTTPException with safe messages. Let unhandled exceptions hit the 500 handler.
- **NEVER disable CORS, CSRF, or auth checks** — not even temporarily, not even "for testing".

### Required Practices
- **All credentials from env vars**: `SECRET_KEY`, `NEO4J_PASSWORD`, `POSTGRES_PASSWORD`, `DATABASE_URL` — all read from `os.environ` at runtime.
- **Password hashing**: bcrypt via passlib. Never store plaintext passwords.
- **JWT validation**: always verify signature + expiry + check session is_revoked in DB.
- **Input validation**: Pydantic v2 models for all FastAPI request bodies. Zod schemas for all frontend forms.
- **Dependency security**: no `eval()`, no `exec()`, no `pickle.loads()` on user input, no `dangerouslySetInnerHTML` without sanitization.
- **SQL injection prevention**: SQLAlchemy ORM for all queries. If raw SQL is needed, always use `text()` with bound parameters.
- **XSS prevention**: React auto-escapes by default. Never use `dangerouslySetInnerHTML`. Sanitize any user-generated HTML.

## Key Rules — Always Follow

- **WSL2 paths**: use `/home/$USER/` not `/mnt/c/`. Docker volumes must use WSL2 paths.
- **Python**: 3.11 via pyenv. Always activate venv before installing: `source .venv/bin/activate`.
- **Docker**: all services defined in `docker-compose.yml`. Never run services outside of compose during dev.
- **GPU**: Ollama uses the RTX 4060 (8GB VRAM). Max model size = 8B params at Q4. Do not load multiple models simultaneously.
- **No cloud spend**: everything runs locally. No OpenAI API calls. No AWS. Ollama for LLM, nomic-embed-text for embeddings.
- **Data is versioned**: never modify raw data files directly. All ingestion output goes through DVC pipelines.
- **Experiments are tracked**: every NLP model run logs to MLflow. Never run training without `mlflow.start_run()`.
- **Git is user-only**: never run `git add`, `git commit`, `git push`, or any destructive git command. Only the user touches git.

## Commands — Exact Strings

```bash
# Start everything
docker compose up -d

# Python env
source .venv/bin/activate
pip install -r requirements.txt

# Run ingestion pipeline
dvc repro ingestion

# MLflow UI
mlflow ui --host 0.0.0.0 --port 5000

# Ollama
ollama serve          # starts server (should already be running as service)
ollama run mistral    # interactive test
ollama ps             # check what's loaded

# Neo4j browser
open http://localhost:7474   # or visit in browser

# Grafana
open http://localhost:3001

# PostgreSQL
open http://localhost:5050   # pgAdmin GUI

# Alembic migrations
source .venv/bin/activate
export DATABASE_URL="postgresql+asyncpg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/insight_engine"
alembic revision --autogenerate -m "description"
alembic upgrade head

# Tests
pytest tests/ -v
pytest tests/unit/ -v --no-header
```

## Phase Status

> **Active:** Phase 3 — IN PROGRESS — Status: `Phase 2 COMPLETE. Phase 3 ACTIVE.`
> Full checklist: @docs/progress.md | Architecture: @docs/architecture.md | Stack: @docs/stack.md

### Completed (this phase)
- [x] WSL2 Python 3.11 via deadsnakes PPA (pyenv not used — build issues on WSL2, deadsnakes more reliable)
- [x] Docker Desktop WSL2 integration enabled
- [x] `nvidia-smi` shows RTX 4060 in WSL2 — GPU confirmed visible
- [x] Ollama running via Docker (not native WSL2) — container name `ollama`, named volume `ollama`, port 11434
- [x] `ollama pull mistral:v0.3` complete (switched from v0.1 — better instruction following, same size)
- [x] `ollama pull nomic-embed-text` complete
- [x] GitHub repo created and connected
- [x] DVC initialized (`dvc init`)
- [x] `.env` file created from `.env.example`
- [x] `docker compose up -d` — infrastructure services healthy (neo4j, qdrant, grobid, redis, mlflow, prometheus, grafana)
- [x] arXiv fetcher — ALL 12 domains (src/ingestion/arxiv_fetcher.py)
- [x] First batch downloaded: 229,498 papers across 12 domains
- [x] dvc.yaml pipeline defined (fetch_arxiv → ner → relations → graph_loader)
- [x] Raw data pushed to Google Drive via DVC (OAuth, personal credentials)
- [x] dvc repro run 2026-03-21 — all 4 stages cached, pipeline locked
- [x] spaCy 3.7.5 + SciSpacy installed and tested
- [x] `en_core_sci_lg` model downloaded
- [x] NER pipeline script: JSONL in → entities JSONL out (src/nlp/ner_pipeline.py)
- [x] Entity types expanded to 12: Technology, Material, Disease, Device, Compound, Process, Organism, Gene, Algorithm, Phenomenon, Software, Infrastructure
- [x] Full 229,498 docs processed through NER — 10,779,699 entities extracted (47/doc avg)
- [x] MLflow experiment `insight-engine-nlp` created and logging to Docker server (:5000)
- [x] Relation extraction v1 rule-based (src/nlp/relation_extractor.py) — 2,294,895 relations extracted
- [x] params.yaml created — all pipeline params version-controlled via DVC
- [x] params.yaml — NER, relations, graph params all tracked
- [x] dvc.yaml — full 4-stage pipeline: fetch_arxiv → ner → relations → graph_loader
- [x] DVC plots wired: ner_domain_stats.csv, relation_domain_stats.csv
- [x] MLflow tracking URI configured — scripts log to Docker server, export MLFLOW_TRACKING_URI in ~/.bashrc
- [x] `dvc dag` shows full pipeline DAG
- [x] `dvc metrics show` shows NER + relation metrics
- [x] Neo4j Community running in Docker at :7474 / :7687
- [x] Graph schema applied: composite uniqueness constraints + domain/type indexes
- [x] src/graph/graph_loader.py written — streams entities + relations → Neo4j
- [x] graph_loader added as Stage 4 in dvc.yaml
- [x] Graph loaded: 1,529,916 entity nodes | 166,573 paper nodes | 1,583,613 RELATES_TO edges
- [x] First cross-domain Cypher query verified — 1,837,582 cross-domain RELATES_TO edges confirmed
- [x] Qdrant running in Docker at :6333
- [x] Embedding pipeline complete — 1,529,916 / 1,529,916 entities embedded (nomic-embed-text, 768-dim)
- [x] embedding_id property set on all Entity nodes (links Neo4j ↔ Qdrant)
- [x] Neo4j index on Entity.embedding_id created (fast seed lookup)
- [x] Qdrant has_edges payload flag set on 517,473 entities (filters to traversable seeds instantly)
- [x] GraphRAG query engine built: src/graph/graphrag_query.py (Stage 6)
- [x] First GraphRAG query returns cross-domain answer with Mistral synthesis
- [x] End-to-end: raw paper → entities → relations → Neo4j graph working
- [x] Full DVC pipeline tracked and reproducible
- [x] MLflow logging all 3 pipeline stages
- [x] First cross-domain Cypher query verified
- [x] GraphRAG query returns answer — demo query "aerospace materials for cardiac implants" works
- [x] 20 cross-domain paths found, Mistral synthesizes coherent answer
- [x] Query latency: ~32s (embedding 1s + Qdrant 0.2s + Neo4j traversal 12s + Mistral 14s)
- [x] Neo4j Community running in Docker at :7474 / :7687
- [x] Graph schema Cypher constraints + indexes applied
- [x] graph_loader.py: entities + relations JSONL → Neo4j MERGE (src/graph/graph_loader.py)
- [x] 1,529,916 entity nodes loaded
- [x] 1,583,613 RELATES_TO edges loaded (1,837,582 are cross-domain)
- [x] First cross-domain Cypher query tested: "aerospace materials for cardiac implants" — WORKS
- [x] Qdrant running in Docker at :6333
- [x] Embedding pipeline: entity text → nomic-embed-text → Qdrant upsert (src/graph/embedding_pipeline.py)
- [x] `embedding_id` property set on all 1,529,916 Entity nodes
- [x] Neo4j index on Entity.embedding_id created for fast lookup
- [x] Qdrant has_edges payload flag: 517,473 entities flagged for instant seed filtering
- [x] GraphRAG query engine: src/graph/graphrag_query.py — Stage 6 complete
- [x] Apache Airflow installed in .venv — DAG at dags/insight_engine_pipeline.py
- [x] Airflow UI at localhost:8080 — start with: bash scripts/start_airflow.sh
- [x] Demo query works: "aerospace materials for cardiac implants"
- [x] Answer includes ≥3 cross-domain connections
- [x] PostgreSQL 16 running in Docker at :5432 — user/auth/session DB
- [x] pgAdmin 4 running in Docker at :5050 — DB GUI
- [x] SQLAlchemy 2.0 async ORM + asyncpg driver configured
- [x] Alembic migrations initialized — 2 migrations applied (initial_schema, auth_sessions)
- [x] DB schema: users, organizations, memberships, api_keys, query_logs, usage_quotas, auth_sessions, refresh_tokens
- [x] .env.example + .env updated with POSTGRES_USER, POSTGRES_PASSWORD, SECRET_KEY, PGADMIN creds
- [x] docker-compose.yml updated — postgres + pgadmin services, DATABASE_URL wired to api + celery
- [x] JWT access token (HS256, 60 min) + opaque refresh token (30 days, single-use rotation)
- [x] Session tracking — auth_sessions table, per-device session listing + revocation
- [x] Replay detection — reusing consumed refresh token revokes entire session
- [x] src/backend/auth/security.py — hash_password, verify_password, create_access_token, decode_token, hash_token
- [x] src/backend/auth/token_service.py — issue_tokens, refresh_tokens, revoke_session_by_token_hash
- [x] src/backend/auth/deps.py — get_current_user checks session is_revoked + expiry in DB
- [x] src/backend/db/crud/ — users.py, sessions.py, tokens.py
- [x] src/backend/main.py — FastAPI app entrypoint
- [x] POST /auth/register, POST /auth/login, POST /auth/refresh, POST /auth/logout
- [x] GET /auth/me, GET /auth/sessions, DELETE /auth/sessions/{id}
- [x] GET /health — checks postgres, neo4j, qdrant, ollama
- [x] Prometheus metrics wired (/metrics endpoint)
- [x] src/backend/api/schemas.py — Pydantic v2 models for all request/response shapes
- [x] FastAPI /docs working with Pydantic schemas
- [x] POST /query endpoint — wired to GraphRAG engine, logs to query_logs table
- [x] GET /graph/explore — Neo4j neighborhood subgraph, returns nodes + edges for Sigma.js
- [x] GET /trending — top 30 entities by cross-domain RELATES_TO count
- [x] POST /queries/save, GET /queries/saved, DELETE /queries/saved/{id} — saved research CRUD
- [x] GET /queries/history — last 50 query log entries for current user
- [x] POST /watchlist, GET /watchlist, DELETE /watchlist/{entity_name} — entity watchlist CRUD
- [x] Next.js 14 App Router at src/frontend/
- [x] src/frontend/src/lib/api.ts — typed fetch client for all auth + query endpoints
- [x] src/frontend/src/app/signup/page.tsx — full signup form (react-hook-form + zod)
- [x] src/frontend/src/app/login/page.tsx — login form with dark theme
- [x] src/frontend/src/app/page.tsx — redirects to /login (no default Next.js page)
- [x] src/frontend/src/middleware.ts — protects all routes except /login and /signup
- [x] src/frontend/src/app/dashboard/page.tsx — query UI with answer, paths, seed entities, citations
- [x] Frontend ↔ backend integration verified: signup → login → dashboard query all working
- [x] Source citations panel — CitationCard component, source papers section below answer
- [x] Graph explorer: GET /graph/explore + Sigma.js GraphExplorer component — seed entities are clickable, renders neighborhood subgraph (nodes + edges) with domain colour legend
- [x] Saved queries: POST /queries/save, GET /queries/saved, DELETE /queries/saved/{id} — save with name + notes, replay from Saved tab
- [x] Query history: GET /queries/history — last 50 queries with re-run button
- [x] Entity watchlist: POST /watchlist, GET /watchlist, DELETE /watchlist/{name} — add from results, manage in Watchlist tab, explore from there
- [x] Trending feed: GET /trending — top 30 entities by cross-domain RELATES_TO connections, with bar chart, watchlist add, and graph explore
- [x] Dashboard tab navigation: Discover / Saved / History / Watchlist / Trending
- [x] Export to Markdown: client-side download of query result as .md file
- [x] DB migration a3c7e9f12b45: saved_queries + entity_watchlist tables
- [x] Prometheus metrics — 4 GraphRAG quality histograms: graphrag_paths_found, graphrag_seeds_found, graphrag_citations_returned, graphrag_confidence_score
- [x] MLflow per-query logging — every /query request logs to "graphrag-queries" experiment (best-effort, non-blocking)
- [x] Grafana dashboard: config/grafana/dashboards/api-dashboard.json — Request Rate, P95/P50 Latency, Total Requests, Avg Latency, Requests/Endpoint bar chart
- [x] Grafana dashboard: config/grafana/dashboards/graphrag-dashboard.json — GraphRAG latency, cross-domain paths, seeds, confidence score, citations
- [x] Airflow in Docker — apache/airflow:2.9.0 standalone service added to docker-compose.yml (port 8080). Resolves SQLAlchemy conflict with api service.
- [x] DAG hardcoded NEO4J_PASSWORD removed — replaced with os.environ["NEO4J_PASSWORD"] (enforced by security hook)
- [x] Stage 6 (graphrag_query_engine) updated in DAG — runs smoke test instead of echo stub
- [x] MLflow Model Registry — scripts/register_pipeline.py: finds best run by confidence, creates registered model "insight-engine-graphrag", transitions to Staging
- [x] Data quality gate — src/pipeline/quality_check.py: 5 checks (entity count, relation count, graph size, embedding coverage, cross-domain ratio). Exits non-zero on failure.
- [x] quality_gate thresholds added to params.yaml (DVC-tracked)
- [x] quality_check stage added to dvc.yaml (deps: ner/relation/graph metrics)
- [x] pytest.ini configured (asyncio_mode=auto, unit + integration markers)
- [x] tests/conftest.py — sets SECRET_KEY + DATABASE_URL env vars for test isolation
- [x] tests/unit/test_security.py — 13 tests: password hashing, JWT encode/decode, hash_token
- [x] tests/unit/test_schemas.py — 12 tests: Pydantic validation for all request schemas
- [x] tests/unit/test_quality_check.py — 10 tests: each quality gate check in isolation with temp files
- [x] tests/integration/test_api_health.py — /health, /metrics, auth rejection tests (requires running api)
- [x] .github/workflows/ci.yml — runs on every PR to develop/main and on push to develop
- [x] .github/workflows/release.yml — runs on push to main only
- [x] GitHub Container Registry (ghcr.io) — free Docker image registry
- [x] README.md — full rewrite: project thesis, 4 modules, architecture diagram, quickstart, service URLs, demo query, project structure, CI/CD flow, MLOps section, tech stack table
- [x] test_tampered_token_raises fixed — full signature segment replacement (not single-char flip; base64url padding tolerates single-char changes)
- [x] api.ts ESLint no-explicit-any fixed — `(data as { detail?: unknown })` and `(d: { msg?: string })`
- [x] src/backend/main.py bandit MD5 fix — `hashlib.md5(..., usedforsecurity=False)  # nosec B324`
- [x] QueryRequest empty string validation — `query: str = Field(..., min_length=1)`
- [x] WSL2 locale warning fixed — `sudo locale-gen en_US.UTF-8`

### Open Blockers
- _(none)_

### Recent Decisions
- 2026-03-22: JWT tamper test uses full signature replacement (Flipping one character in a JWT signature is flaky — base64url padding can tolerate it. Replacing the entire third segment with garbage is deterministically invalid.)
- 2026-03-22: isort must run before black with --profile black flag (Without --profile black, isort reformats files after black, causing black to fail. Always: `isort --profile black` first, then `black`.)
- 2026-03-22: bcrypt must be pinned to 3.2.2 in CI (passlib 1.7.x is incompatible with bcrypt>=4.0. pip sometimes installs latest (5.x). Explicit `pip install "bcrypt==3.2.2"` step added after requirements install in both workflows.)

### Key Numbers
- Papers ingested: 229,498 (12 domains, arXiv)
- Entities extracted: 10,779,699 (47/doc avg)
- GraphRAG query latency (p95): ~32s (embed 1s + Qdrant 0.2s + Neo4j traversal 12s + Mistral 14s)

## Coding Conventions

- Python: black formatter, isort imports, type hints on all functions, docstrings on classes.
- Next.js 14 App Router, SSR mode (Node.js server, not static export). See api-rules.md for conventions.
- FastAPI: async handlers only. Pydantic v2 models for all request/response shapes.
- React: functional components only, TypeScript strict mode, Zustand for global state.
- Cypher: always use parameters, never string interpolation. Use `MERGE` not `CREATE` for entities.
- SQL: always use SQLAlchemy ORM or `text()` with bound params. NEVER use f-strings for SQL.
- Secrets: all credentials via env vars. Never hardcode passwords, keys, or tokens.
- Tests: pytest for Python, Vitest for TypeScript. Test files mirror src structure in `tests/`.
- Commits: conventional commits format (`feat:`, `fix:`, `chore:`, `docs:`).

## Docs
- See @docs/architecture.md for the overall architecture
- See @docs/stack.md for all the stack we are using
- See @docs/frontend-design.md for the canonical frontend UI theme — ALL new pages and components must follow this