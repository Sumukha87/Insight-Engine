"""
NER Pipeline — Named Entity Recognition over raw arXiv JSONL files.

What this does:
  1. Reads every paper from data/raw/arxiv/{domain}/batch_*.jsonl
  2. Runs spaCy en_core_sci_lg NER on title + abstract
  3. Maps spaCy entity types → our 8 canonical types
  4. Writes one output JSONL per domain to data/processed/entities/
  5. Logs metrics to MLflow

Output format (one JSON per line):
  {
    "doc_id": "arxiv_2401.12345v1",
    "domain": "aerospace",
    "entities": [
      {"text": "titanium alloy", "type": "Material", "start": 42, "end": 56, "domain": "aerospace"}
    ]
  }

Usage:
    python -m src.nlp.ner_pipeline
"""

import json
import logging
import os
from pathlib import Path

import mlflow
import spacy
import yaml
from spacy.language import Language

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw/arxiv")
OUT_DIR = Path("data/processed/entities")
METRICS_DIR = Path("metrics")

# Load params from DVC params.yaml
_params = yaml.safe_load(Path("params.yaml").read_text())["ner"]
MODEL_NAME: str = _params["model_name"]
BATCH_SIZE: int = _params["batch_size"]
MIN_ENTITY_LENGTH: int = _params["min_entity_length"]

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_EXPERIMENT = "insight-engine-nlp"

# Map spaCy / SciSpacy entity labels → our 8 canonical types
# en_core_sci_lg produces labels like CHEMICAL, DISEASE, etc.
ENTITY_TYPE_MAP: dict[str, str] = {
    # SciSpacy biomedical labels
    "CHEMICAL": "Compound",
    "DISEASE": "Disease",
    "ORGANISM": "Organism",
    "GENE_OR_GENE_PRODUCT": "Gene",
    "SIMPLE_CHEMICAL": "Compound",
    "AMINO_ACID": "Compound",
    "CELL": "Organism",
    "CELL_LINE": "Organism",
    "CELL_TYPE": "Organism",
    "DNA": "Gene",
    "RNA": "Gene",
    "PROTEIN": "Gene",
    "TAXON": "Organism",
    # General spaCy labels we remap
    "PRODUCT": "Device",
    "ORG": "Software",      # orgs in scientific text are usually tools/frameworks
    "FAC": "Infrastructure", # facility → infrastructure
    "EVENT": "Phenomenon",  # events in science are usually phenomena
    "GPE": None,        # geo-political — skip
    "LOC": None,        # location — skip
    "PERSON": None,     # person — skip
    "DATE": None,       # date — skip
    "TIME": None,       # skip
    "MONEY": None,      # skip
    "PERCENT": None,    # skip
    "CARDINAL": None,   # numbers — skip
    "ORDINAL": None,    # skip
    "QUANTITY": None,   # skip
    "LANGUAGE": None,   # skip
    "LAW": None,        # skip
    "NORP": None,       # skip
    "WORK_OF_ART": None, # skip
    # Fallback for any unlisted label → Technology (most common in our domains)
}

