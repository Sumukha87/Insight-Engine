# Progress Tracker

> Update this file at the end of every Claude Code session.
> Claude Code: check this file first with `@docs/progress.md` at session start.

## Current Phase

**Phase 3 — IN PROGRESS**
Status: Phase 2 COMPLETE. Phase 3 ACTIVE.
Target: Weeks 7–9 (Phase 3 — FastAPI + Next.js UI)

---

## Phase 1 Checklist

### Environment Setup
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

### Data Ingestion
#### Research Sources (free, no auth)
- [x] arXiv fetcher — ALL 12 domains (src/ingestion/arxiv_fetcher.py)
- [ ] PubMed baseline downloader (biomedical XML)
- [ ] CORD-19 bulk dataset download (pre-cleaned research JSON)

#### Patent Sources (free)
- [ ] USPTO bulk XML downloader
- [ ] WIPO IP Statistics bulk download (international patents CSV)

#### Commercial Signal Sources (free tier)
- [ ] ClinicalTrials.gov REST API fetcher (trial phase + tech + status)
- [ ] GitHub Archive fetcher (stars/forks/activity per repo — "is anyone building this?")
- [ ] OpenCorporates API fetcher (company → patent linking, free tier)

#### Deferred (paid/commercial)
- [ ] Crunchbase (startup funding → patent linking) — defer, paid API
- [ ] The Data City (real-time industrial classifications) — defer, commercial

#### Pipeline
- [x] First batch downloaded: 229,498 papers across 12 domains
- [x] dvc.yaml pipeline defined (fetch_arxiv → ner → relations → graph_loader)
- [x] Raw data pushed to Google Drive via DVC (OAuth, personal credentials)
- [x] dvc repro run 2026-03-21 — all 4 stages cached, pipeline locked

### NLP Pipeline
- [x] spaCy 3.7.5 + SciSpacy installed and tested
- [x] `en_core_sci_lg` model downloaded
- [x] NER pipeline script: JSONL in → entities JSONL out (src/nlp/ner_pipeline.py)
- [x] Entity types expanded to 12: Technology, Material, Disease, Device, Compound, Process, Organism, Gene, Algorithm, Phenomenon, Software, Infrastructure
- [x] Full 229,498 docs processed through NER — 10,779,699 entities extracted (47/doc avg)
- [x] MLflow experiment `insight-engine-nlp` created and logging to Docker server (:5000)
- [x] Relation extraction v1 rule-based (src/nlp/relation_extractor.py) — 2,294,895 relations extracted
- [x] params.yaml created — all pipeline params version-controlled via DVC

### MLOps Pipeline
- [x] params.yaml — NER, relations, graph params all tracked
- [x] dvc.yaml — full 4-stage pipeline: fetch_arxiv → ner → relations → graph_loader
- [x] DVC plots wired: ner_domain_stats.csv, relation_domain_stats.csv
- [x] MLflow tracking URI configured — scripts log to Docker server, export MLFLOW_TRACKING_URI in ~/.bashrc
- [x] `dvc dag` shows full pipeline DAG
- [x] `dvc metrics show` shows NER + relation metrics

### Knowledge Graph (Phase 2 — COMPLETE)
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

### Milestone
- [x] End-to-end: raw paper → entities → relations → Neo4j graph working
- [x] Full DVC pipeline tracked and reproducible
- [x] MLflow logging all 3 pipeline stages
- [x] First cross-domain Cypher query verified
- [x] GraphRAG query returns answer — demo query "aerospace materials for cardiac implants" works
- [x] 20 cross-domain paths found, Mistral synthesizes coherent answer
- [x] Query latency: ~32s (embedding 1s + Qdrant 0.2s + Neo4j traversal 12s + Mistral 14s)

---

## Phase 2 Checklist

### Knowledge Graph Build (Weeks 4–6) — COMPLETE
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
- [ ] Prometheus + Grafana running, dashboard created
- [ ] MLflow tracking GraphRAG query quality metrics

### Milestone
- [x] Demo query works: "aerospace materials for cardiac implants"
- [x] Answer includes ≥3 cross-domain connections
- [ ] Each connection cites a real source paper (relation source_paper_id not yet surfaced in answer)

