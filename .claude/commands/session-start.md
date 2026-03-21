# Session Start Checklist

Run this at the beginning of every work session.

## Step 1 — Read Progress
Read `.claude/docs/progress.md` — identify current phase, open blockers, and key numbers.

## Step 2 — Check Services
Run `docker ps --format "table {{.Names}}\t{{.Status}}"` to verify all containers are running.
Expected: ie-neo4j, ie-qdrant, ie-mlflow, ie-grobid, ie-redis, ie-prometheus, ie-grafana, ollama.

## Step 3 — Check Pipeline
Run `dvc status` to see if any pipeline stages are stale.

## Step 4 — Git State
Run `git status` and `git log --oneline -5`.

## Step 5 — Recommend Next Steps
Based on progress.md, identify the next 2–3 tasks in priority order with the specific commands or files involved.

Present a summary:
```
═══════════════════════════
Phase: [current phase]
Branch: [current branch]
Services: [X/8 healthy]
Pipeline: [stale/up-to-date]

Next Steps:
1. [highest priority]
2. [second task]
3. [third task]

Blockers: [open blockers]
═══════════════════════════
```
