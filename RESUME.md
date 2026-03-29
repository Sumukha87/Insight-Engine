# Insight Engine — Resume Checklist

> Pick this up when returning to the project.
> All Docker containers have been deleted — full environment rebuild required.

---

## Step 1 — Rebuild Environment

```bash
# 1. Confirm GPU is visible
nvidia-smi

# 2. Bring up all Docker services
docker compose up -d

# 3. Pull Ollama models (models were in a named volume — may need re-pulling after container delete)
docker exec ollama ollama pull mistral:v0.3
docker exec ollama ollama pull nomic-embed-text

# 4. Activate Python venv
source .venv/bin/activate

# 5. Apply Neo4j schema constraints + indexes
# (run the Cypher from .claude/rules/graph-rules.md in Neo4j browser at http://localhost:7474)

# 6. Re-run DVC pipeline to reload graph data
dvc repro
```

> **Note:** DVC has a pathspec import error (`_DIR_MARK`). If `dvc repro` fails, check:
> ```bash
> pip install --upgrade pathspec
> # or pin: pip install "pathspec==0.11.2"
> ```

---

## Step 2 — Verify Data Is Loaded

After `dvc repro`, check key numbers match:

| Metric | Expected |
|--------|----------|
| Entity nodes in Neo4j | 1,529,916 |
| Paper nodes in Neo4j | 166,573 |
| RELATES_TO edges | 1,583,613 |
| Qdrant vectors | 1,529,916 |
| Qdrant `has_edges` entities | 517,473 |

Run a smoke test:
```bash
source .venv/bin/activate
python src/graph/graphrag_query.py --query "aerospace materials for cardiac implants"
# Expected: 20 cross-domain paths, Mistral answer, ~32s latency
```

---

## Step 3 — New Data Sources (Priority Work)

These were deferred in Phase 1 and are **the next major development area**. Each adds a new signal layer to the graph.

### Research Sources (free, no auth required)

| Source | Script location | What it adds |
|--------|----------------|--------------|
| **PubMed baseline** | `src/ingestion/pubmed_fetcher.py` (TODO) | Biomedical XML — deeper medical/pharma coverage |
| **CORD-19** | `src/ingestion/cord19_fetcher.py` (TODO) | Pre-cleaned COVID research JSON — 200K+ papers |

### Patent Sources (free)

| Source | Script location | What it adds |
|--------|----------------|--------------|
| **USPTO bulk XML** | `src/ingestion/uspto_fetcher.py` (TODO) | Patent filings → `Patent` nodes + `FILED_BY` edges |
| **WIPO IP Statistics** | `src/ingestion/wipo_fetcher.py` (TODO) | International patent CSV → cross-country patent graph |

### Commercial Signal Sources (free tier)

| Source | Script location | What it adds |
|--------|----------------|--------------|
| **ClinicalTrials.gov** | `src/ingestion/clinicaltrials_fetcher.py` (TODO) | `ClinicalTrial` nodes — TESTED_IN edges (trial phase is a strong signal) |
| **GitHub Archive** | `src/ingestion/github_fetcher.py` (TODO) | `GitHubRepo` nodes — BUILT_ON edges (stars/forks = adoption signal) |
| **OpenCorporates** | `src/ingestion/opencorporates_fetcher.py` (TODO) | `Company` nodes — FILED_BY edges (patent → company → country) |

### Deferred (paid APIs — skip for now)

- Crunchbase (startup funding → patent linking)
- The Data City (industrial classifications)

### For each new source, the full pipeline is:

```
Fetcher script → data/raw/<source>/ (DVC tracked)
    → NER pipeline (reuse src/nlp/ner_pipeline.py)
    → Relation extractor (reuse src/nlp/relation_extractor.py)
    → Graph loader (extend src/graph/graph_loader.py for new node/edge types)
    → Add DVC stage in dvc.yaml
    → Log to MLflow experiment insight-engine-nlp
```

New node/edge types to implement (defined in `.claude/docs/architecture.md`):
- `Patent` nodes with `MENTIONED_IN`, `FILED_BY`, `PATENTED_IN` edges
- `ClinicalTrial` nodes with `TESTED_IN` edges
- `GitHubRepo` nodes with `BUILT_ON` edges
- `Company` nodes with `FILED_BY` edges
- `Author` nodes with `AUTHORED_BY` edges

---

## Step 4 — Finish Phase 3

Two items remain before Phase 3 is complete:

- [ ] **Cloudflare Tunnel** — persistent public HTTPS URL for the demo
  ```bash
  # Install cloudflared in WSL2, then:
  cloudflared tunnel create insight-engine
  cloudflared tunnel route dns insight-engine <your-subdomain>.trycloudflare.com
  cloudflared tunnel run insight-engine
  ```
- [ ] **Demo flow rehearsal** — run through the 3 demo scenarios, time each (<5 min total)

---

## Step 5 — Phase 4 (Polish)

- [ ] MLflow model comparison: Mistral vs Llama 3.1 benchmarked on same query set
- [ ] Grafana dashboards screenshot-ready
- [ ] 3 demo scenarios scripted and tested end-to-end
- [ ] README.md: final architecture diagram, quickstart, demo instructions
- [ ] One-command full stack: `docker compose up -d` starts everything cleanly

---

## Known Issues to Fix on Return

| Issue | Symptom | Fix |
|-------|---------|-----|
| DVC pathspec error | `cannot import name '_DIR_MARK'` | `pip install "pathspec==0.11.2"` or upgrade pathspec |
| Ollama models gone | Container was deleted | Re-pull mistral:v0.3 and nomic-embed-text |
| Neo4j data gone | Container was deleted | Re-run `dvc repro` to reload from DVC cache |
| Qdrant vectors gone | Container was deleted | Re-run `python src/graph/embedding_pipeline.py` |

---

## Key Service URLs (once docker compose is up)

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| FastAPI | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |
| Qdrant | http://localhost:6333/dashboard |
| MLflow | http://localhost:5000 |
| Grafana | http://localhost:3001 |
| pgAdmin | http://localhost:5050 |
| Airflow | http://localhost:8080 |