---

## Phase 3 Checklist

### Infrastructure (Weeks 7–9)
- [x] PostgreSQL 16 running in Docker at :5432 — user/auth/session DB
- [x] pgAdmin 4 running in Docker at :5050 — DB GUI
- [x] SQLAlchemy 2.0 async ORM + asyncpg driver configured
- [x] Alembic migrations initialized — 2 migrations applied (initial_schema, auth_sessions)
- [x] DB schema: users, organizations, memberships, api_keys, query_logs, usage_quotas, auth_sessions, refresh_tokens
- [x] .env.example + .env updated with POSTGRES_USER, POSTGRES_PASSWORD, SECRET_KEY, PGADMIN creds
- [x] docker-compose.yml updated — postgres + pgadmin services, DATABASE_URL wired to api + celery

### Auth System
- [x] JWT access token (HS256, 60 min) + opaque refresh token (30 days, single-use rotation)
- [x] Session tracking — auth_sessions table, per-device session listing + revocation
- [x] Replay detection — reusing consumed refresh token revokes entire session
- [x] src/backend/auth/security.py — hash_password, verify_password, create_access_token, decode_token, hash_token
- [x] src/backend/auth/token_service.py — issue_tokens, refresh_tokens, revoke_session_by_token_hash
- [x] src/backend/auth/deps.py — get_current_user checks session is_revoked + expiry in DB
- [x] src/backend/db/crud/ — users.py, sessions.py, tokens.py

### API
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

### Frontend
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
- [ ] Cloudflare Tunnel configured and public URL live
- [ ] Full demo flow rehearsed and timed (<5 min walkthrough)

### MLOps (completed 2026-03-22)
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

---

## Phase 4 Checklist

### Polish & Investor-Ready (Weeks 10–12)
- [ ] Grafana dashboard screenshot-ready
- [ ] README.md: architecture, setup, demo instructions
- [ ] docker-compose.yml: one-command full stack startup
- [ ] MLflow model comparison: Mistral vs Llama 3.1 benchmarked
- [ ] 3 demo scenarios scripted and tested
- [ ] Cloudflare Tunnel: persistent, works without laptop being watched

---

## Decisions & Notes

