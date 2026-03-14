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

## Key Rules — Always Follow

- **WSL2 paths**: use `/home/$USER/` not `/mnt/c/`. Docker volumes must use WSL2 paths.
- **Python**: 3.11 via pyenv. Always activate venv before installing: `source .venv/bin/activate`.
- **Docker**: all services defined in `docker-compose.yml`. Never run services outside of compose during dev.
- **GPU**: Ollama uses the RTX 4060 (8GB VRAM). Max model size = 8B params at Q4. Do not load multiple models simultaneously.
- **No cloud spend**: everything runs locally. No OpenAI API calls. No AWS. Ollama for LLM, nomic-embed-text for embeddings.
- **Data is versioned**: never modify raw data files directly. All ingestion output goes through DVC pipelines.
- **Experiments are tracked**: every NLP model run logs to MLflow. Never run training without `mlflow.start_run()`.

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

# Tests
pytest tests/ -v
pytest tests/unit/ -v --no-header
```

## Phase Status

See @docs/progress.md for current phase, completed tasks, and next steps.
See @docs/architecture.md for the overall architechure 
See @docs/stack.md for all the stck we are using 
## Coding Conventions

- Python: black formatter, isort imports, type hints on all functions, docstrings on classes.
-Next 14 frontend with static rendering and no SSR
- FastAPI: async handlers only. Pydantic v2 models for all request/response shapes.
- React: functional components only, TypeScript strict mode, Zustand for global state.
- Cypher: always use parameters, never string interpolation. Use `MERGE` not `CREATE` for entities.
- Tests: pytest for Python, Vitest for TypeScript. Test files mirror src structure in `tests/`.
- Commits: conventional commits format (`feat:`, `fix:`, `chore:`, `docs:`).
