# Cross-Domain Graph Query

Run a cross-domain path discovery query on Neo4j for the topic: **$ARGUMENTS**

## Steps

1. Connect to Neo4j at bolt://localhost:7687 (password: changeme_strong_password)

2. First, find entities matching the keyword:
```cypher
MATCH (e:Entity)
WHERE toLower(e.name) CONTAINS toLower($keyword)
RETURN e.name, e.type, e.domain, count(*) as mentions
ORDER BY mentions DESC LIMIT 10
```

3. If matches found, run cross-domain path discovery from the top match:
```cypher
MATCH path = (a:Entity)-[r:RELATES_TO*1..3]-(b:Entity)
WHERE a.name = $seed_entity AND a.domain <> b.domain
RETURN DISTINCT b.name, b.type, b.domain,
       [rel in relationships(path) | rel.relation] as relations,
       length(path) as hops
ORDER BY hops ASC
LIMIT 20
```

4. Present results:
   - Which domains the topic connects to
   - The shortest cross-domain paths found
   - The relation chain (e.g., IMPROVES → USED_IN → COMPOSED_OF)

5. If no matches, suggest alternative keywords.

Always use parameterized queries — never string interpolation.
