# Progress Tracker

> Update this file at the end of every Claude Code session.
> Claude Code: check this file first with `@docs/progress.md` at session start.

## Current Phase

**Phase 1 — Data Ingestion & NLP Pipeline**
Status: IN PROGRESS
Target: Weeks 1–3

---

## Phase 1 Checklist

### Environment Setup
- [x] WSL2 Python 3.11 via deadsnakes PPA (pyenv not used — build issues on WSL2, deadsnakes more reliable)
- [x] Docker Desktop WSL2 integration enabled
- [x] `nvidia-smi` shows RTX 4060 in WSL2 — GPU confirmed visible
- [x] Ollama running via Docker (not native WSL2) — container name `ollama`, named volume `ollama`, port 11434
- [x] `ollama pull mistral:v0.3` complete (switched from v0.1 — better instruction following, same size)
- [x] `ollama pull nomic-embed-text` complete
- [ ] GitHub repo created and connected
- [ ] DVC initialized (`dvc init`)
- [x] `.env` file created from `.env.example`
- [x] `docker compose up -d` — infrastructure services healthy (neo4j, qdrant, grobid, redis, mlflow, prometheus, grafana)

### Data Ingestion
- [ ] PubMed baseline downloader script written
- [ ] arXiv API fetcher written (target domain: Aerospace)
- [ ] arXiv API fetcher written (target domain: Medical Devices)
- [ ] USPTO bulk XML downloader written
- [ ] First batch downloaded: target 50K papers
- [ ] DVC pipeline stage: `dvc run` for ingestion
- [ ] Data committed to DVC, `.dvc` files committed to git

### PDF Parsing
- [ ] Grobid running in Docker at :8070
- [ ] `grobid_client` Python wrapper working
- [ ] Batch parser script: PDF → structured JSON
- [ ] 10K papers parsed successfully
- [ ] Parsed output stored in `data/processed/parsed/`

### NLP Pipeline
- [ ] spaCy + SciSpacy installed and tested
- [ ] `en_core_sci_lg` model downloaded
- [ ] NER pipeline script: JSONL in → entities JSONL out
- [ ] Entity types confirmed: Technology, Material, Disease, Device, Process
- [ ] Relation extraction: rule-based v1 (TREATS, IMPROVES, DERIVED_FROM)
- [ ] First 10K docs processed through NER
- [ ] MLflow experiment created: `nlp-ner-v1`
- [ ] Metrics logged: precision, recall, entity_count_per_domain
- [ ] MLflow UI shows experiment at localhost:5000

### Milestone
- [ ] End-to-end: raw paper → entities → MLflow log working
- [ ] Processed 50K+ papers through full pipeline
- [ ] Summary: entity counts per domain documented here

---

## Phase 2 Checklist

### Knowledge Graph Build (Weeks 4–6)
- [ ] Neo4j Community running in Docker at :7474 / :7687
- [ ] Graph schema Cypher file written: `scripts/schema.cypher`
- [ ] Schema applied to Neo4j (constraints + indexes)
- [ ] Node loader script: entities CSV → Neo4j MERGE
- [ ] Edge loader script: relations CSV → Neo4j relationships
- [ ] First 100K entities loaded into graph
- [ ] First cross-domain Cypher query returns results
- [ ] Qdrant running in Docker at :6333
- [ ] Embedding pipeline: entity text → nomic-embed-text → Qdrant upsert
- [ ] LlamaIndex KnowledgeGraphIndex connected to Neo4j + Qdrant
- [ ] First GraphRAG query returns answer with source citations
- [ ] Prometheus + Grafana running, dashboard created
- [ ] MLflow tracking GraphRAG query quality metrics

### Milestone
- [ ] Demo query works: "aerospace materials for cardiac implants"
- [ ] Answer includes ≥3 cross-domain connections
- [ ] Each connection cites a real source paper

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

## Blockers / Issues

| Issue | Status | Notes |
|-------|--------|-------|
| api + celery services not started | Open | Need src/backend/main.py before these can run |
| frontend service not started | Open | Next.js app exists at src/frontend but no API to connect to yet |

## Key Numbers (update as work progresses)

- Papers ingested: 0
- Entities extracted: 0
- Graph nodes: 0
- Graph edges: 0
- GraphRAG query latency (p95): —
- Demo corpus domains: Aerospace, Medical Devices
