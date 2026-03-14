# NLP Pipeline Rules

## Entity Extraction Standards

- Always use `en_core_sci_lg` for biomedical text, `en_core_web_trf` for engineering/patent text
- Entity type mapping — use ONLY these types (map everything to one of them):
  - `Technology` — methods, algorithms, techniques, processes
  - `Material` — substances, compounds, alloys, polymers
  - `Disease` — conditions, disorders, syndromes
  - `Device` — instruments, implants, machines, sensors
  - `Compound` — chemicals, drugs, molecules
  - `Process` — manufacturing steps, biological processes
  - `Organism` — bacteria, viruses, cell types
  - `Gene` — genes, proteins, biomarkers

## Relation Types — Exact Strings

Only use these relation labels (case-sensitive):
`TREATS`, `INHIBITS`, `IMPROVES`, `DERIVED_FROM`, `COMPOSED_OF`,
`USED_IN`, `CAUSES`, `INTERACTS_WITH`, `SYNTHESIZED_FROM`, `REPLACES`

## MLflow Logging Convention

Every NLP run must log:
```python
mlflow.log_param("model_name", ...)
mlflow.log_param("domain", ...)
mlflow.log_param("doc_count", ...)
mlflow.log_metric("entity_count", ...)
mlflow.log_metric("relation_count", ...)
mlflow.log_metric("entities_per_doc", ...)
mlflow.log_metric("precision", ...)   # if eval set available
mlflow.log_metric("recall", ...)
```

## DVC Pipeline Stages

```yaml
# dvc.yaml pattern for NLP stages
stages:
  ner_pipeline:
    cmd: python src/nlp/ner_pipeline.py
    deps:
      - data/processed/parsed/
      - src/nlp/ner_pipeline.py
    outs:
      - data/processed/entities/
    metrics:
      - metrics/ner_metrics.json
```

## Output Format — JSONL

Every stage outputs JSONL (one JSON object per line):

```json
{"doc_id": "pubmed_12345", "entities": [{"text": "titanium alloy", "type": "Material", "start": 42, "end": 56, "domain": "Aerospace"}], "relations": [{"head": "titanium alloy", "tail": "fatigue resistance", "type": "IMPROVES", "confidence": 0.87}]}
```
