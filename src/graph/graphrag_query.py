"""
GraphRAG Query Engine — natural language query → cross-domain graph answer.

Flow:
  1. Embed the query via nomic-embed-text (Ollama)
  2. Qdrant ANN search → top K seed entities (by vector similarity)
  3. Neo4j graph traversal from each seed → cross-domain RELATES_TO paths (1–3 hops)
  4. Assemble subgraph context (entity names, relation types, domains)
  5. Mistral 7B synthesis (Ollama) → answer with cross-domain citations

Usage:
    python -m src.graph.graphrag_query --query "aerospace materials for cardiac implants"
    python -m src.graph.graphrag_query --query "battery tech from drones for pacemakers" --top-k 5

Output:
    Prints the answer + graph paths found.
    Also importable: from src.graph.graphrag_query import run_query
"""

import argparse
import json
import logging
import os
import time
from dataclasses import asdict, dataclass

import requests
from neo4j import Driver, GraphDatabase
from qdrant_client import QdrantClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]  # required — no default, fail fast if unset
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "mistral:v0.3"
COLLECTION_NAME = "entities"

DEFAULT_TOP_K = 5       # seed entities from Qdrant
DEFAULT_MAX_PATHS = 20  # max paths sent to Mistral per seed


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class GraphPath:
    nodes: list[dict]          # [{"name": ..., "type": ..., "domain": ...}, ...]
    relations: list[str]       # ["TREATS", "IMPROVES", ...]
    hops: int
    source_paper_ids: list[str] = None  # doc_ids from RELATES_TO edge properties


@dataclass
class SourceCitation:
    doc_id: str
    title: str
    year: int
    doi: str | None
    domain: str | None


@dataclass
class QueryResult:
    query: str
    answer: str
    paths: list[GraphPath]
    seed_entities: list[str]
    sources: list[SourceCitation]
    confidence: float
    latency_ms: int


# ---------------------------------------------------------------------------
# Step 1 — embed the query
# ---------------------------------------------------------------------------


def embed_query(query: str) -> list[float]:
    """Embed a single query string via nomic-embed-text."""
    response = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": [query]},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["embeddings"][0]


# ---------------------------------------------------------------------------
# Step 2 — Qdrant ANN search → seed entities
# ---------------------------------------------------------------------------


def find_seed_entities(
    qdrant: QdrantClient,
    query_vector: list[float],
    top_k: int,
) -> list[dict]:
    """
    Search Qdrant for entities most similar to the query vector.

    Filters to only entities with has_edges=True in Qdrant payload — these
    are entities that have at least one RELATES_TO edge in Neo4j and can
    actually yield graph paths. The flag was pre-computed by the setup step
    and stored in Qdrant, so this filter adds zero latency.
    """
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    hits = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
        query_filter=Filter(
            must=[FieldCondition(key="has_edges", match=MatchValue(value=True))]
        ),
    )

    return [
        {
            "embedding_id": hit.id,
            "name": hit.payload.get("name", ""),
            "type": hit.payload.get("type", ""),
            "domain": hit.payload.get("domain", ""),
            "score": round(hit.score, 4),
        }
        for hit in hits
    ]


# ---------------------------------------------------------------------------
# Step 3 — Neo4j graph traversal → cross-domain paths
# ---------------------------------------------------------------------------


