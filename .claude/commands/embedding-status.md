# Embedding Pipeline Status

Check embedding progress across Neo4j and Qdrant.

## Neo4j — Entity counts
```python
from neo4j import GraphDatabase
import os
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", os.getenv("NEO4J_PASSWORD", "changeme_strong_password")))
with driver.session() as s:
    total = s.run("MATCH (e:Entity) RETURN count(e) AS c").single()["c"]
    embedded = s.run("MATCH (e:Entity) WHERE e.embedding_id IS NOT NULL RETURN count(e) AS c").single()["c"]
    by_domain = s.run("""
        MATCH (e:Entity)
        WITH e.domain AS domain, count(e) AS total,
             count(CASE WHEN e.embedding_id IS NOT NULL THEN 1 END) AS embedded
        RETURN domain, total, embedded, total - embedded AS remaining
        ORDER BY remaining DESC
    """).data()
    print(f"Total: {total:,} | Embedded: {embedded:,} ({embedded/total*100:.1f}%) | Remaining: {total-embedded:,}")
    for row in by_domain:
        print(f"  {row['domain']}: {row['embedded']:,}/{row['total']:,} ({row['remaining']:,} remaining)")
driver.close()
```

## Qdrant — Vector count
`curl -s http://localhost:6333/collections/entities`

## Report
```
Embedding Progress
══════════════════
Total entities:  X
Embedded:        Y (Z%)
Remaining:       W
Qdrant vectors:  V

Per Domain:
| Domain | Total | Embedded | Remaining |
```

If remaining > 0: `set -a && source .env && set +a && source .venv/bin/activate && python -m src.graph.embedding_pipeline`
