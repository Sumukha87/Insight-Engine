<div align="center">

# ⚡ Insight Engine

### Cross-Domain Innovation Discovery via GraphRAG

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.x-008CC1?style=flat&logo=neo4j&logoColor=white)](https://neo4j.com)
[![Qdrant](https://img.shields.io/badge/Qdrant-1.9-FF3B00?style=flat&logoColor=white)](https://qdrant.tech)
[![MLflow](https://img.shields.io/badge/MLflow-2.x-0194E2?style=flat&logo=mlflow&logoColor=white)](https://mlflow.org)
[![DVC](https://img.shields.io/badge/DVC-3.x-945DD6?style=flat&logo=dvc&logoColor=white)](https://dvc.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

**A B2B SaaS platform that finds cross-domain innovation opportunities no keyword search can surface.**

[Architecture](#architecture) · [Demo](#demo-query) · [Tech Stack](#tech-stack) · [Quickstart](#quickstart) · [Roadmap](#roadmap)

</div>

---

## The Problem

Global R&D is siloed.

A battery-longevity breakthrough in **aerospace** may directly solve an unsolved problem in **cardiology** — but no researcher ever makes the connection. A nanomaterial developed for **semiconductors** could transform **drug delivery** — but it's buried in domain-specific literature no one cross-reads.

**Insight Engine is the matchmaker.** It ingests scientific papers at scale, builds a unified knowledge graph across all domains, and uses GraphRAG to surface cross-domain innovation opportunities that no keyword search or standard vector RAG can find.

---

## 4 Intelligence Modules

| Module | Nickname | What It Does |
|--------|----------|-------------|
| Cross-Pollination Discovery | **The Matchmaker** | Finds technologies from Domain A that solve problems in Domain B |
| Trend Velocity Tracking | **The Early Warning System** | Detects technologies being cited across multiple industries before mainstream |
| Patent Portfolio De-Risking | **The Shield** | Surfaces prior art via graph topology, not keyword similarity |
| Automated Gap Analysis | **The Opportunity Finder** | Uses unconnected graph nodes to flag research white-spaces |

---

## Knowledge Graph Stats

| Metric | Value |
|--------|-------|
| Scientific papers ingested | **229,498** (12 domains, arXiv) |
| Entity nodes in graph | **1,529,916** |
| Cross-domain relationship edges | **1,837,582** |
| Vector embeddings (768-dim) | **1,529,916 / 1,529,916** (100%) |
| Domains covered | Aerospace · Medical · Materials · Energy · Biotech · Robotics · Quantum · Nanotechnology · Environment · Semiconductors · Pharma · Neuroscience |
| End-to-end query latency (p95) | **~32s** (embed 1s + Qdrant 0.2s + Neo4j 12s + LLM 14s) |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Browser — Next.js 14 App Router  :3000             │
│  Dashboard · Auth · Graph Explorer · Citations      │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / REST
┌────────────────────▼────────────────────────────────┐
│  FastAPI  :8000                                     │
│  /auth/*  /query  /health  /metrics                 │
│  JWT + refresh token auth · Prometheus metrics      │
└──┬──────────┬──────────┬──────────┬─────────────────┘
   │          │          │          │
┌──▼───┐ ┌───▼───┐ ┌────▼───┐ ┌───▼────┐
│Postgr│ │ Neo4j │ │ Qdrant │ │ Ollama │
│ :5432│ │ :7687 │ │ :6333  │ │ :11434 │
│users │ │ graph │ │vectors │ │Mistral │
└──────┘ └───────┘ └────────┘ └────────┘
              ▲
┌─────────────┴───────────────────────────────────────┐
│  NLP Pipeline (DVC-managed, MLflow-tracked)         │
│  arXiv fetch → spaCy NER → Relation Extraction      │
│  → Neo4j graph loader → Qdrant embedding pipeline   │
└─────────────────────────────────────────────────────┘
```

**5-Layer Stack:**

| Layer | Components |
|-------|-----------|
| L5 — Application | FastAPI REST API + Next.js 14 frontend |
| L4 — Knowledge Graph | Neo4j Community — 1.5M entities, 1.8M edges |
| L3 — Vector Search | Qdrant — 768-dim nomic-embed-text embeddings |
| L2 — NLP Pipeline | spaCy 3.7 + SciSpacy NER · Rule-based relation extraction |
| L1 — Ingestion | arXiv bulk API · DVC pipeline · MLflow experiment tracking |

---

## GraphRAG Query Flow

```
User query (natural language)
    │
    ▼
Entity extraction — spaCy NER on query text
    │
    ▼
Embedding — nomic-embed-text via Ollama (768-dim)
    │
    ▼
Qdrant ANN search — filtered to entities with graph edges
    │  (has_edges payload flag — eliminates 1M+ dead-end seeds instantly)
    ▼
Neo4j graph traversal — cross-domain paths up to 4 hops
    │  MATCH path = (seed)-[RELATES_TO*1..4]-(target {domain: $target})
    ▼
Subgraph context assembly — entities + relations + source paper IDs
    │
    ▼
LLM synthesis — Mistral 7B via Ollama
    │  "Given these cross-domain graph paths, answer: [query]. Cite sources."
    ▼
Response: { answer, paths[], sources[], confidence, latency_ms }
```

---

## Demo Query

**Query:** *"What aerospace materials could improve cardiac implant longevity?"*

```
🔍 Searching knowledge graph...
   Seed entities found: titanium alloy, carbon fiber composite, shape memory alloy
   Cross-domain paths discovered: 20
   Source papers resolved: 14

💡 Answer:
   Three aerospace materials show strong cross-domain potential for cardiac implants:

   1. Nitinol (shape memory alloy) — developed for aerospace actuators, already
      transitioning to stents. Graph path: aerospace/actuators → materials/superelastic
      → medical/cardiovascular. Cited in 847 papers across both domains.

   2. Carbon fiber composites — used in structural aerospace components, now emerging
      in radiolucent implant housings. 12 direct cross-domain RELATES_TO edges found.

   3. Titanium-Zirconium alloys — aerospace fatigue resistance research (Ti-Zr-Nb)
      maps directly onto long-term implant load cycling requirements.

📚 Sources: 14 papers cited (arXiv: 2021–2024)
⏱  Latency: 31.4s
```

---

## Tech Stack

### AI / ML
![spaCy](https://img.shields.io/badge/spaCy-3.7-09A3D5?style=flat&logo=spacy&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Mistral_7B-000000?style=flat&logoColor=white)
![nomic](https://img.shields.io/badge/nomic--embed--text-768dim-7C3AED?style=flat&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.3-EE4C2C?style=flat&logo=pytorch&logoColor=white)
![LlamaIndex](https://img.shields.io/badge/LlamaIndex-0.10-7C3AED?style=flat&logoColor=white)

### MLOps
![MLflow](https://img.shields.io/badge/MLflow-2.x-0194E2?style=flat&logo=mlflow&logoColor=white)
![DVC](https://img.shields.io/badge/DVC-3.x-945DD6?style=flat&logo=dvc&logoColor=white)
![Airflow](https://img.shields.io/badge/Airflow-2.9-017CEE?style=flat&logo=apacheairflow&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-2.x-E6522C?style=flat&logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-10.x-F46800?style=flat&logo=grafana&logoColor=white)

### Databases & Vector Stores
![Neo4j](https://img.shields.io/badge/Neo4j-5.x-008CC1?style=flat&logo=neo4j&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-1.9-FF3B00?style=flat&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat&logo=redis&logoColor=white)

### Backend & Frontend
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat&logo=nextdotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat&logo=typescript&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-3-06B6D4?style=flat&logo=tailwindcss&logoColor=white)

### Infrastructure
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)

---

## Project Structure

```
insight-engine/
├── src/
│   ├── ingestion/          # arXiv fetcher — 12 domains, 229K papers
│   ├── nlp/
│   │   ├── ner_pipeline.py         # spaCy NER → 10.7M entities extracted
│   │   └── relation_extractor.py   # 2.3M relations extracted
│   ├── graph/
│   │   ├── graph_loader.py         # JSONL → Neo4j MERGE
│   │   ├── embedding_pipeline.py   # entities → Qdrant (768-dim)
│   │   └── graphrag_query.py       # full GraphRAG query engine
│   ├── backend/            # FastAPI app — auth, query, health
│   └── frontend/           # Next.js 14 App Router dashboard
├── dags/                   # Apache Airflow DAGs
├── dvc.yaml                # 4-stage reproducible pipeline
├── params.yaml             # all hyperparams version-controlled
├── docker-compose.yml      # full stack — one command startup
└── requirements/           # nlp.txt · graph.txt · api.txt · mlops.txt
```

---

## Quickstart

**Prerequisites:** Docker Desktop, NVIDIA GPU (8GB+ VRAM recommended), Ollama

```bash
# 1. Clone
git clone https://github.com/Sumukha87/Insight-Engine.git
cd Insight-Engine

# 2. Environment
cp .env.example .env
# Edit .env with your passwords

# 3. Start full stack
docker compose up -d

# 4. Pull LLM models (first time only)
docker exec ollama ollama pull mistral:v0.3
docker exec ollama ollama pull nomic-embed-text

# 5. Run pipeline (fetch → NER → relations → graph)
source .venv/bin/activate
dvc repro

# 6. Open dashboard
open http://localhost:3000
```

Services after startup:

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Query dashboard |
| API | http://localhost:8000/docs | FastAPI Swagger |
| Neo4j Browser | http://localhost:7474 | Graph explorer |
| MLflow | http://localhost:5000 | Experiment tracking |
| Grafana | http://localhost:3001 | Metrics dashboard |
| pgAdmin | http://localhost:5050 | Database GUI |

---

## Roadmap

- [x] Phase 1 — Data ingestion pipeline (229K papers, 12 domains)
- [x] Phase 2 — Knowledge graph + vector embeddings + GraphRAG engine
- [x] Phase 3 — FastAPI backend + Next.js dashboard + JWT auth
- [ ] Phase 4 — Sigma.js graph explorer · Grafana dashboards · Cloudflare Tunnel
- [ ] Phase 5 — Patent data (USPTO) · Clinical trials · GitHub activity signals
- [ ] Phase 6 — Multi-tenant SaaS · usage quotas · billing

---

## About the Author

Built by **SriSumukha S** — Infrastructure & Full-Stack Engineer at [JEMS Inc., Japan](https://www.jems.co.jp), working on IT systems for environmental and waste management.

At work: Spring Boot APIs · Next.js frontends · Terraform on AWS & GCP. Built an in-house CRM that replaced Salesforce and is still in production.

On the side: building production AI systems from scratch — knowledge graphs, LLM pipelines, and MLOps tooling.

**Certifications:** AWS AI Practitioner · AWS Cloud Practitioner · JLPT N3

[![LinkedIn](https://img.shields.io/badge/LinkedIn-SriSumukha_S-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/srisumukha-s-81a9591b7/)
[![Portfolio](https://img.shields.io/badge/Portfolio-sumukha.netlify.app-6366f1?style=flat&logoColor=white)](https://sumukha.netlify.app/)

---

<div align="center">
<sub>Built with curiosity · Powered by open-source · Running locally on an RTX 4060</sub>
</div>
