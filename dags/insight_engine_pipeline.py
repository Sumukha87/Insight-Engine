"""
Insight-Engine — Full Pipeline DAG

6 stages visualised in Airflow:
  fetch_arxiv → ner → relations → graph_loader → embedding_pipeline → graphrag_query

Trigger manually from the Airflow UI (no schedule — runs on demand).
Each stage runs the same Python module you'd run from the command line.
"""

from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

PROJECT_ROOT = str(Path(__file__).parent.parent)
PYTHON = str(Path(__file__).parent.parent / ".venv" / "bin" / "python")

ENV = {
    "PYTHONPATH": PROJECT_ROOT,
    "NEO4J_URI": "bolt://localhost:7687",
    "NEO4J_USER": "neo4j",
    "NEO4J_PASSWORD": "changeme_strong_password",
    "QDRANT_URL": "http://localhost:6333",
    "OLLAMA_URL": "http://localhost:11434",
    "MLFLOW_TRACKING_URI": "http://localhost:5000",
}

with DAG(
    dag_id="insight_engine_pipeline",
    description="Full pipeline: arXiv ingest → NER → relations → Neo4j → Qdrant embeddings → GraphRAG",
    start_date=datetime(2026, 1, 1),
    schedule=None,           # manual trigger only
    catchup=False,
    tags=["insight-engine", "pipeline"],
) as dag:

    fetch_arxiv = BashOperator(
        task_id="fetch_arxiv",
        bash_command=f"cd {PROJECT_ROOT} && {PYTHON} -m src.ingestion.arxiv_fetcher --domain all --max-results 5000",
        env=ENV,
        doc_md="""
        **Stage 1 — Data Ingestion**
        Fetches paper abstracts from arXiv across 12 domains.
        Output: `data/raw/arxiv/<domain>/*.json`
        """,
    )

    ner = BashOperator(
        task_id="ner",
        bash_command=f"cd {PROJECT_ROOT} && {PYTHON} -m src.nlp.ner_pipeline",
        env=ENV,
        doc_md="""
        **Stage 2 — NER Pipeline**
        Runs spaCy en_core_sci_lg on all paper abstracts.
        Extracts 12 entity types. Logs metrics to MLflow.
        Output: `data/processed/entities/<domain>/entities.jsonl`
        """,
    )

    relations = BashOperator(
        task_id="relation_extraction",
        bash_command=f"cd {PROJECT_ROOT} && {PYTHON} -m src.nlp.relation_extractor",
        env=ENV,
        doc_md="""
        **Stage 3 — Relation Extraction**
        Rule-based type-pair matching across entity pairs.
        10 relation types (TREATS, IMPROVES, USED_IN...).
        Output: `data/processed/relations/<domain>/relations.jsonl`
        """,
    )

    graph_loader = BashOperator(
        task_id="graph_loader",
        bash_command=f"cd {PROJECT_ROOT} && {PYTHON} -m src.graph.graph_loader",
        env=ENV,
        doc_md="""
        **Stage 4 — Graph Loading**
        Streams entities + relations into Neo4j via MERGE.
        Deduplicates 10.7M entity mentions → unique nodes.
        Output: Neo4j at bolt://localhost:7687
        """,
    )

    embedding_pipeline = BashOperator(
        task_id="embedding_pipeline",
        bash_command=f"cd {PROJECT_ROOT} && {PYTHON} -m src.graph.embedding_pipeline",
        env=ENV,
        doc_md="""
        **Stage 5 — Embedding Pipeline**
        Streams Entity nodes from Neo4j.
        Embeds via nomic-embed-text (Ollama) → 768-dim vectors.
        Upserts to Qdrant. Writes embedding_id back to Neo4j.
        Output: Qdrant collection 'entities'
        """,
    )

    graphrag_query = BashOperator(
        task_id="graphrag_query_engine",
        bash_command=f"cd {PROJECT_ROOT} && echo 'Stage 6 not built yet — skipping'",
        env=ENV,
        doc_md="""
        **Stage 6 — GraphRAG Query Engine** *(not built yet)*
        User query → Qdrant ANN → Neo4j traversal → Mistral synthesis.
        Script: `src/graph/graphrag_query.py`
        """,
    )

    # Pipeline order
    fetch_arxiv >> ner >> relations >> graph_loader >> embedding_pipeline >> graphrag_query