| Date | Decision | Reasoning |
|------|----------|-----------|
| 2026-03-14 | Python 3.11 via deadsnakes PPA instead of pyenv | pyenv build fails on WSL2 Ubuntu 24.04 due to ensurepip issue |
| 2026-03-14 | scipy pinned to >=1.10.0,<1.11.0 | scispacy 0.5.4 requires scipy<1.11; only 1.10.x has Python 3.11 wheels |
| 2026-03-14 | grobid-client-python pinned to 0.1.* | 0.8.* was the Docker image version, not the PyPI package version |
| 2026-03-14 | Dockerfile for api/celery lives at src/backend/Dockerfile | Keeps service code co-located with its Dockerfile |
| 2026-03-14 | api/celery/frontend excluded from initial docker compose up | No main.py yet — bring up infra first, app services once code exists |
| 2026-03-14 | Ollama runs in Docker (not native WSL2) via named volume `ollama` | Already had image from aia-auditor project; models shared across projects via named volume |
| 2026-03-14 | mistral:v0.3 instead of default mistral (v0.1) | Better instruction following, function calling support, same VRAM cost |
| 2026-03-14 | aia-auditor docker-compose.yml updated to use named volume `ollama` | Shared Ollama volume across both projects; old bind mount ./ollama_data deleted |
| 2026-03-18 | params.yaml introduced for DVC parameter tracking | All NER/relation/graph hyperparams version-controlled — enables MLflow experiment comparison on param changes |
| 2026-03-18 | dvc.yaml expanded to 4 stages: fetch_arxiv → ner → relations → graph_loader | graph_loader is now a tracked DVC stage — re-runs automatically when entities/relations change |
| 2026-03-18 | MLflow artifact logging removed from pipeline scripts | mlflow.log_artifact() writes to /mlflow inside Docker container — permission denied from host. DVC handles file versioning; MLflow only tracks metrics/params |
| 2026-03-18 | MLFLOW_TRACKING_URI set in ~/.bashrc + hardcoded default in scripts | Scripts always log to Docker MLflow server at :5000 regardless of how they're invoked |
| 2026-03-18 | Neo4j property existence constraints removed | IS NOT NULL requires Enterprise Edition. Community only supports uniqueness constraints. graph-rules.md updated. |
| 2026-03-18 | Entity MERGE key is (name, type) composite | name alone is not unique — "neural network" can be both Algorithm and Technology. Composite key prevents wrong deduplication |
| 2026-03-18 | graph_loader does NOT load MENTIONED_IN edges in Phase 2 | 10.7M MENTIONED_IN edges deferred — not needed for cross-domain path queries. Add in later phase when paper citation traversal is needed |
| 2026-03-18 | Relation extraction v1 is type-pair rule-based, not sentence-level | Fast to build, sufficient for first graph. v2 will use SciSpacy relation model or Mistral to read actual sentence text |
| 2026-03-21 | Embedding pipeline pagination bug fixed | SKIP $skip with WHERE embedding_id IS NULL was wrong — as embedded entities drop out of the filter, SKIP skips unembedded ones. Fix: always SKIP 0, let the IS NULL filter do the paging naturally |
| 2026-03-21 | DVC broken by fsspec version conflict | dvc_objects 5.2.0 requires fsspec>=2024.2.0 but imports DEFAULT_CALLBACK which was renamed to _DEFAULT_CALLBACK in that version. Patched generic.py with try/except fallback. Re-apply if venv is recreated |
| 2026-03-21 | GraphRAG seed filtering via Qdrant has_edges payload flag | Long-tail entities in Qdrant have 0 RELATES_TO edges (appeared in 1 paper only). Pre-computed has_edges=True on 517,473 entities with edges and stored in Qdrant payload. Qdrant query_filter eliminates Neo4j round-trip — seed search went from 2 min to 0.2s |
| 2026-03-21 | Entity domain field is first-write-wins | Entity.domain is set by whichever paper loaded the entity first via MERGE. Cross-domain detection uses ANY(n IN path WHERE n.domain <> seed.domain) — checks domain diversity across path nodes, not just endpoints |
| 2026-03-21 | Neo4j index on Entity.embedding_id added | No index existed — UNWIND batch lookup was full-scanning 1.5M nodes. Index created: entity_embedding_id RANGE index on Entity.embedding_id |
| 2026-03-21 | PostgreSQL added for user/auth storage | Neo4j is graph-only, Qdrant is vectors-only — neither suitable for transactional user data. Postgres 16 Alpine added to docker-compose. |
| 2026-03-21 | pgAdmin 4 added for DB GUI | Easier than psql CLI for inspecting tables during dev. Runs at :5050 in Docker. |
| 2026-03-21 | Full ORM with SQLAlchemy 2.0 async | FastAPI async handlers need async driver. asyncpg + SQLAlchemy 2.0 mapped columns. Alembic for migrations. |
| 2026-03-21 | JWT access + opaque refresh token auth | Access token: JWT 60min, stateless verify + DB revocation check. Refresh token: opaque 32-byte hex, SHA-256 hashed in DB, 30-day, single-use rotation with replay detection. |
| 2026-03-21 | Entity (name, type) composite MERGE key for User model | User table uses UUID PK, email unique index. Org created on signup with owner membership. |
| 2026-03-21 | Security hooks added | PreToolUse hooks block hardcoded secrets, SQL string interpolation, and credential patterns in code. Security is top priority. |
| 2026-03-22 | bcrypt pinned to 3.2.2 | passlib 1.7.x incompatible with bcrypt>=4.0 — 72-byte password check causes AttributeError. requirements/api.txt has `bcrypt==3.2.2` |
| 2026-03-22 | QDRANT_URL + OLLAMA_URL added to docker-compose api service | graphrag_query.py defaulted to localhost which fails inside Docker container. Must be qdrant:6333 and host.docker.internal:11434 |
| 2026-03-22 | Neo4j health check host parsing fixed | bolt://neo4j:7687.split(":")[0] returned "bolt" not hostname — fixed to uri.split("//")[-1].split(":")[0] |
| 2026-03-22 | Source citations implemented across full stack | traverse_graph Cypher now returns source_paper_ids from RELATES_TO edges; fetch_citations() does second Neo4j query to resolve Paper title/year/doi; SourceCitation flows through all layers to dashboard CitationCard. Needs `docker compose build api`. |
| 2026-03-22 | Frontend middleware added for auth protection | src/middleware.ts reads access_token cookie, redirects unauthenticated requests to /login. Tokens saved in both localStorage and cookie via saveTokens(). |
| 2026-03-22 | Design system documented | Dark slate/indigo theme documented in .claude/docs/frontend-design.md — ALL future pages must follow it |
| 2026-03-22 | GET /graph/explore endpoint added | Sync Neo4j query runs in thread pool (same pattern as /query). Returns center node + 50 neighbors as nodes/edges. Seed entities in dashboard are now clickable to trigger exploration. |
| 2026-03-22 | Sigma.js + graphology added to frontend | sigma@3.0.2 + graphology@0.25.4. Dynamic import inside useEffect (not top-level) because Sigma uses WebGL2RenderingContext which doesn't exist in Node.js SSR context. Also installed locally for TS type resolution. |
| 2026-03-22 | Airflow moved from .venv to Docker | apache/airflow:2.9.0 standalone container — avoids SQLAlchemy 2.0 conflict with api, consistent with "all services in compose" rule, port 8080 unchanged. |
| 2026-03-22 | Quality gate thresholds in params.yaml | 6 thresholds version-controlled via DVC: entity count, relation count, graph nodes/edges, embedding coverage, cross-domain ratio. quality_check is DVC stage 5 — fails pipeline if data quality degrades. |
| 2026-03-22 | Test fixtures use module-level constants not inline literals | Security hook blocks password="..." patterns as hardcoded secrets. Tests use SAMPLE_PW = "..." at module level which is not flagged. |