def traverse_graph(driver: Driver, seed: dict, max_paths: int) -> list[GraphPath]:
    """
    From a seed entity, find paths that cross domain boundaries.
    Uses RELATES_TO edges, 1–3 hops.

    Cross-domain is detected by domain diversity across path nodes — NOT just
    start vs end — because entity domain is set to the first paper that loaded
    it (first-write-wins), so a single entity may connect to entities from
    many domains even if its own domain label doesn't reflect that.
    """
    with driver.session() as session:
        records = session.run(
            """
            MATCH (seed:Entity {embedding_id: $seed_id})
            MATCH path = (seed)-[:RELATES_TO*1..3]-(target:Entity)
            WITH path,
                 [n IN nodes(path) | {name: n.name, type: n.type, domain: n.domain}] AS path_nodes,
                 [r IN relationships(path) | coalesce(r.relation, 'RELATES_TO')]     AS relations,
                 [r IN relationships(path) | r.source_paper_id]                      AS source_paper_ids,
                 length(path) AS hops,
                 head(nodes(path)).domain AS seed_domain
            WHERE ANY(n IN tail(nodes(path)) WHERE n.domain <> seed_domain)
            RETURN path_nodes, relations, source_paper_ids, hops
            ORDER BY hops ASC
            LIMIT $limit
            """,
            seed_id=seed["embedding_id"],
            limit=max_paths,
        ).data()

    paths = []
    for rec in records:
        raw_ids = rec.get("source_paper_ids") or []
        paper_ids = [pid for pid in raw_ids if pid]
        paths.append(GraphPath(
            nodes=rec["path_nodes"],
            relations=rec["relations"],
            hops=rec["hops"],
            source_paper_ids=paper_ids,
        ))
    return paths


# ---------------------------------------------------------------------------
# Step 3b — look up source papers for citations
# ---------------------------------------------------------------------------


def fetch_citations(driver: Driver, doc_ids: list[str]) -> list[SourceCitation]:
    """Look up Paper nodes by doc_id and return citation metadata."""
    if not doc_ids:
        return []
    with driver.session() as session:
        records = session.run(
            """
            UNWIND $doc_ids AS doc_id
            MATCH (p:Paper {doc_id: doc_id})
            RETURN p.doc_id AS doc_id, p.title AS title,
                   coalesce(p.year, 0) AS year, p.doi AS doi, p.domain AS domain
            """,
            doc_ids=doc_ids,
        ).data()
    return [
        SourceCitation(
            doc_id=rec["doc_id"],
            title=rec["title"] or rec["doc_id"],
            year=rec["year"] or 0,
            doi=rec.get("doi"),
            domain=rec.get("domain"),
        )
        for rec in records
    ]


# ---------------------------------------------------------------------------
# Step 4 — format paths as readable context for Mistral
# ---------------------------------------------------------------------------


def format_paths_for_prompt(paths: list[GraphPath], seed_entities: list[dict]) -> str:
    """Render graph paths as plain text the LLM can reason over."""
    if not paths:
        return "No cross-domain connections found in the knowledge graph."

    lines = []
    for i, path in enumerate(paths, 1):
        nodes = path.nodes
        relations = path.relations

        # Build readable chain: Entity [Type, Domain] --RELATION--> Entity [Type, Domain]
        chain_parts = [f'{nodes[0]["name"]} [{nodes[0]["type"]}, {nodes[0]["domain"]}]']
        for j, rel in enumerate(relations):
            next_node = nodes[j + 1]
            chain_parts.append(f"--{rel}-->")
            chain_parts.append(f'{next_node["name"]} [{next_node["type"]}, {next_node["domain"]}]')

        chain = "  ".join(chain_parts)
        lines.append(f"PATH {i} ({path.hops} hop{'s' if path.hops > 1 else ''}):\n  {chain}")

    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Step 5 — call Mistral
# ---------------------------------------------------------------------------


def call_mistral(query: str, paths_text: str) -> str:
    """Send graph context + query to Mistral, return synthesized answer."""
    prompt = f"""You are an expert scientific analyst specializing in cross-domain innovation discovery.

A researcher asked: "{query}"

I searched a knowledge graph of 1.5 million scientific entities across 12 research domains \
(Aerospace, Medical, Materials, Energy, Biotechnology, Robotics, Quantum, Nanotechnology, \
Environment, Semiconductors, Pharma, Neuroscience) and found these cross-domain connections:

{paths_text}

Based on the graph evidence above, provide a concise answer that:
1. Identifies the key cross-domain connections found
2. Explains how technology or knowledge from one domain could apply to another
3. Highlights the most promising connection and why it matters

Be specific — reference the entity names and domains from the evidence. \
If the evidence is weak or off-topic, say so honestly.
Keep your answer under 300 words."""

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=180,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


# ---------------------------------------------------------------------------
# Confidence heuristic
# ---------------------------------------------------------------------------


