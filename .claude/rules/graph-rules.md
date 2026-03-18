# Graph & Neo4j Rules

## Cypher Conventions

- ALWAYS use parameters, never string interpolation:
  ```python
  # WRONG
  session.run(f"MATCH (n:Entity {{name: '{name}'}}) RETURN n")
  # RIGHT
  session.run("MATCH (n:Entity {name: $name}) RETURN n", name=name)
  ```
- Use `MERGE` not `CREATE` for all entity nodes to prevent duplicates
- Always set index on `Entity.name` and `Entity.domain` before loading data
- Use `CALL apoc.periodic.iterate` for bulk loads (>10K nodes at once)
- All relationships must include `source_paper_id` and `confidence` properties

## Required Indexes (apply on fresh Neo4j)

```cypher
-- NOTE: Property existence (IS NOT NULL) requires Enterprise Edition — do NOT use.
-- Use uniqueness constraints only (Community Edition supported).

CREATE CONSTRAINT entity_unique IF NOT EXISTS
  FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE;

CREATE CONSTRAINT paper_unique IF NOT EXISTS
  FOR (p:Paper) REQUIRE p.doc_id IS UNIQUE;

CREATE INDEX entity_domain IF NOT EXISTS
  FOR (e:Entity) ON (e.domain);

CREATE INDEX entity_type IF NOT EXISTS
  FOR (e:Entity) ON (e.type);

CREATE INDEX paper_doi IF NOT EXISTS
  FOR (p:Paper) ON (p.doi);
```

## Python Driver Pattern

```python
from neo4j import AsyncGraphDatabase

driver = AsyncGraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", os.getenv("NEO4J_PASSWORD"))
)

async with driver.session() as session:
    result = await session.run(query, **params)
    records = await result.data()
```

Always use `async` driver in FastAPI context.

## LlamaIndex Integration

```python
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.core import KnowledgeGraphIndex, StorageContext

graph_store = Neo4jGraphStore(
    username="neo4j",
    password=os.getenv("NEO4J_PASSWORD"),
    url="bolt://localhost:7687",
    database="neo4j"
)
storage_context = StorageContext.from_defaults(graph_store=graph_store)
```
