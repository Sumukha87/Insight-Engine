# Architecture Reference

## System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  User (Browser)                                             │
│  Next.js 14 frontend — localhost:3000                       │
│  Sigma.js graph visualizer | shadcn/ui components          │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP / WebSocket
┌────────────────────▼────────────────────────────────────────┐
│  FastAPI backend — localhost:8000                           │
│  /auth/* /query /graph/explore /trending /health            │
│  JWT + refresh token auth | Celery workers                  │
│  Prometheus metrics endpoint                                │
└──┬──────────┬──────────┬──────────┬──────────┬──────────────┘
   │          │          │          │          │
┌──▼───┐ ┌───▼───┐ ┌────▼───┐ ┌───▼───┐ ┌───▼────┐
│Postgr│ │ Neo4j │ │ Qdrant │ │Ollama │ │ MLflow │
│ :5432│ │ :7687 │ │ :6333  │ │:11434 │ │ :5000  │
│users │ │ graph │ │vectors │ │Mistr7B│ │tracking│
└──────┘ └───────┘ └────────┘ └───────┘ └────────┘
                                 │
  ┌──────────────────────────────┘
  │   pgAdmin :5050 (DB GUI)
  │
┌─▼────────────────────────────────────────────────────────┐
│  NLP Pipeline (Python processes)                          │
│  Grobid:8070 → spaCy NER → Relation Extraction → Graph    │
│  DVC manages all data pipeline stages                     │
└──────┬────────────────────────────────────────────────────┘
       │
┌──────▼────────────────────────────────────────────────────┐
│  Raw Data (S3-compatible local storage / DVC-tracked)     │
│  PubMed XML  |  arXiv PDFs  |  USPTO bulk XML             │
│  data/raw/   |  data/processed/  |  data/graph/           │
└───────────────────────────────────────────────────────────┘
```

## GraphRAG Query Flow

```
User query (natural language)
    │
    ▼
Query router (FastAPI)
    │
    ├─► Entity extraction (spaCy NER on query text)
    │
    ├─► Embedding (nomic-embed-text via Ollama)
    │       │
    │       ▼
    │   Qdrant ANN search → seed entity IDs
    │
    ▼
Neo4j graph traversal
    │  MATCH path = (seed)-[*1..4]-(target {domain: $target_domain})
    │  RETURN path, relationships ORDER BY path_score DESC LIMIT 10
    │
    ▼
Subgraph context assembly
    │  Collect: entities + edge types + source paper citations
    │
    ▼
LLM synthesis (Mistral 7B via Ollama)
    │  Prompt: "Given these cross-domain graph paths [context],
    │           answer: [user query]. Cite each source."
    │
    ▼
Response: { answer, paths[], sources[], confidence }
```

## Neo4j Graph Schema

### Node Types
| Label           | Key Properties                              | Description                          |
|-----------------|---------------------------------------------|--------------------------------------|
| Entity          | name, type, domain, embedding_id            | Core knowledge node                  |
| Paper           | doi, title, year, journal, domain           | Scientific publication (arXiv/PubMed/CORD-19) |
| Patent          | number, title, year, assignee, cpc, source  | Patent filing (USPTO / WIPO)         |
| Author          | name, institution                           | Person entity                        |
| ClinicalTrial   | nct_id, title, phase, status, sponsor, year | ClinicalTrials.gov trial record      |
| GitHubRepo      | repo_id, name, stars, forks, last_commit    | GitHub repo linked to a paper/patent |
| Company         | name, country, opencorporates_id            | Company linked to patent/startup     |

### Entity Types (values of Entity.type)
`Technology`, `Material`, `Disease`, `Compound`, `Device`, `Process`, `Organism`, `Gene`

### Edge Types
| Type            | From → To                    | Properties                        |
|-----------------|------------------------------|-----------------------------------|
| MENTIONED_IN    | Entity → Paper/Patent        | position, frequency               |
| CITES           | Paper → Paper                | year_delta                        |
| RELATES_TO      | Entity → Entity              | relation, confidence, source      |
| FROM_DOMAIN     | Entity → Domain node         | —                                 |
| AUTHORED_BY     | Paper → Author               | —                                 |
| TESTED_IN       | Entity → ClinicalTrial       | phase, trial_id                   |
| BUILT_ON        | Entity → GitHubRepo          | stars, forks, last_commit         |
| FILED_BY        | Patent → Company             | country, year                     |
| PATENTED_IN     | Patent → Patent (WIPO→USPTO) | country, year                     |

### Key Cypher Patterns

```cypher
// Cross-domain path discovery
MATCH path = (a:Entity {domain:'Aerospace'})-[r:RELATES_TO*1..4]-(b:Entity {domain:'Medical'})
WHERE a.name CONTAINS $keyword
RETURN path, [rel in relationships(path) | rel.relation] as relations
ORDER BY length(path) ASC
LIMIT 20

// Trend velocity: citation centrality over time
MATCH (e:Entity)-[:MENTIONED_IN]->(p:Paper)
WHERE p.year >= date().year - 2
WITH e, count(p) as recent_citations
ORDER BY recent_citations DESC
RETURN e.name, e.domain, recent_citations LIMIT 50

// Gap analysis: high-research entities with no treatment connections
MATCH (d:Entity {type:'Disease'})-[:MENTIONED_IN]->(p:Paper)
WHERE NOT EXISTS {
  MATCH (d)-[:RELATES_TO {relation:'TREATED_BY'}]->(:Entity {type:'Compound'})
}
WITH d, count(p) as paper_count
WHERE paper_count > 50
RETURN d.name, paper_count ORDER BY paper_count DESC
```

## Data Directory Layout

```
data/
├── raw/
│   ├── arxiv/            # arXiv abstract JSONs (DVC tracked)
│   ├── pubmed/           # PubMed XML baseline files (DVC tracked)
│   ├── cord19/           # CORD-19 bulk research JSON (DVC tracked)
│   ├── uspto/            # USPTO bulk XML (DVC tracked)
│   ├── wipo/             # WIPO IP Statistics CSV (DVC tracked)
│   ├── clinicaltrials/   # ClinicalTrials.gov JSON (DVC tracked)
│   ├── github/           # GitHub repo activity JSON (DVC tracked)
│   └── opencorporates/   # Company→patent linking JSON (DVC tracked)
├── processed/
│   ├── parsed/           # Grobid JSON output per paper
│   ├── entities/         # NER output JSONL per batch
│   └── relations/        # Relation extraction output JSONL
└── graph/
    ├── nodes.csv         # Ready-to-load node CSVs
    └── edges.csv         # Ready-to-load edge CSVs
```

## Signal Pattern: "Success Pattern" Detection

The key insight that makes Insight-Engine valuable:

```
arXiv paper (year N)
    └──MENTIONED_IN──► Entity
                           └──TESTED_IN──► ClinicalTrial (Phase III)
                           └──BUILT_ON───► GitHubRepo (stars exploding)
                           └──MENTIONED_IN──► USPTO Patent
                                                  └──FILED_BY──► Company
                                                  └──PATENTED_IN──► WIPO (40+ countries)
```

When all 5 signals align on one Entity = **confirmed cross-domain breakthrough**.

## PostgreSQL Schema (User/Auth DB)

```
users            — id (UUID), email (unique), hashed_password, full_name, job_title,
                   is_active, is_verified, last_login_at, created_at, updated_at
organizations    — id, name, plan_tier (free/starter/pro/enterprise), created_at
memberships      — id, user_id (FK), org_id (FK), role (owner/member/viewer), created_at
auth_sessions    — id, user_id (FK), access_token_hash (SHA-256), user_agent, ip_address,
                   created_at, expires_at, is_revoked
refresh_tokens   — id, session_id (FK), user_id (FK), token_hash (SHA-256), created_at,
                   expires_at, used_at, is_revoked
api_keys         — id, org_id (FK), name, key_hash (unique), last_used_at, expires_at
query_logs       — id, org_id (FK), user_id (FK), query_text, latency_ms, created_at
usage_quotas     — id, org_id (FK, unique), period_start, queries_used, queries_limit
```

Managed via SQLAlchemy 2.0 async ORM + Alembic migrations.
Connection: `postgresql+asyncpg://` via `DATABASE_URL` env var.
GUI: pgAdmin at `http://localhost:5050`.

## Auth Flow

```
POST /auth/register  → create user + org + session → {access_token, refresh_token}
POST /auth/login     → verify creds + create session → {access_token, refresh_token}
POST /auth/refresh   → rotate refresh token (single-use) → {access_token, refresh_token}
POST /auth/logout    → revoke session + refresh token
GET  /auth/me        → current user profile
GET  /auth/sessions  → list active sessions
DELETE /auth/sessions/{id} → revoke specific session (remote logout)

Access token:  JWT (HS256), 60 min, checked against auth_sessions.is_revoked
Refresh token: opaque 32-byte hex, SHA-256 hashed in DB, 30-day expiry, single-use rotation
Replay detection: reusing a consumed refresh token revokes the entire session
```

## Service Dependencies & Startup Order

```
1. postgres    (no deps)
2. neo4j       (no deps)
3. qdrant      (no deps)
4. grobid      (no deps)
5. ollama      (no deps, needs GPU access)
6. mlflow      (no deps)
7. prometheus  (no deps)
8. grafana     (depends: prometheus)
9. redis       (no deps)
10. pgadmin    (depends: postgres)
11. celery     (depends: redis, neo4j, qdrant, ollama, postgres)
12. api        (depends: all above)
13. frontend   (depends: api)
```

`docker compose up -d` handles this order automatically via `depends_on`.
