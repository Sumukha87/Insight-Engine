# Technology Stack

## Versions (pinned for reproducibility)

| Layer         | Tool                  | Version   | Why                                              |
|---------------|-----------------------|-----------|--------------------------------------------------|
| LLM           | Ollama                | latest    | Local LLM server, OpenAI-compatible API          |
| LLM model     | Mistral 7B (Q4_K_M)   | 0.3       | Fits in 4.1GB VRAM, best quality/size ratio      |
| LLM fallback  | Llama 3.1 8B (Q4_K_M) | 3.1       | Slightly larger, better instruction following    |
| Embeddings    | nomic-embed-text      | v1.5      | 768-dim, free, runs via Ollama, strong quality   |
| Graph DB      | Neo4j Community       | 5.x       | Full Cypher, GDS algorithms, browser UI included |
| Vector DB     | Qdrant                | 1.9.x     | Best OSS vector DB, local Docker, good Python SDK|
| NLP           | spaCy                 | 3.7.x     | Fast, production-grade NLP                       |
| NLP models    | SciSpacy en_core_sci_lg| 0.5.4    | Biomedical entity types out of the box           |
| PDF parse     | Grobid                | 0.8.0     | Best open-source scientific PDF parser           |
| RAG framework | LlamaIndex            | 0.10.x    | KnowledgeGraphIndex connects to Neo4j natively   |
| Data version  | DVC                   | 3.x       | Git-like versioning for data files and pipelines |
| ML tracking   | MLflow                | 2.x       | Local experiment tracking, model registry        |
| Orchestration | Apache Airflow        | 2.x       | DAG-based pipeline scheduling (Phase 2+)         |
| API           | FastAPI               | 0.111.x   | Async, auto OpenAPI docs, Pydantic v2            |
| Frontend      | Next.js               | 14.x      | App Router, SSR, easy API routes                 |
| Graph viz     | Sigma.js              | 3.x       | WebGL, handles 100K+ nodes in browser            |
| UI components | shadcn/ui + Tailwind  | latest    | Clean enterprise components                      |
| State         | Zustand               | 4.x       | Minimal global state                             |
| Server state  | TanStack Query        | 5.x       | Server state sync, caching                       |
| Monitoring    | Prometheus            | 2.x       | Metrics scraping                                 |
| Dashboards    | Grafana               | 10.x      | Visualization of Prometheus metrics              |
| Containers    | Docker Compose        | v2        | Single-file local orchestration                  |
| Python mgmt   | pyenv + venv          | 3.11      | Clean Python version management in WSL2          |
| Formatter     | black + isort         | latest    | Consistent Python formatting                     |
| Type check    | mypy                  | latest    | Strict type checking                             |
| Test          | pytest                | 7.x       | Python testing                                   |
| Test (TS)     | Vitest                | 1.x       | Fast TypeScript unit testing                     |
| CI            | GitHub Actions        | —         | Free CI, auto-runs tests on push                 |
| Tunnel        | Cloudflare Tunnel     | latest    | Free, permanent public HTTPS URL                 |

## Python Package Groups

### Core NLP (`requirements/nlp.txt`)
```
spacy==3.7.*
scispacy==0.5.4
https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_lg-0.5.4.tar.gz
transformers==4.40.*
torch==2.3.*          # CPU or CUDA depending on task
sentence-transformers==3.0.*
```

### Graph (`requirements/graph.txt`)
```
neo4j==5.*
qdrant-client==1.9.*
llama-index==0.10.*
llama-index-graph-stores-neo4j
llama-index-vector-stores-qdrant
llama-index-llms-ollama
llama-index-embeddings-ollama
```

### API (`requirements/api.txt`)
```
fastapi==0.111.*
uvicorn[standard]==0.29.*
pydantic==2.*
celery==5.*
redis==5.*
httpx==0.27.*
```

### MLOps (`requirements/mlops.txt`)
```
mlflow==2.*
dvc==3.*
prometheus-client==0.20.*
```

### Ingestion (`requirements/ingest.txt`)
```
grobid-client-python==0.8.*
requests==2.31.*
aiohttp==3.9.*
lxml==5.*
```

## Ollama Model Commands

```bash
ollama pull mistral                    # primary — 4.1GB
ollama pull llama3.1:8b               # fallback — 4.7GB
ollama pull nomic-embed-text          # embeddings — 274MB
ollama pull phi3:mini                 # ultra-fast, lower quality — 2.2GB

# During dev, only keep one large model loaded at a time
ollama rm llama3.1:8b                 # free VRAM if switching
```

## WSL2-Specific Notes

- CUDA works in WSL2 via NVIDIA's Windows driver (no separate Linux driver needed)
- Run `nvidia-smi` in WSL2 to confirm GPU visibility
- Docker Desktop WSL2 backend shares the same CUDA access
- Ollama installed natively in WSL2 (not in Docker) for best GPU performance
- Port forwarding: WSL2 ports are auto-forwarded to Windows localhost
- File I/O: keep all project files in WSL2 filesystem (`/home/`) not `/mnt/c/` — massive speed difference for Docker volumes