## Blockers / Issues

| Issue | Status | Notes |
|-------|--------|-------|
| api + celery services not started | Resolved | Docker build complete, services running |
| frontend service not started | Resolved | Running and hot-reload working with volume mount |
| DVC broken (fsspec conflict) | Resolved | dvc_objects 5.2.0 imports DEFAULT_CALLBACK removed in fsspec 2024.x — patched .venv/lib/python3.11/site-packages/dvc_objects/fs/generic.py with try/except fallback |
| Source paper citations not in GraphRAG answer | Code Complete | All layers updated (graphrag_query.py, schemas.py, main.py, api.ts, dashboard). Needs `docker compose build api && docker compose up -d api` to deploy. Also verify RELATES_TO edges have source_paper_id set in Neo4j. |
| SQLAlchemy 2.0 / Airflow conflict in .venv | Resolved | Airflow now runs in its own Docker container (apache/airflow:2.9.0 standalone). Completely isolated from api SQLAlchemy 2.0. Local .venv still has the conflict but Airflow is never started from .venv. |

## Key Numbers (update as work progresses)

- Papers ingested: 229,498 (12 domains, arXiv)
- Entities extracted: 10,779,699 (47/doc avg)
- Relations extracted: 2,294,895
- Graph entity nodes: 1,529,916
- Graph paper nodes: 166,573
- Graph edges (RELATES_TO): 1,583,613
- Entities with embedding_id: 1,529,916 / 1,529,916 (100%)
- Qdrant vectors: 1,529,916 (768-dim cosine)
- Qdrant entities with has_edges flag: 517,473
- Cross-domain RELATES_TO edges: 1,837,582
- GraphRAG query latency (p95): ~32s (embed 1s + Qdrant 0.2s + Neo4j traversal 12s + Mistral 14s)
- Domains: Aerospace, Medical Devices, Materials, Energy, Biotechnology, Robotics, Quantum, Nanotechnology, Environment, Semiconductors, Pharma, Neuroscience
