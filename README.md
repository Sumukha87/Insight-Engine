# Insight-Engine Prototype

Strategic Intelligence Platform — Cross-domain innovation discovery via GraphRAG.

## Quick Start (WSL2)

```bash
# 1. Clone and enter project
git clone <repo-url> insight-engine
cd insight-engine

# 2. Set up Python environment
pyenv install 3.11.9
pyenv local 3.11.9
python -m venv .venv
source .venv/activate

# 3. Copy and fill environment variables
cp .env.example .env
# Edit .env with your passwords

# 4. Install Ollama (native WSL2 — NOT in Docker)
curl https://ollama.ai/install.sh | sh
ollama pull mistral
ollama pull nomic-embed-text

# 5. Start all Docker services
mkdir -p volumes/{neo4j/{data,logs,plugins},qdrant,redis,mlflow,grafana,prometheus}
docker compose up -d

# 6. Verify all services healthy
docker compose ps

# 7. Apply Neo4j schema
docker exec -it ie-neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD < scripts/schema.cypher
```

## Service URLs

| Service       | URL                            |
|---------------|--------------------------------|
| Frontend      | http://localhost:3000          |
| API docs      | http://localhost:8000/docs     |
| Neo4j browser | http://localhost:7474          |
| Qdrant UI     | http://localhost:6333/dashboard|
| MLflow        | http://localhost:5000          |
| Grafana       | http://localhost:3001          |
| Prometheus    | http://localhost:9090          |

## Project Structure

```
insight-engine/
├── CLAUDE.md              ← Claude Code context (read this)
├── CLAUDE.local.md        ← Your local notes (gitignored)
├── docs/
│   ├── architecture.md    ← System design reference
│   ├── stack.md           ← Tool versions and rationale
│   └── progress.md        ← Current phase, task checklist
├── .claude/
│   └── rules/             ← Domain-specific Claude Code rules
│       ├── nlp-rules.md
│       ├── graph-rules.md
│       └── api-rules.md
├── src/
│   ├── ingestion/         ← Data downloaders (PubMed, arXiv, USPTO)
│   ├── nlp/               ← NER, relation extraction pipelines
│   ├── graph/             ← Neo4j loaders, Qdrant embedding pipeline
│   ├── graphrag/          ← LlamaIndex GraphRAG query engine
│   ├── api/               ← FastAPI app
│   └── workers/           ← Celery async tasks
├── frontend/              ← Next.js 14 app
├── tests/                 ← pytest test suite
├── config/                ← Prometheus, Grafana config files
├── scripts/               ← One-off scripts (schema.cypher, etc.)
├── data/                  ← DVC-tracked data (raw → processed → graph)
├── docker-compose.yml
├── .env.example
└── dvc.yaml               ← DVC pipeline definition
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for full system diagram and query flow.

## Claude Code Usage

This project is built with Claude Code. At the start of each session:

```
# Claude Code automatically reads CLAUDE.md
# For architecture details:
@docs/architecture.md

# For current progress:
@docs/progress.md

# For stack decisions:
@docs/stack.md
```
