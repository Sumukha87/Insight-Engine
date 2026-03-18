"""
Graph Loader — loads NLP pipeline output into Neo4j.

Two-pass loading:
  Pass 1 (entities):  Entity nodes + Paper nodes
  Pass 2 (relations): RELATES_TO edges between entities

All writes use MERGE — fully idempotent, safe to re-run.

Usage:
    python -m src.graph.graph_loader
"""

import json
import logging
import os
from pathlib import Path

import mlflow
import yaml
from neo4j import GraphDatabase
from neo4j import Driver

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ENTITIES_DIR = Path("data/processed/entities")
RELATIONS_DIR = Path("data/processed/relations")
METRICS_DIR = Path("metrics")

# Load params
_params = yaml.safe_load(Path("params.yaml").read_text())["graph"]
ENTITY_BATCH_SIZE: int = _params["entity_batch_size"]
RELATION_BATCH_SIZE: int = _params["relation_batch_size"]

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_EXPERIMENT = "insight-engine-nlp"

# ---------------------------------------------------------------------------
# Schema setup
# ---------------------------------------------------------------------------

SCHEMA_QUERIES = [
    # Uniqueness constraints (Community Edition supported)
    "CREATE CONSTRAINT entity_unique IF NOT EXISTS FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE",
    "CREATE CONSTRAINT paper_unique IF NOT EXISTS FOR (p:Paper) REQUIRE p.doc_id IS UNIQUE",
    # Indexes for fast traversal
    "CREATE INDEX entity_domain IF NOT EXISTS FOR (e:Entity) ON (e.domain)",
    "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
]


def apply_schema(driver: Driver) -> None:
    """Apply constraints and indexes to Neo4j. Safe to run multiple times."""
    with driver.session() as session:
        for query in SCHEMA_QUERIES:
            session.run(query)
            logger.info(f"Schema: {query[:60]}...")
    logger.info("Schema applied.")


# ---------------------------------------------------------------------------
# Pass 1 — Entity nodes + Paper nodes
# ---------------------------------------------------------------------------

MERGE_ENTITIES_QUERY = """
UNWIND $batch AS row
MERGE (e:Entity {name: row.name, type: row.type})
ON CREATE SET e.domain = row.domain
"""

MERGE_PAPERS_QUERY = """
UNWIND $batch AS row
MERGE (p:Paper {doc_id: row.doc_id})
ON CREATE SET p.domain = row.domain, p.source = 'arxiv'
"""


