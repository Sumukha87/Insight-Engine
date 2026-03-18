"""
Relation Extractor v1 — Rule-based co-occurrence relation extraction.

What this does:
  1. Reads entity JSONL from data/processed/entities/{domain}/entities.jsonl
  2. For each document, finds entity pairs that satisfy type-pair relation rules
  3. Assigns a relation type and confidence score
  4. Writes output JSONL to data/processed/relations/{domain}/relations.jsonl
  5. Logs metrics to MLflow under experiment "insight-engine-nlp"

Relation logic (v1 = type-pair rules, no text needed):
  - Entity type pairs → deterministic relation label
  - Confidence is fixed per rule (rule-based, no model uncertainty)
  - Max N relations per document (controlled via params.yaml) to avoid combinatorial explosion

Output format (one JSON per line):
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
        "confidence": 0.7
      }
    ]
  }

Usage:
    python -m src.nlp.relation_extractor
"""

import json
import logging
import os
from itertools import combinations
from pathlib import Path

import mlflow
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ENTITIES_DIR = Path("data/processed/entities")
OUT_DIR = Path("data/processed/relations")
METRICS_DIR = Path("metrics")

# Load params from DVC params.yaml
_params = yaml.safe_load(Path("params.yaml").read_text())["relations"]
CONFIDENCE_THRESHOLD: float = _params["confidence_threshold"]
MAX_RELATIONS_PER_DOC: int = _params["max_relations_per_doc"]

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_EXPERIMENT = "insight-engine-nlp"

# ---------------------------------------------------------------------------
# Relation rules: (head_type, tail_type) → (relation_label, confidence)
# Ordered by priority — first match wins.
# ---------------------------------------------------------------------------
RELATION_RULES: list[tuple[str, str, str, float]] = [
    # Biomedical signal rules (highest priority)
    ("Compound",      "Disease",       "TREATS",           0.85),
    ("Gene",          "Disease",       "CAUSES",           0.80),
    ("Compound",      "Gene",          "INHIBITS",         0.80),
    ("Organism",      "Disease",       "CAUSES",           0.75),
    ("Compound",      "Organism",      "INHIBITS",         0.75),
    # Material / device / manufacturing rules
    ("Material",      "Device",        "COMPOSED_OF",      0.80),
    ("Material",      "Infrastructure","COMPOSED_OF",      0.75),
    ("Process",       "Material",      "SYNTHESIZED_FROM", 0.80),
    ("Material",      "Process",       "DERIVED_FROM",     0.75),
    ("Process",       "Compound",      "SYNTHESIZED_FROM", 0.75),
    ("Process",       "Device",        "USED_IN",          0.70),
    # Technology / algorithm / software rules
    ("Algorithm",     "Technology",    "USED_IN",          0.75),
    ("Software",      "Technology",    "USED_IN",          0.75),
    ("Algorithm",     "Device",        "USED_IN",          0.70),
    ("Software",      "Device",        "USED_IN",          0.70),
    ("Technology",    "Technology",    "IMPROVES",         0.70),
    ("Algorithm",     "Algorithm",     "IMPROVES",         0.70),
    # Compound / gene interactions
    ("Compound",      "Compound",      "INTERACTS_WITH",   0.70),
    ("Gene",          "Gene",          "INTERACTS_WITH",   0.70),
    ("Gene",          "Compound",      "INTERACTS_WITH",   0.70),
    # Phenomenon rules
    ("Phenomenon",    "Material",      "CAUSES",           0.70),
    ("Phenomenon",    "Device",        "CAUSES",           0.70),
    ("Material",      "Phenomenon",    "CAUSES",           0.70),
    # Catch-all for same-type pairs within key types
    ("Material",      "Material",      "DERIVED_FROM",     0.65),
    ("Device",        "Device",        "REPLACES",         0.65),
    ("Technology",    "Device",        "USED_IN",          0.65),
    ("Compound",      "Process",       "USED_IN",          0.65),
]

# Build lookup: (head_type, tail_type) → (relation, confidence)
_RULE_LOOKUP: dict[tuple[str, str], tuple[str, float]] = {
    (h, t): (rel, conf) for h, t, rel, conf in RELATION_RULES
}


def get_relation(head_type: str, tail_type: str) -> tuple[str, float] | None:
    """Return (relation_label, confidence) for a type pair, or None if no rule matches."""
    result = _RULE_LOOKUP.get((head_type, tail_type))
    if result and result[1] >= CONFIDENCE_THRESHOLD:
        return result
    # Try reversed pair with symmetric relations
    rev = _RULE_LOOKUP.get((tail_type, head_type))
    if rev and rev[0] in {"INTERACTS_WITH", "IMPROVES"} and rev[1] >= CONFIDENCE_THRESHOLD:
        return rev
    return None