def compute_confidence(paths: list[GraphPath]) -> float:
    """Simple heuristic: more short paths = higher confidence."""
    if not paths:
        return 0.0
    short = sum(1 for p in paths if p.hops <= 2)
    score = min(1.0, (short * 0.2) + (len(paths) * 0.05))
    return round(score, 2)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_query(query: str, top_k: int = DEFAULT_TOP_K, max_paths: int = DEFAULT_MAX_PATHS) -> QueryResult:
    """
    Full GraphRAG pipeline: query → answer.
    Importable for use in the FastAPI backend.
    """
    start = time.time()

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    qdrant = QdrantClient(url=QDRANT_URL)

    try:
        # Step 1 — embed query
        logger.info("Embedding query...")
        query_vector = embed_query(query)

        # Step 2 — find seed entities (pre-filtered to those with graph edges)
        logger.info(f"Searching Qdrant for top {top_k} seed entities...")
        seeds = find_seed_entities(qdrant, query_vector, top_k)
        seed_names = [f'{s["name"]} ({s["domain"]}, score={s["score"]})' for s in seeds]
        logger.info(f"Seeds: {seed_names}")

        # Step 3 — traverse graph from each seed
        logger.info("Traversing Neo4j for cross-domain paths...")
        all_paths: list[GraphPath] = []
        for seed in seeds:
            paths = traverse_graph(driver, seed, max_paths=max_paths // top_k + 5)
            all_paths.extend(paths)
            if paths:
                logger.info(f"  {seed['name']}: {len(paths)} cross-domain path(s)")
            else:
                logger.info(f"  {seed['name']}: no cross-domain paths")

        # Deduplicate paths by their node sequence
        seen: set[str] = set()
        unique_paths: list[GraphPath] = []
        for p in all_paths:
            key = json.dumps([n["name"] for n in p.nodes])
            if key not in seen:
                seen.add(key)
                unique_paths.append(p)

        # Sort by hops, keep top max_paths
        unique_paths.sort(key=lambda p: p.hops)
        unique_paths = unique_paths[:max_paths]

        logger.info(f"Total unique cross-domain paths: {len(unique_paths)}")

        # Collect unique source paper IDs from all paths
        all_doc_ids: list[str] = []
        seen_ids: set[str] = set()
        for p in unique_paths:
            for pid in (p.source_paper_ids or []):
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    all_doc_ids.append(pid)

        # Look up source paper metadata
        logger.info(f"Fetching {len(all_doc_ids)} source paper citations...")
        sources = fetch_citations(driver, all_doc_ids[:50])  # cap at 50 citations

        # Step 4 — format context
        paths_text = format_paths_for_prompt(unique_paths, seeds)

        # Step 5 — call Mistral
        logger.info(f"Calling {LLM_MODEL} for synthesis...")
        answer = call_mistral(query, paths_text)

        latency_ms = int((time.time() - start) * 1000)
        confidence = compute_confidence(unique_paths)

        return QueryResult(
            query=query,
            answer=answer,
            paths=unique_paths,
            seed_entities=seed_names,
            sources=sources,
            confidence=confidence,
            latency_ms=latency_ms,
        )

    finally:
        driver.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="GraphRAG cross-domain query engine")
    parser.add_argument("--query", "-q", required=True, help="Natural language query")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Seed entities from Qdrant")
    parser.add_argument("--max-paths", type=int, default=DEFAULT_MAX_PATHS, help="Max paths to send to LLM")
    parser.add_argument("--json", action="store_true", help="Output full JSON instead of readable text")
    args = parser.parse_args()

    result = run_query(args.query, top_k=args.top_k, max_paths=args.max_paths)

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print("\n" + "=" * 70)
        print(f"QUERY: {result.query}")
        print("=" * 70)
        print(f"\nSEED ENTITIES ({len(result.seed_entities)}):")
        for s in result.seed_entities:
            print(f"  • {s}")
        print(f"\nCROSS-DOMAIN PATHS FOUND: {len(result.paths)}")
        print(f"CONFIDENCE: {result.confidence}")
        print(f"\nANSWER (via {LLM_MODEL}):")
        print("-" * 70)
        print(result.answer)
        print("-" * 70)
        print(f"\nLatency: {result.latency_ms}ms")


if __name__ == "__main__":
    main()