def load_entities_and_papers(driver: Driver) -> dict:
    """
    Stream entities JSONL → MERGE Entity nodes and Paper nodes into Neo4j.
    Returns metrics dict.
    """
    domain_files = sorted(ENTITIES_DIR.glob("*/entities.jsonl"))
    if not domain_files:
        raise FileNotFoundError(f"No entity files found in {ENTITIES_DIR}")

    entity_batch: list[dict] = []
    paper_batch: list[dict] = []
    seen_papers: set[str] = set()

    total_entity_merges = 0
    total_paper_merges = 0

    def flush_entities(session) -> int:
        if not entity_batch:
            return 0
        session.run(MERGE_ENTITIES_QUERY, batch=entity_batch)
        count = len(entity_batch)
        entity_batch.clear()
        return count

    def flush_papers(session) -> int:
        if not paper_batch:
            return 0
        session.run(MERGE_PAPERS_QUERY, batch=paper_batch)
        count = len(paper_batch)
        paper_batch.clear()
        return count

    with driver.session() as session:
        for domain_file in domain_files:
            domain = domain_file.parent.name
            file_entity_count = 0

            with open(domain_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    doc_id = record["doc_id"]

                    # Queue paper node (once per doc)
                    if doc_id not in seen_papers:
                        seen_papers.add(doc_id)
                        paper_batch.append({"doc_id": doc_id, "domain": domain})
                        if len(paper_batch) >= ENTITY_BATCH_SIZE:
                            total_paper_merges += flush_papers(session)

                    # Queue entity nodes
                    for ent in record.get("entities", []):
                        entity_batch.append({
                            "name": ent["text"],
                            "type": ent["type"],
                            "domain": domain,
                        })
                        file_entity_count += 1
                        if len(entity_batch) >= ENTITY_BATCH_SIZE:
                            total_entity_merges += flush_entities(session)

            # Flush remaining for this domain
            total_entity_merges += flush_entities(session)
            total_paper_merges += flush_papers(session)
            logger.info(f"[{domain}] Entity pass done — {file_entity_count} entity records processed")

    logger.info(f"Pass 1 complete — {total_entity_merges} entity MERGEs, {total_paper_merges} paper MERGEs")
    return {
        "entity_merges": total_entity_merges,
        "paper_merges": total_paper_merges,
    }


# ---------------------------------------------------------------------------
# Pass 2 — RELATES_TO edges
# ---------------------------------------------------------------------------

MERGE_RELATIONS_QUERY = """
UNWIND $batch AS row
MATCH (h:Entity {name: row.head, type: row.head_type})
MATCH (t:Entity {name: row.tail, type: row.tail_type})
MERGE (h)-[r:RELATES_TO {relation: row.relation}]->(t)
ON CREATE SET r.confidence = row.confidence, r.source_paper_id = row.doc_id
"""


def load_relations(driver: Driver) -> dict:
    """
    Stream relations JSONL → MERGE RELATES_TO edges into Neo4j.
    Returns metrics dict.
    """
    domain_files = sorted(RELATIONS_DIR.glob("*/relations.jsonl"))
    if not domain_files:
        raise FileNotFoundError(f"No relation files found in {RELATIONS_DIR}")

    batch: list[dict] = []
    total_relation_merges = 0
    total_skipped = 0

    def flush(session) -> int:
        if not batch:
            return 0
        session.run(MERGE_RELATIONS_QUERY, batch=batch)
        count = len(batch)
        batch.clear()
        return count

    with driver.session() as session:
        for domain_file in domain_files:
            domain = domain_file.parent.name
            file_relation_count = 0

            with open(domain_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    doc_id = record["doc_id"]

                    for rel in record.get("relations", []):
                        batch.append({
                            "head": rel["head"],
                            "head_type": rel["head_type"],
                            "tail": rel["tail"],
                            "tail_type": rel["tail_type"],
                            "relation": rel["relation"],
                            "confidence": rel["confidence"],
                            "doc_id": doc_id,
                        })
                        file_relation_count += 1
                        if len(batch) >= RELATION_BATCH_SIZE:
                            total_relation_merges += flush(session)

            total_relation_merges += flush(session)
            logger.info(f"[{domain}] Relations pass done — {file_relation_count} relation records processed")

    logger.info(f"Pass 2 complete — {total_relation_merges} RELATES_TO MERGEs")
    return {"relation_merges": total_relation_merges}


# ---------------------------------------------------------------------------
# Graph stats query — what landed in Neo4j
# ---------------------------------------------------------------------------

def get_graph_stats(driver: Driver) -> dict:
    """Query Neo4j for final node/edge counts."""
    with driver.session() as session:
        entity_count = session.run("MATCH (e:Entity) RETURN count(e) AS c").single()["c"]
        paper_count = session.run("MATCH (p:Paper) RETURN count(p) AS c").single()["c"]
        relation_count = session.run("MATCH ()-[r:RELATES_TO]->() RETURN count(r) AS c").single()["c"]
        domain_counts = session.run(
            "MATCH (e:Entity) RETURN e.domain AS domain, count(e) AS c ORDER BY c DESC"
        ).data()
    return {
        "entity_nodes": entity_count,
        "paper_nodes": paper_count,
        "relates_to_edges": relation_count,
        "domains": {row["domain"]: row["c"] for row in domain_counts},
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Connecting to Neo4j at {NEO4J_URI}")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    logger.info("Neo4j connection verified.")

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)

    with mlflow.start_run(
        run_name="graph_loader_v1",
        tags={"stage": "graph", "target": "neo4j", "source": "arxiv"},
    ):
        mlflow.log_param("entity_batch_size", ENTITY_BATCH_SIZE)
        mlflow.log_param("relation_batch_size", RELATION_BATCH_SIZE)
        mlflow.log_param("neo4j_uri", NEO4J_URI)

        # Step 1 — schema
        logger.info("=== Step 1: Applying schema ===")
        apply_schema(driver)

        # Step 2 — entity + paper nodes
        logger.info("=== Step 2: Loading entities and papers ===")
        entity_metrics = load_entities_and_papers(driver)

        # Step 3 — relation edges
        logger.info("=== Step 3: Loading relations ===")
        relation_metrics = load_relations(driver)

        # Step 4 — final counts from Neo4j
        logger.info("=== Step 4: Querying graph stats ===")
        stats = get_graph_stats(driver)

        # Log to MLflow
        mlflow.log_metric("entity_nodes", stats["entity_nodes"])
        mlflow.log_metric("paper_nodes", stats["paper_nodes"])
        mlflow.log_metric("relates_to_edges", stats["relates_to_edges"])
        mlflow.log_metric("entity_merges_total", entity_metrics["entity_merges"])
        mlflow.log_metric("relation_merges_total", relation_metrics["relation_merges"])

        logger.info(
            f"GRAPH STATS — {stats['entity_nodes']:,} entity nodes | "
            f"{stats['paper_nodes']:,} paper nodes | "
            f"{stats['relates_to_edges']:,} RELATES_TO edges"
        )

        # Write DVC metrics
        metrics_out = {**stats, **entity_metrics, **relation_metrics}
        with open(METRICS_DIR / "graph_metrics.json", "w") as f:
            json.dump(metrics_out, f, indent=2)

    driver.close()
    logger.info("Done.")


if __name__ == "__main__":
    main()
