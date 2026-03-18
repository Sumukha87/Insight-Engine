# Insight-Engine Pipeline — Full Explanation

## What We Are Building

Insight-Engine ingests scientific papers, extracts knowledge from them, and loads that
knowledge into a graph database (Neo4j). The graph is then queried to find cross-domain
innovation connections that no keyword search can find.

The core thesis: a battery-longevity breakthrough in aerospace may directly solve an
unsolved problem in cardiology — but no one ever makes the connection. Insight-Engine
is the matchmaker.

---

## The Full Pipeline

```
arXiv papers (229,498 docs)
        ↓  fetch_arxiv
Raw JSONL  data/raw/arxiv/{domain}/batch_*.jsonl
        ↓  ner
Entities   data/processed/entities/{domain}/entities.jsonl   (10,779,699 entity mentions)
        ↓  relation_extractor
Relations  data/processed/relations/{domain}/relations.jsonl (~2.3M relation pairs)
        ↓  graph_loader
Neo4j      Entity nodes + Paper nodes + RELATES_TO edges
```

Every stage is tracked by DVC (`dvc.yaml`) and every run is logged to MLflow
(`insight-engine-nlp` experiment at http://localhost:5000).

---

## Stage 1 — fetch_arxiv

**Script:** `src/ingestion/arxiv_fetcher.py`

**What it does:**
Calls the arXiv API with domain-specific search queries. Fetches paper metadata
(title, abstract, authors, categories, published date) and writes it to JSONL files.

**12 domains covered:**
Aerospace, Medical Devices, Materials, Energy, Biotechnology, Robotics,
Quantum, Nanotechnology, Environment, Semiconductors, Pharma, Neuroscience

**Key behaviour:**
- Deduplicates on `arxiv_id` — re-running never downloads the same paper twice
- New papers land in new batch files — DVC detects the change and marks downstream stages stale
- Rate-limited to 3 seconds between requests (arXiv API requirement)

**Output format (one JSON per line):**
```json
{
  "arxiv_id": "2401.12345v1",
  "title": "Titanium alloy coatings for cardiac implants",
  "abstract": "...",
  "authors": ["Smith J", "Lee K"],
  "categories": ["cond-mat.mtrl-sci"],
  "published": "2024-01-15",
  "source": "arxiv"
}
```

---

## Stage 2 — NER (Named Entity Recognition)

**Script:** `src/nlp/ner_pipeline.py`
**Model:** `en_core_sci_lg` (SciSpacy large biomedical model)

**What it does:**
Runs spaCy NER on every paper's title + abstract. Extracts named entities and maps
them to one of 12 canonical entity types. Writes one output JSONL per domain.

**The 12 entity types and what they capture:**

| Type | What it represents | Example |
|---|---|---|
| `Technology` | Methods, platforms, systems | "CRISPR", "lithography" |
| `Material` | Substances, alloys, nanomaterials | "titanium alloy", "graphene" |
| `Disease` | Conditions, disorders, syndromes | "Alzheimer's", "arrhythmia" |
| `Device` | Instruments, implants, sensors | "pacemaker", "transistor" |
| `Compound` | Chemicals, drugs, molecules | "aspirin", "lithium oxide" |
| `Process` | Manufacturing steps, bio processes | "sputtering", "fermentation" |
| `Organism` | Bacteria, viruses, cell types | "E. coli", "T-cell" |
| `Gene` | Genes, proteins, biomarkers | "BRCA1", "tau protein" |
| `Algorithm` | ML models, optimizers | "transformer", "ResNet" |
| `Phenomenon` | Physical/chemical effects | "superconductivity", "entanglement" |
| `Software` | Frameworks, libraries, tools | "PyTorch", "CUDA", "OpenFOAM" |
| `Infrastructure` | Large-scale systems, facilities | "reactor", "wind farm", "power grid" |

**Output format (one JSON per line):**
```json
{
  "doc_id": "arxiv_2401.12345v1",
  "domain": "materials",
  "entities": [
    {"text": "titanium alloy", "type": "Material", "start": 0, "end": 14, "domain": "materials"},
    {"text": "bone implant",   "type": "Device",   "start": 28, "end": 40, "domain": "materials"}
  ]
}
```

**Key numbers:**
- 229,498 documents processed
- 10,779,699 total entity mentions extracted
- 47 entities per document on average

---

## Stage 3 — Relation Extraction (v1 Rule-Based)

**Script:** `src/nlp/relation_extractor.py`

**What it does:**
Reads entity records. For each document, looks at every pair of entities and applies
type-pair rules to assign a relation type and confidence score. This is v1 — rules are
pre-configured based on entity types, not the actual sentence text.

### Why Relations Are Pre-Configured

Relations are not universal truth — they are **this product's knowledge model**.
The relations we configure are determined by the intelligence modules we need to power:

| Intelligence Module | Relations that power it |
|---|---|
| Cross-Pollination (The Matchmaker) | `COMPOSED_OF`, `USED_IN`, `IMPROVES`, `DERIVED_FROM` |
| Trend Velocity (Early Warning) | `IMPROVES`, `REPLACES` |
| Patent De-Risking (The Shield) | `DERIVED_FROM`, `SYNTHESIZED_FROM`, `COMPOSED_OF` |
| Gap Analysis (Opportunity Finder) | `TREATS`, `INHIBITS`, `CAUSES` |

### The 10 Relation Types

| Relation | Head Type | Tail Type | Confidence | Meaning |
|---|---|---|---|---|
| `TREATS` | Compound | Disease | 0.85 | Drug/compound addresses a disease |
| `TREATS` | Compound | Disease | 0.85 | (also via Device → Disease at 0.75) |
| `CAUSES` | Gene | Disease | 0.80 | Gene mutation produces a condition |
| `CAUSES` | Organism | Disease | 0.75 | Pathogen causes disease |
| `INHIBITS` | Compound | Gene | 0.80 | Drug suppresses gene expression |
| `INHIBITS` | Compound | Organism | 0.75 | Compound kills/suppresses organism |
| `COMPOSED_OF` | Material | Device | 0.80 | Material is the substrate of a device |
| `COMPOSED_OF` | Material | Infrastructure | 0.75 | Material makes up large-scale system |
| `DERIVED_FROM` | Material | Process | 0.75 | Material is output of a process |
| `SYNTHESIZED_FROM` | Process | Material | 0.80 | Process produces a material |
| `SYNTHESIZED_FROM` | Process | Compound | 0.75 | Process produces a compound |
| `IMPROVES` | Technology | Technology | 0.70 | One technology enhances another |
| `IMPROVES` | Algorithm | Algorithm | 0.70 | One algorithm improves another |
| `USED_IN` | Algorithm | Technology | 0.75 | Algorithm applied within a technology |
| `USED_IN` | Software | Technology | 0.75 | Software used to build a technology |
| `USED_IN` | Device | Process | 0.70 | Device is part of a process |
| `INTERACTS_WITH` | Compound | Compound | 0.70 | Two drugs interact |
| `INTERACTS_WITH` | Gene | Gene | 0.70 | Two genes interact |
| `REPLACES` | Device | Device | 0.65 | Newer device supersedes older one |

### How the Rule Lookup Works

```
Document has entities: [titanium alloy (Material), bone implant (Device)]
                                ↓
Lookup (Material, Device) in rule table
                                ↓
Match found: COMPOSED_OF, confidence 0.80
                                ↓
Emit: titanium alloy -[COMPOSED_OF 0.80]-> bone implant
```

### v1 Limitation

Relations are assigned by entity type co-occurrence in the same document — not by
what the sentence actually says. A paper saying "compound X does NOT treat disease Y"
would still emit a TREATS relation. This is acceptable for a first graph pass.

**v2 (future):** NLP sentence-level extraction using SciSpacy relation models or
Mistral 7B via Ollama to read the actual text between entities.

### Params (tunable via params.yaml)

```yaml
relations:
  confidence_threshold: 0.7   # rules below this score are dropped
  max_relations_per_doc: 10   # cap per document (prevents combinatorial explosion)
```

**Output format (one JSON per line):**
```json
{
  "doc_id": "arxiv_2401.12345v1",
  "domain": "materials",
  "relations": [
    {
      "head": "titanium alloy",
      "head_type": "Material",
      "tail": "bone implant",
      "tail_type": "Device",
      "relation": "COMPOSED_OF",
      "confidence": 0.8
    }
  ]
}
```

---

## Stage 4 — Graph Loader

**Script:** `src/graph/graph_loader.py`

**What it does:**
Streams entities and relations JSONL files into Neo4j in two passes. Uses `MERGE`
throughout — fully idempotent, safe to re-run.

**Pass 1 — Entity + Paper nodes:**
- Reads `data/processed/entities/`
- `MERGE (e:Entity {name, type})` — deduplicates 10.7M mentions into unique nodes
- `MERGE (p:Paper {doc_id})` — one node per paper

**Pass 2 — RELATES_TO edges:**
- Reads `data/processed/relations/`
- `MERGE (h)-[:RELATES_TO {relation, confidence, source_paper_id}]->(t)`

**Schema applied first (Neo4j Community Edition compatible):**
```cypher
CREATE CONSTRAINT entity_unique FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE
CREATE CONSTRAINT paper_unique  FOR (p:Paper)  REQUIRE p.doc_id IS UNIQUE
CREATE INDEX entity_domain FOR (e:Entity) ON (e.domain)
CREATE INDEX entity_type   FOR (e:Entity) ON (e.type)
```

> NOTE: Property existence constraints (IS NOT NULL) require Enterprise Edition.
> Only use uniqueness constraints and indexes with Community Edition.

**Params (tunable via params.yaml):**
```yaml
graph:
  entity_batch_size: 500    # nodes per Neo4j transaction
  relation_batch_size: 1000 # edges per Neo4j transaction
```

---

## What Exists in Neo4j After the Loader Runs

### Nodes
- `Entity` — unique (name, type) pairs. Properties: name, type, domain
- `Paper` — one per arXiv paper. Properties: doc_id, domain, source

### Edges
- `RELATES_TO` — between Entity nodes. Properties: relation, confidence, source_paper_id

### Example Queries

```cypher
// See what's in the graph
MATCH (e:Entity) RETURN e.type, count(e) ORDER BY count(e) DESC

// All TREATS relations
MATCH (c:Entity)-[r:RELATES_TO {relation:'TREATS'}]->(d:Entity)
RETURN c.name, d.name, r.confidence LIMIT 20

// The core value prop — cross-domain path discovery
MATCH path = (a:Entity {domain:'aerospace'})-[:RELATES_TO*1..3]-(b:Entity {domain:'medical_devices'})
RETURN path LIMIT 5
```

---

## MLflow Experiment Tracking

Every stage run logs to the `insight-engine-nlp` experiment at http://localhost:5000

| Run name | Stage | Key metrics logged |
|---|---|---|
| `ner_pipeline` | NER | entity_count, entities_per_doc per domain |
| `relation_extractor_v1` | Relations | relation_count, relations_per_doc per domain |
| `graph_loader_v1` | Graph | entity_nodes, paper_nodes, relates_to_edges |

Changing any value in `params.yaml` and re-running creates a new MLflow run, allowing
side-by-side comparison of how the change affected output quality.

---

## DVC Pipeline

```
fetch_arxiv → ner → relations → graph_loader
```

```bash
dvc dag          # visualise the pipeline
dvc status       # see what stages are stale
dvc repro        # re-run only stale stages
dvc metrics show # compare metrics across runs
dvc push         # push data to Google Drive
dvc pull         # restore data from Google Drive
```

DVC tracks: code deps, params, output directories, metrics files.
If any dep or param changes, the affected stage and all downstream stages are marked
stale and re-run on the next `dvc repro`.

---

## What Is Still Missing (Phase 2 Completion)

| Missing | Why needed |
|---|---|
| Vector embeddings via Qdrant | Semantic search — find entities by meaning |
| `embedding_id` property on Entity nodes | Links Neo4j node ↔ Qdrant vector |
| LlamaIndex GraphRAG layer | Answers natural language questions using graph paths |
| More data sources | PubMed, USPTO, ClinicalTrials.gov (richer cross-domain signal) |
| v2 Relation extraction | Sentence-level NLP instead of type-pair rules |
