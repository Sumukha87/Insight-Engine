---
name: embedding-status
description: Check the progress of the embedding pipeline — how many entities are embedded in Qdrant vs total in Neo4j
---

# Embedding Pipeline Status

Check the embedding pipeline progress by querying both databases.

## Neo4j — Entity counts
Run via Python:
```python
from neo4j import GraphDatabase
import os
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", os.getenv("NEO4J_PASSWORD", "changeme_strong_password")))
with driver.session() as s:
    total = s.run("MATCH (e:Entity) RETURN count(e) AS c").single()["c"]
    embedded = s.run("MATCH (e:Entity) WHERE e.embedding_id IS NOT NULL RETURN count(e) AS c").single()["c"]
    remaining = total - embedded
    pct = (embedded / total * 100) if total > 0 else 0
    by_domain = s.run("""
        MATCH (e:Entity)
        WITH e.domain AS domain, count(e) AS total,
             count(CASE WHEN e.embedding_id IS NOT NULL THEN 1 END) AS embedded
        RETURN domain, total, embedded, total - embedded AS remaining
        ORDER BY remaining DESC
    """).data()
driver.close()
```

## Qdrant — Vector counts
Run `curl -s http://localhost:6333/collections/entities | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d.get('result',{}).get('points_count', 'N/A')))"` to get Qdrant point count.

## Report
Present as:

```
Embedding Progress
══════════════════
Total entities:    X
Embedded:          Y (Z%)
Remaining:         W
Qdrant vectors:    V

Per Domain:
| Domain | Total | Embedded | Remaining |
|--------|-------|----------|-----------|
```

If remaining > 0, remind to run: `python -m src.graph.embedding_pipeline`
