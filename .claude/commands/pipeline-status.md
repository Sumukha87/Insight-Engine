# Pipeline Status Check

Check the full pipeline status across all 6 stages. Run these in parallel where possible:

## Stage 1–4 (DVC managed)
- Run `dvc status` to see which stages are stale
- Run `dvc metrics show` to show current metrics from metrics/*.json

## Stage 4 — Graph (Neo4j)
Run this via Python to get graph stats:
```python
from neo4j import GraphDatabase
import os
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", os.getenv("NEO4J_PASSWORD", "changeme_strong_password")))
with driver.session() as s:
    entities = s.run("MATCH (e:Entity) RETURN count(e) AS c").single()["c"]
    papers = s.run("MATCH (p:Paper) RETURN count(p) AS c").single()["c"]
    edges = s.run("MATCH ()-[r:RELATES_TO]->() RETURN count(r) AS c").single()["c"]
    embedded = s.run("MATCH (e:Entity) WHERE e.embedding_id IS NOT NULL RETURN count(e) AS c").single()["c"]
    print(f"Entity nodes: {entities:,}")
    print(f"Paper nodes: {papers:,}")
    print(f"RELATES_TO edges: {edges:,}")
    print(f"Entities with embedding_id: {embedded:,} / {entities:,} ({embedded/entities*100:.1f}%)")
driver.close()
```

## Stage 5 — Embeddings (Qdrant)
Run `curl -s http://localhost:6333/collections/entities` and report vector count.

## Stage 6 — GraphRAG Query Engine
Check if `src/graph/graphrag_query.py` exists. Report whether it's built or not.

## Summary
Present all findings in a single table:

| Stage | Component | Status | Key Numbers |
|-------|-----------|--------|-------------|
| 1 | arXiv Ingestion | | |
| 2 | NER | | |
| 3 | Relation Extraction | | |
| 4 | Graph Loading | | |
| 5 | Embedding Pipeline | | |
| 6 | GraphRAG Query | | |

Compare against the numbers in .claude/docs/progress.md and flag any discrepancies.
