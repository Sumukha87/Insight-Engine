"""
Embedding Pipeline — Entity nodes → nomic-embed-text → Qdrant → embedding_id back to Neo4j.

Flow:
  1. Stream all Entity nodes from Neo4j (skip already-embedded ones)
  2. Embed each entity as "<name> [<type>]" via nomic-embed-text (Ollama)
  3. Upsert vectors into Qdrant collection "entities"
  4. Write embedding_id back onto the Neo4j Entity node

Usage:
    python -m src.graph.embedding_pipeline

Resume-safe: entities that already have embedding_id are skipped.
"""

import logging
import os
import time
import uuid
from typing import Generator

import mlflow
import requests
from neo4j import GraphDatabase, Driver
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "entities"
VECTOR_DIM = 768

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_EXPERIMENT = "insight-engine-nlp"

# How many entities to embed + upsert per batch
EMBED_BATCH_SIZE = 64
# How many neo4j rows to fetch per page
NEO4J_PAGE_SIZE = 1000

# ---------------------------------------------------------------------------
# Qdrant setup
# ---------------------------------------------------------------------------


def ensure_collection(client: QdrantClient) -> None:
    """Create the Qdrant collection if it doesn't exist."""
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
        logger.info(f"Qdrant collection '{COLLECTION_NAME}' created.")
    else:
        logger.info(f"Qdrant collection '{COLLECTION_NAME}' already exists.")


# ---------------------------------------------------------------------------
# Embedding via Ollama
# ---------------------------------------------------------------------------


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Call Ollama /api/embed for a batch of texts.
    Returns list of 768-dim float vectors.
    """
    response = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": texts},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["embeddings"]


# ---------------------------------------------------------------------------
# Neo4j streaming
# ---------------------------------------------------------------------------


def stream_unembedded_entities(driver: Driver) -> Generator[list[dict], None, None]:
    """
    Page through all Entity nodes that don't yet have embedding_id.
    Yields pages of {id, name, type, domain} dicts.
    """
    skip = 0
    while True:
        with driver.session() as session:
            records = session.run(
                """
                MATCH (e:Entity)
                WHERE e.embedding_id IS NULL
                RETURN elementId(e) AS id, e.name AS name, e.type AS type, e.domain AS domain
                SKIP $skip LIMIT $limit
                """,
                skip=skip,
                limit=NEO4J_PAGE_SIZE,
            ).data()

        if not records:
            break

        yield records
        skip += NEO4J_PAGE_SIZE


def write_embedding_ids(driver: Driver, updates: list[dict]) -> None:
    """
    Batch-write embedding_id back onto Entity nodes.
    updates = [{"id": elementId, "embedding_id": str}, ...]
    """
    with driver.session() as session:
        session.run(
            """
            UNWIND $updates AS row
            MATCH (e:Entity) WHERE elementId(e) = row.id
            SET e.embedding_id = row.embedding_id
            """,
            updates=updates,
        )


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run_embedding_pipeline(driver: Driver, qdrant: QdrantClient) -> dict:
    """
    Stream entities → embed → upsert Qdrant → write embedding_id to Neo4j.
    Returns metrics dict.
    """
    total_embedded = 0
    total_pages = 0

    for page in stream_unembedded_entities(driver):
        total_pages += 1
        logger.info(f"Page {total_pages}: processing {len(page)} entities...")

        # Process page in embed-sized sub-batches
        for i in range(0, len(page), EMBED_BATCH_SIZE):
            sub = page[i : i + EMBED_BATCH_SIZE]

            # Build text for embedding: "titanium alloy [Material]"
            texts = [f"{e['name']} [{e['type']}]" for e in sub]

            # Embed
            vectors = embed_texts(texts)

            # Build Qdrant points
            points = []
            id_map = []  # (neo4j_element_id, qdrant_uuid)

            for entity, vector in zip(sub, vectors):
                qid = str(uuid.uuid4())
                points.append(
                    PointStruct(
                        id=qid,
                        vector=vector,
                        payload={
                            "name": entity["name"],
                            "type": entity["type"],
                            "domain": entity["domain"],
                        },
                    )
                )
                id_map.append({"id": entity["id"], "embedding_id": qid})

            # Upsert to Qdrant
            qdrant.upsert(collection_name=COLLECTION_NAME, points=points)

            # Write embedding_id back to Neo4j
            write_embedding_ids(driver, id_map)

            total_embedded += len(sub)

        if total_pages % 10 == 0:
            logger.info(f"Progress: {total_embedded:,} entities embedded so far...")

    logger.info(f"Embedding pipeline complete — {total_embedded:,} entities embedded.")
    return {"entities_embedded": total_embedded}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    logger.info(f"Connecting to Neo4j at {NEO4J_URI}")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    logger.info("Neo4j connection verified.")

    logger.info(f"Connecting to Qdrant at {QDRANT_URL}")
    qdrant = QdrantClient(url=QDRANT_URL)
    ensure_collection(qdrant)

    # Verify Ollama + embed model is available
    logger.info(f"Verifying Ollama embed model '{EMBED_MODEL}'...")
    test = embed_texts(["test"])
    assert len(test[0]) == VECTOR_DIM, f"Expected {VECTOR_DIM}-dim vector, got {len(test[0])}"
    logger.info("Ollama embed model OK.")

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)

    with mlflow.start_run(
        run_name="embedding_pipeline_v1",
        tags={"stage": "embedding", "model": EMBED_MODEL, "target": "qdrant"},
    ):
        mlflow.log_param("embed_model", EMBED_MODEL)
        mlflow.log_param("collection", COLLECTION_NAME)
        mlflow.log_param("vector_dim", VECTOR_DIM)
        mlflow.log_param("embed_batch_size", EMBED_BATCH_SIZE)

        start = time.time()
        metrics = run_embedding_pipeline(driver, qdrant)
        elapsed = time.time() - start

        mlflow.log_metric("entities_embedded", metrics["entities_embedded"])
        mlflow.log_metric("elapsed_seconds", elapsed)

        collection_info = qdrant.get_collection(COLLECTION_NAME)
        qdrant_count = collection_info.vectors_count or collection_info.points_count or 0
        mlflow.log_metric("qdrant_vector_count", qdrant_count)

        logger.info(
            f"Done — {metrics['entities_embedded']:,} entities embedded in {elapsed:.0f}s "
            f"({metrics['entities_embedded']/elapsed:.0f} entities/sec)"
        )

    driver.close()


if __name__ == "__main__":
    main()