# Keywords that hint at specific entity types when label is ambiguous
KEYWORD_TYPE_HINTS: dict[str, str] = {
    # Material
    "alloy": "Material", "polymer": "Material", "composite": "Material",
    "ceramic": "Material", "coating": "Material", "fiber": "Material",
    "graphene": "Material", "perovskite": "Material", "nanomaterial": "Material",
    "electrolyte": "Material", "substrate": "Material", "membrane": "Material",
    "nanoparticle": "Material", "nanowire": "Material", "nanotube": "Material",
    # Device
    "sensor": "Device", "implant": "Device", "robot": "Device",
    "actuator": "Device", "transistor": "Device", "electrode": "Device",
    "detector": "Device", "antenna": "Device", "chip": "Device",
    "prosthetic": "Device", "catheter": "Device", "stent": "Device",
    # Process
    "synthesis": "Process", "fabrication": "Process", "deposition": "Process",
    "annealing": "Process", "etching": "Process", "polymerization": "Process",
    "sequencing": "Process", "fermentation": "Process", "oxidation": "Process",
    "photolithography": "Process", "sputtering": "Process", "doping": "Process",
    # Technology
    "technology": "Technology", "system": "Technology",
    "method": "Technology", "technique": "Technology", "platform": "Technology",
    "framework": "Technology", "architecture": "Technology", "mechanism": "Technology",
    # Algorithm
    "algorithm": "Algorithm", "neural network": "Algorithm", "transformer": "Algorithm",
    "classifier": "Algorithm", "optimizer": "Algorithm", "clustering": "Algorithm",
    "regression": "Algorithm", "reinforcement learning": "Algorithm",
    "convolutional": "Algorithm", "diffusion model": "Algorithm",
    # Phenomenon
    "superconductivity": "Phenomenon", "entanglement": "Phenomenon",
    "photovoltaic effect": "Phenomenon", "magnetism": "Phenomenon",
    "fluorescence": "Phenomenon", "catalysis": "Phenomenon",
    "turbulence": "Phenomenon", "resonance": "Phenomenon",
    "conductivity": "Phenomenon", "plasticity": "Phenomenon",
    # Software
    "tensorflow": "Software", "pytorch": "Software", "cuda": "Software",
    "openfoam": "Software", "matlab": "Software", "simulink": "Software",
    "library": "Software", "toolkit": "Software", "simulator": "Software",
    "database": "Software", "pipeline": "Software", "compiler": "Software",
    # Infrastructure
    "grid": "Infrastructure", "network infrastructure": "Infrastructure",
    "propulsion system": "Infrastructure", "reactor": "Infrastructure",
    "pipeline infrastructure": "Infrastructure", "facility": "Infrastructure",
    "power plant": "Infrastructure", "wind farm": "Infrastructure",
}


def resolve_entity_type(spacy_label: str, entity_text: str) -> str | None:
    """
    Convert a spaCy label to our canonical entity type.
    Falls back to keyword matching on entity text, then defaults to Technology.
    Returns None for entity types we want to skip entirely.
    """
    # Direct mapping
    mapped = ENTITY_TYPE_MAP.get(spacy_label)
    if mapped is not None:
        return mapped
    if mapped is None and spacy_label in ENTITY_TYPE_MAP:
        return None  # explicitly skipped

    # Keyword hint matching on lowercased entity text
    text_lower = entity_text.lower()
    for keyword, entity_type in KEYWORD_TYPE_HINTS.items():
        if keyword in text_lower:
            return entity_type

    # Default fallback
    return "Technology"


def process_domain(nlp: Language, domain: str) -> dict:
    """
    Run NER on all JSONL batches for a domain.
    Returns metrics dict: {doc_count, entity_count, entities_per_doc}
    """
    in_dir = RAW_DIR / domain
    out_dir = OUT_DIR / domain
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "entities.jsonl"

    if not in_dir.exists():
        logger.warning(f"[{domain}] No raw data found at {in_dir}, skipping")
        return {"doc_count": 0, "entity_count": 0, "entities_per_doc": 0.0}

    batch_files = sorted(in_dir.glob("batch_*.jsonl"))
    if not batch_files:
        logger.warning(f"[{domain}] No batch files found, skipping")
        return {"doc_count": 0, "entity_count": 0, "entities_per_doc": 0.0}

    doc_count = 0
    entity_count = 0

    with open(out_file, "w") as out_f:
        for batch_file in batch_files:
            with open(batch_file) as f:
                papers = [json.loads(line) for line in f if line.strip()]

            # Combine title + abstract as input text for NER
            texts = [
                (p.get("title", "") + ". " + p.get("abstract", "")).strip()
                for p in papers
            ]
            arxiv_ids = [p["arxiv_id"] for p in papers]

            # spaCy pipe processes texts in batches — faster than one at a time
            for doc, arxiv_id in zip(nlp.pipe(texts, batch_size=BATCH_SIZE), arxiv_ids):
                entities = []
                seen_texts: set[str] = set()

                for ent in doc.ents:
                    # Skip very short or duplicate entities
                    if len(ent.text.strip()) < MIN_ENTITY_LENGTH:
                        continue
                    ent_text_clean = ent.text.strip().lower()
                    if ent_text_clean in seen_texts:
                        continue
                    seen_texts.add(ent_text_clean)

                    entity_type = resolve_entity_type(ent.label_, ent.text)
                    if entity_type is None:
                        continue  # skip unwanted types

                    entities.append({
                        "text": ent.text.strip(),
                        "type": entity_type,
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "domain": domain,
                    })

                record = {
                    "doc_id": f"arxiv_{arxiv_id}",
                    "domain": domain,
                    "entities": entities,
                }
                out_f.write(json.dumps(record) + "\n")

                doc_count += 1
                entity_count += len(entities)

            logger.info(
                f"[{domain}] Processed {batch_file.name} — "
                f"{sum(1 for _ in papers)} papers"
            )

    entities_per_doc = entity_count / doc_count if doc_count > 0 else 0.0
    logger.info(
        f"[{domain}] Done — {doc_count} docs, {entity_count} entities, "
        f"{entities_per_doc:.1f} entities/doc → {out_file}"
    )
    return {
        "doc_count": doc_count,
        "entity_count": entity_count,
        "entities_per_doc": entities_per_doc,
    }


