"""
Data Quality Gate — blocks pipeline promotion if output quality is below thresholds.

Checks:
  1. NER — entity count above minimum
  2. Relations — relation count above minimum
  3. Graph metrics — entity and edge counts above minimum
  4. Embedding coverage — % of entities embedded above minimum
  5. Cross-domain edge ratio — enough cross-domain diversity

Reads thresholds from params.yaml (quality_gate section).
Writes results to metrics/quality_report.json.
Exits with code 1 if any check fails (DVC treats this as stage failure).

Usage:
    python -m src.pipeline.quality_check
"""

import json
import os
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
METRICS_DIR = PROJECT_ROOT / "metrics"
METRICS_DIR.mkdir(exist_ok=True)


def load_params() -> dict:
    params_path = PROJECT_ROOT / "params.yaml"
    with open(params_path) as f:
        return yaml.safe_load(f)


def load_metric_file(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def check_ner(thresholds: dict) -> tuple[bool, dict]:
    metrics = load_metric_file(METRICS_DIR / "ner_metrics.json")
    entity_count = metrics.get("entity_count", 0)
    min_entities = thresholds.get("min_entity_count", 1_000_000)
    passed = entity_count >= min_entities
    return passed, {
        "check": "ner_entity_count",
        "value": entity_count,
        "threshold": min_entities,
        "passed": passed,
    }


def check_relations(thresholds: dict) -> tuple[bool, dict]:
    metrics = load_metric_file(METRICS_DIR / "relation_metrics.json")
    relation_count = metrics.get("relation_count", 0)
    min_relations = thresholds.get("min_relation_count", 500_000)
    passed = relation_count >= min_relations
    return passed, {
        "check": "relation_count",
        "value": relation_count,
        "threshold": min_relations,
        "passed": passed,
    }


def check_graph(thresholds: dict) -> tuple[bool, dict]:
    metrics = load_metric_file(METRICS_DIR / "graph_metrics.json")
    entity_nodes = metrics.get("entity_nodes", 0)
    edge_count = metrics.get("edge_count", 0)
    min_nodes = thresholds.get("min_graph_entity_nodes", 500_000)
    min_edges = thresholds.get("min_graph_edge_count", 500_000)
    node_ok = entity_nodes >= min_nodes
    edge_ok = edge_count >= min_edges
    passed = node_ok and edge_ok
    return passed, {
        "check": "graph_size",
        "entity_nodes": entity_nodes,
        "edge_count": edge_count,
        "min_nodes": min_nodes,
        "min_edges": min_edges,
        "passed": passed,
    }


def check_embedding_coverage(thresholds: dict) -> tuple[bool, dict]:
    """Check what fraction of entity nodes have been embedded."""
    graph_metrics = load_metric_file(METRICS_DIR / "graph_metrics.json")
    total_entities = graph_metrics.get("entity_nodes", 0)

    embedding_metrics_path = METRICS_DIR / "embedding_metrics.json"
    if embedding_metrics_path.exists():
        emb = load_metric_file(embedding_metrics_path)
        embedded = emb.get("embedded_count", 0)
    else:
        # Fall back: count entities in Qdrant via REST if available
        try:
            import httpx

            qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
            resp = httpx.get(f"{qdrant_url}/collections/entities", timeout=5)
            embedded = resp.json()["result"]["vectors_count"]
        except Exception:
            embedded = 0

    coverage = (embedded / total_entities) if total_entities > 0 else 0.0
    min_coverage = thresholds.get("min_embedding_coverage", 0.95)
    passed = coverage >= min_coverage
    return passed, {
        "check": "embedding_coverage",
        "embedded": embedded,
        "total": total_entities,
        "coverage": round(coverage, 4),
        "threshold": min_coverage,
        "passed": passed,
    }


def check_cross_domain_ratio(thresholds: dict) -> tuple[bool, dict]:
    """Check that cross-domain edges are a meaningful fraction of total RELATES_TO edges."""
    graph_metrics = load_metric_file(METRICS_DIR / "graph_metrics.json")
    total_edges = graph_metrics.get("edge_count", 0)
    cross_domain_edges = graph_metrics.get("cross_domain_edge_count", 0)

    ratio = (cross_domain_edges / total_edges) if total_edges > 0 else 0.0
    min_ratio = thresholds.get("min_cross_domain_ratio", 0.50)
    passed = ratio >= min_ratio
    return passed, {
        "check": "cross_domain_ratio",
        "cross_domain_edges": cross_domain_edges,
        "total_edges": total_edges,
        "ratio": round(ratio, 4),
        "threshold": min_ratio,
        "passed": passed,
    }


def main() -> None:
    params = load_params()
    thresholds = params.get("quality_gate", {})

    checks = [
        check_ner(thresholds),
        check_relations(thresholds),
        check_graph(thresholds),
        check_embedding_coverage(thresholds),
        check_cross_domain_ratio(thresholds),
    ]

    all_passed = all(ok for ok, _ in checks)
    results = [result for _, result in checks]

    report = {
        "passed": all_passed,
        "checks": results,
        "failed_checks": [r["check"] for r in results if not r["passed"]],
    }

    report_path = METRICS_DIR / "quality_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Quality Gate Report")
    print(f"{'='*50}")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['check']}")

    print(f"{'='*50}")
    print(f"Overall: {'PASS' if all_passed else 'FAIL'}")
    print(f"Report written to: {report_path}")

    if not all_passed:
        print(f"\nFailed checks: {report['failed_checks']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
