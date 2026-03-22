"""
Register the best GraphRAG pipeline run in the MLflow Model Registry.

Usage:
    source .venv/bin/activate
    python scripts/register_pipeline.py

What it does:
1. Searches the "graphrag-queries" experiment for all completed runs.
2. Picks the run with the highest mean confidence score.
3. Logs it to the MLflow Model Registry as "insight-engine-graphrag".
4. Transitions the latest version to the "Staging" stage.

If no logged model artifact exists on the run (graphrag_query uses Ollama, not
a packaged sklearn/pytorch model), we register a pyfunc wrapper that records the
run's params so the registry entry is still meaningful for lineage tracking.
"""

import os
import sys

import mlflow
from mlflow import MlflowClient
from mlflow.exceptions import MlflowException

TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
EXPERIMENT_NAME = "graphrag-queries"
REGISTERED_MODEL_NAME = "insight-engine-graphrag"


def main() -> None:
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()

    # ── 1. Find the experiment ─────────────────────────────────────────────────
    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        print(f"[register_pipeline] Experiment '{EXPERIMENT_NAME}' not found.")
        print("  Run at least one /query request first so MLflow has data to register.")
        sys.exit(1)

    # ── 2. Find the best run by mean confidence score ─────────────────────────
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string="status = 'FINISHED'",
        order_by=["metrics.confidence DESC"],
        max_results=1,
    )
    if not runs:
        print("[register_pipeline] No finished runs found in experiment.")
        sys.exit(1)

    best_run = runs[0]
    run_id = best_run.info.run_id
    confidence = best_run.data.metrics.get("confidence", 0.0)
    paths = best_run.data.metrics.get("paths_found", 0)
    seeds = best_run.data.metrics.get("seeds_found", 0)
    print(f"[register_pipeline] Best run: {run_id}")
    print(f"  confidence={confidence:.3f}  paths={paths}  seeds={seeds}")

    # ── 3. Ensure registered model exists ─────────────────────────────────────
    try:
        client.get_registered_model(REGISTERED_MODEL_NAME)
        print(f"[register_pipeline] Model '{REGISTERED_MODEL_NAME}' already exists in registry.")
    except MlflowException:
        client.create_registered_model(
            name=REGISTERED_MODEL_NAME,
            description=(
                "Insight-Engine GraphRAG query engine. "
                "Tracks Neo4j traversal + Qdrant ANN + Mistral synthesis pipeline quality."
            ),
            tags={
                "team": "insight-engine",
                "pipeline": "graphrag",
                "llm": "mistral:v0.3",
                "embeddings": "nomic-embed-text",
            },
        )
        print(f"[register_pipeline] Created registered model '{REGISTERED_MODEL_NAME}'.")

    # ── 4. Create a model version linked to this run ──────────────────────────
    # GraphRAG uses Ollama (no packaged artifact). We register using the run URI
    # so the registry records lineage without requiring a model artifact blob.
    model_uri = f"runs:/{run_id}/graphrag_pipeline"

    # Try to create version from a logged artifact; fall back to run source.
    try:
        version = client.create_model_version(
            name=REGISTERED_MODEL_NAME,
            source=model_uri,
            run_id=run_id,
            description=(
                f"Auto-registered. confidence={confidence:.3f} "
                f"paths={paths} seeds={seeds}"
            ),
        )
    except MlflowException:
        # Artifact path doesn't exist — register via run source directly.
        version = client.create_model_version(
            name=REGISTERED_MODEL_NAME,
            source=f"runs:/{run_id}",
            run_id=run_id,
            description=(
                f"Auto-registered (no artifact). confidence={confidence:.3f} "
                f"paths={paths} seeds={seeds}"
            ),
        )

    print(f"[register_pipeline] Created version {version.version} of '{REGISTERED_MODEL_NAME}'.")

    # ── 5. Transition to Staging ───────────────────────────────────────────────
    client.transition_model_version_stage(
        name=REGISTERED_MODEL_NAME,
        version=version.version,
        stage="Staging",
        archive_existing_versions=True,
    )
    print(f"[register_pipeline] Version {version.version} transitioned to Staging.")
    print(f"\nView in MLflow UI: {TRACKING_URI}/#/models/{REGISTERED_MODEL_NAME}")


if __name__ == "__main__":
    main()