def extract_relations(entities: list[dict]) -> list[dict]:
    """
    Extract relations from a list of entities in one document.
    Returns a list of relation dicts, capped at MAX_RELATIONS_PER_DOC.
    """
    relations: list[dict] = []

    # Use combinations to avoid duplicate pairs (A,B) and (B,A)
    for ent_a, ent_b in combinations(entities, 2):
        if len(relations) >= MAX_RELATIONS_PER_DOC:
            break

        head_type = ent_a["type"]
        tail_type = ent_b["type"]

        match = get_relation(head_type, tail_type)
        if match is None:
            continue

        relation_label, confidence = match
        relations.append({
            "head": ent_a["text"],
            "head_type": head_type,
            "tail": ent_b["text"],
            "tail_type": tail_type,
            "relation": relation_label,
            "confidence": confidence,
        })

    return relations


def process_domain(domain: str) -> dict:
    """
    Run relation extraction on all entity records for a domain.
    Returns metrics dict: {doc_count, relation_count, relations_per_doc}
    """
    in_file = ENTITIES_DIR / domain / "entities.jsonl"
    out_dir = OUT_DIR / domain
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "relations.jsonl"

    if not in_file.exists():
        logger.warning(f"[{domain}] No entity file at {in_file}, skipping")
        return {"doc_count": 0, "relation_count": 0, "relations_per_doc": 0.0}

    doc_count = 0
    relation_count = 0

    with open(in_file) as in_f, open(out_file, "w") as out_f:
        for line in in_f:
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)
            entities = record.get("entities", [])

            relations = extract_relations(entities)

            out_f.write(json.dumps({
                "doc_id": record["doc_id"],
                "domain": record["domain"],
                "relations": relations,
            }) + "\n")

            doc_count += 1
            relation_count += len(relations)

    relations_per_doc = relation_count / doc_count if doc_count > 0 else 0.0
    logger.info(
        f"[{domain}] Done — {doc_count} docs, {relation_count} relations, "
        f"{relations_per_doc:.1f} relations/doc → {out_file}"
    )
    return {
        "doc_count": doc_count,
        "relation_count": relation_count,
        "relations_per_doc": relations_per_doc,
    }


def main() -> None:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not ENTITIES_DIR.exists():
        raise FileNotFoundError(
            f"Entity directory not found: {ENTITIES_DIR}. Run the NER stage first."
        )

    domains = [d.name for d in ENTITIES_DIR.iterdir() if d.is_dir()]
    if not domains:
        raise ValueError(f"No domain subdirectories found in {ENTITIES_DIR}")
    logger.info(f"Domains: {domains}")

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)
    with mlflow.start_run(
        run_name="relation_extractor_v1",
        tags={"stage": "relations", "version": "v1", "method": "rule-based"},
    ):
        mlflow.log_param("confidence_threshold", CONFIDENCE_THRESHOLD)
        mlflow.log_param("max_relations_per_doc", MAX_RELATIONS_PER_DOC)
        mlflow.log_param("num_rules", len(RELATION_RULES))
        mlflow.log_param("domains", ",".join(sorted(domains)))

        total_docs = 0
        total_relations = 0
        all_metrics: dict = {}

        for domain in sorted(domains):
            metrics = process_domain(domain)
            all_metrics[domain] = metrics
            total_docs += metrics["doc_count"]
            total_relations += metrics["relation_count"]

            mlflow.log_metric(f"{domain}_doc_count", metrics["doc_count"])
            mlflow.log_metric(f"{domain}_relation_count", metrics["relation_count"])
            mlflow.log_metric(f"{domain}_relations_per_doc", metrics["relations_per_doc"])

        overall_relations_per_doc = total_relations / total_docs if total_docs > 0 else 0.0
        mlflow.log_metric("total_relations", total_relations)
        mlflow.log_metric("relations_per_doc", overall_relations_per_doc)

        logger.info(
            f"TOTAL — {total_docs} docs, {total_relations} relations, "
            f"{overall_relations_per_doc:.1f} relations/doc"
        )

        # Write metrics JSON for DVC to track
        metrics_out = {
            "total_docs": total_docs,
            "total_relations": total_relations,
            "relations_per_doc": round(overall_relations_per_doc, 2),
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "domains": all_metrics,
        }
        with open(METRICS_DIR / "relation_metrics.json", "w") as f:
            json.dump(metrics_out, f, indent=2)

        # Write per-domain CSV for DVC plots
        csv_rows = ["domain,doc_count,relation_count,relations_per_doc"]
        for domain, m in all_metrics.items():
            csv_rows.append(
                f"{domain},{m['doc_count']},{m['relation_count']},{m['relations_per_doc']:.2f}"
            )
        with open(METRICS_DIR / "relation_domain_stats.csv", "w") as f:
            f.write("\n".join(csv_rows) + "\n")

        # Artifacts (metrics files) are versioned by DVC — no need to duplicate in MLflow


if __name__ == "__main__":
    main()
