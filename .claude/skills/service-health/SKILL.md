---
name: service-health
description: Check health of all Docker services and local tools (Neo4j, Qdrant, Ollama, MLflow, etc.)
---

# Service Health Check

Check ALL services. Run these checks in parallel:

## Docker Services
Run `docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"` to list all containers.

Expected containers:
- ie-neo4j (ports 7474, 7687)
- ie-qdrant (ports 6333, 6334)
- ie-mlflow (port 5000)
- ie-grobid (port 8070)
- ie-redis (port 6379)
- ie-prometheus (port 9090)
- ie-grafana (port 3001)
- ollama (port 11434)

## API Health Checks
Run these curl commands in parallel:
- `curl -s http://localhost:6333/healthz` (Qdrant)
- `curl -s http://localhost:11434/api/tags` (Ollama — check which models are pulled)
- `curl -s http://localhost:5000/health` (MLflow)
- `curl -s http://localhost:7474` (Neo4j browser)

## GPU Status
Run `nvidia-smi` to check GPU visibility and VRAM usage.

## Summary
Present results in a table:

| Service | Status | Port | Notes |
|---------|--------|------|-------|

Flag any services that are down with instructions to fix (usually `docker compose up -d`).
