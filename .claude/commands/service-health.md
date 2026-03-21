# Service Health Check

Check ALL services. Run checks in parallel.

## Docker Services
Run `docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"`.

Expected containers:
- ie-neo4j (7474, 7687)
- ie-qdrant (6333, 6334)
- ie-mlflow (5000)
- ie-grobid (8070)
- ie-redis (6379)
- ie-prometheus (9090)
- ie-grafana (3001)
- ollama (11434)

## API Health Checks
- `curl -s http://localhost:6333/healthz` (Qdrant)
- `curl -s http://localhost:11434/api/tags` (Ollama — list loaded models)
- `curl -s http://localhost:5000/health` (MLflow)

## Airflow
Check if Airflow is running: `curl -s http://localhost:8080/health 2>/dev/null || echo "Airflow not running — start with: bash scripts/start_airflow.sh"`

## GPU
Run `nvidia-smi` — confirm RTX 4060 visible, check VRAM usage.

## Summary Table

| Service | Status | Port | Notes |
|---------|--------|------|-------|

Flag anything down with the fix command.