def main() -> None:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading spaCy model: {MODEL_NAME}")
    nlp = spacy.load(MODEL_NAME)
    # Disable unused pipeline components for speed — we only need NER
    nlp.select_pipes(enable=["ner"])

    domains = [d.name for d in RAW_DIR.iterdir() if d.is_dir()]
    logger.info(f"Domains found: {domains}")

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)
    with mlflow.start_run(run_name="ner_pipeline", tags={"stage": "ner", "source": "arxiv"}):
        mlflow.log_param("model_name", MODEL_NAME)
        mlflow.log_param("batch_size", BATCH_SIZE)
        mlflow.log_param("min_entity_length", MIN_ENTITY_LENGTH)
        mlflow.log_param("domains", ",".join(domains))

        total_docs = 0
        total_entities = 0
        all_metrics: dict = {}

        for domain in sorted(domains):
            metrics = process_domain(nlp, domain)
            all_metrics[domain] = metrics
            total_docs += metrics["doc_count"]
            total_entities += metrics["entity_count"]

            # Log per-domain metrics to MLflow
            mlflow.log_metric(f"{domain}_doc_count", metrics["doc_count"])
            mlflow.log_metric(f"{domain}_entity_count", metrics["entity_count"])
            mlflow.log_metric(f"{domain}_entities_per_doc", metrics["entities_per_doc"])

        overall_entities_per_doc = total_entities / total_docs if total_docs > 0 else 0.0
        mlflow.log_param("doc_count", total_docs)
        mlflow.log_metric("entity_count", total_entities)
        mlflow.log_metric("entities_per_doc", overall_entities_per_doc)

        logger.info(
            f"TOTAL — {total_docs} docs, {total_entities} entities, "
            f"{overall_entities_per_doc:.1f} entities/doc"
        )

        # Write metrics JSON for DVC to track
        metrics_out = {
            "total_docs": total_docs,
            "total_entities": total_entities,
            "entities_per_doc": round(overall_entities_per_doc, 2),
            "domains": all_metrics,
        }
        with open(METRICS_DIR / "ner_metrics.json", "w") as f:
            json.dump(metrics_out, f, indent=2)

        # Write per-domain CSV for DVC plots
        csv_rows = ["domain,doc_count,entity_count,entities_per_doc"]
        for domain, m in all_metrics.items():
            csv_rows.append(
                f"{domain},{m['doc_count']},{m['entity_count']},{m['entities_per_doc']:.2f}"
            )
        with open(METRICS_DIR / "ner_domain_stats.csv", "w") as f:
            f.write("\n".join(csv_rows) + "\n")

        # Artifacts (metrics files) are versioned by DVC — no need to duplicate in MLflow


if __name__ == "__main__":
    main()
