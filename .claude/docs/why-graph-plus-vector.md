# Why Graph DB + Vector DB (Not Vector Alone)

## What Pure Vector Search Gives You

You embed every entity, you query, you get back the most semantically similar entities. That's it.

```
Query: "aerospace materials for cardiac implants"
         │
         ▼
Qdrant returns top-10 similar entities:
  - titanium alloy (Aerospace)
  - carbon fiber (Aerospace)
  - nitinol (Materials)
  - stent coating (Medical)
```

These are **individually relevant** results. But you have no idea *how* they connect, *why* they're related, or *what the path between domains looks like*.

---

## The Fundamental Limit of Vector Search

Vectors capture **semantic similarity** — things that sound alike, appear in similar contexts, use similar words.

They cannot capture **structural relationships** — A leads to B which enables C which solves D.

```
titanium alloy  ──IMPROVES──►  fatigue resistance
                                      │
                              USED_IN─┘
                                      │
                                      ▼
                              cardiac valve  ──TREATS──►  aortic stenosis
```

This 3-hop chain is **invisible to Qdrant**. Titanium alloy and aortic stenosis are not semantically similar — they appear in completely different papers, different vocabularies, different fields. Their vectors are far apart. Qdrant will never surface this connection.

But it's exactly the kind of connection Insight-Engine is supposed to find.

---

## This Is the Whole Product Thesis

Standard vector RAG (what every other tool does) finds things that are **already known to be related** — because they co-occur in text.

Graph traversal finds things that are **structurally connected through chains of evidence** that no single document ever put together.

> "We don't find what's similar. We find what's connected."

---

## Concrete Example

A battery longevity breakthrough in aerospace (new electrolyte compound) is described in 40 arXiv papers. Cardiac pacemaker battery life is described in 60 different papers. Zero overlap in vocabulary, authors, or citations.

- **Vector search:** returns aerospace papers for aerospace queries, cardiac papers for cardiac queries. Never connects them.
- **Graph traversal:** `electrolyte compound → IMPROVES → energy density → USED_IN → implantable device → RELATES_TO → pacemaker`. Finds the connection.

---

## How Neo4j and Qdrant Work Together

They serve different purposes and neither can do the job alone.

When a user asks *"aerospace materials for cardiac implants"* you need to:

1. Find the **right starting nodes** in the graph (semantic match, not exact string match) — **Qdrant's job**
2. **Traverse the graph** to find cross-domain paths — **Neo4j's job**

### The Linking Key: `embedding_id`

Every Entity node in Neo4j has an `embedding_id` property — the Qdrant point ID for that entity's vector. It's the bridge between the two databases.

```
Neo4j Entity node                    Qdrant point
─────────────────────                ────────────────────────────
name: "titanium alloy"               id: "abc-123"
type: Material          ◄──────────► vector: [0.12, -0.34, ...]
domain: Aerospace                    payload: {name, type, domain}
embedding_id: "abc-123"
```

### The Full Query Flow

```
User: "aerospace materials for cardiac implants"
         │
         ▼
1. NER on query text
   → extracts ["aerospace materials", "cardiac implants"]
         │
         ▼
2. Embed query with nomic-embed-text
   → query vector [0.21, -0.11, ...]
         │
         ▼
3. Qdrant ANN search (approximate nearest neighbors)
   → returns top-10 most semantically similar entity IDs
   → e.g., ["titanium alloy", "carbon fiber", "nitinol"]
         │
         ▼
4. Look up those Entity nodes in Neo4j
   MATCH (e:Entity) WHERE e.embedding_id IN $ids
         │
         ▼
5. Neo4j graph traversal from those seed nodes
   MATCH path = (seed)-[RELATES_TO*1..4]-(target {domain:'Medical'})
         │
         ▼
6. Return subgraph context (paths + source papers)
         │
         ▼
7. Feed paths into Mistral via Ollama → synthesized answer with citations
```

---

## Why You Need Both — Summary Table

| Task | Neo4j alone | Qdrant alone | Both |
|------|-------------|--------------|------|
| Find "titanium alloy" when user types "lightweight biocompatible metal" | ❌ exact string match only | ✅ semantic similarity | ✅ |
| Find 4-hop path Aerospace → Material → Process → Medical | ✅ graph traversal | ❌ no concept of relationships | ✅ |
| Cross-domain discovery across siloed fields | ✅ once seeded correctly | ❌ flat similarity, no graph structure | ✅ |
| Surface connections no single paper ever made | ❌ | ❌ | ✅ |

**Qdrant gets you to the right door. Neo4j takes you through it and finds the connections.**
