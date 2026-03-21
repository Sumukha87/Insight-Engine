# Progress Tracker

> Update this file at the end of every Claude Code session.
> Claude Code: check this file first with `@docs/progress.md` at session start.

## Current Phase

**Phase 2 → Phase 3 transition**
Status: Phase 2 COMPLETE. Phase 3 NEXT.
Target: Weeks 4–6 (Phase 2 done) → Weeks 7–9 (Phase 3 — FastAPI + Next.js UI)

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

### Web UI & Demo App (Weeks 7–9)
- [ ] FastAPI endpoints: /query, /graph/explore, /trending, /health
- [ ] FastAPI /docs working with Pydantic schemas
- [ ] Next.js app bootstrapped with shadcn/ui
- [ ] Query interface: text input → streamed answer
- [ ] Graph explorer: Sigma.js rendering entity neighborhood
- [ ] Source citations panel below answer
- [ ] Cloudflare Tunnel configured and public URL live
- [ ] Full demo flow rehearsed and timed (<5 min walkthrough)

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

## Blockers / Issues

| Issue | Status | Notes |
|-------|--------|-------|
| api + celery services not started | Open | Need src/backend/main.py before these can run — Phase 3 work |
| frontend service not started | Open | Next.js app exists at src/frontend but no API to connect to yet — Phase 3 work |
| DVC broken (fsspec conflict) | Resolved | dvc_objects 5.2.0 imports DEFAULT_CALLBACK removed in fsspec 2024.x — patched .venv/lib/python3.11/site-packages/dvc_objects/fs/generic.py with try/except fallback |
| Source paper citations not in GraphRAG answer | Open | RELATES_TO edges have source_paper_id but it is not surfaced in graphrag_query.py response yet |

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
