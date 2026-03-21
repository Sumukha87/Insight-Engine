---
name: review-pipeline
description: Review a pipeline script for correctness against project rules — checks Cypher conventions, MLflow logging, DVC tracking, entity types, relation types
allowed-tools: Read, Grep, Glob
---

# Pipeline Code Review

Review the file: **$ARGUMENTS**

Check against ALL project rules:

## Cypher Rules (.claude/rules/graph-rules.md)
- [ ] All Cypher queries use parameters (`$name`), never string interpolation (`f"...{name}..."`)
- [ ] Uses MERGE not CREATE for entity nodes
- [ ] Includes `source_paper_id` and `confidence` on relationships

## NLP Rules (.claude/rules/nlp-rules.md)
- [ ] Entity types are from the approved 12: Technology, Material, Disease, Device, Compound, Process, Organism, Gene, Algorithm, Phenomenon, Software, Infrastructure
- [ ] Relation labels are exact: TREATS, INHIBITS, IMPROVES, DERIVED_FROM, COMPOSED_OF, USED_IN, CAUSES, INTERACTS_WITH, SYNTHESIZED_FROM, REPLACES
- [ ] MLflow logging includes: model_name, domain, doc_count, entity_count, relation_count, entities_per_doc

## API Rules (.claude/rules/api-rules.md)
- [ ] FastAPI handlers are `async def`
- [ ] Request/response bodies use Pydantic v2 models
- [ ] Prometheus metrics on every endpoint

## General (.claude/CLAUDE.md)
- [ ] Type hints on all functions
- [ ] No hardcoded secrets (passwords, API keys)
- [ ] No cloud API calls (OpenAI, AWS, etc.)
- [ ] WSL2 paths only (no /mnt/c/)

## Output
List each violation with file path, line number, and the rule violated.
If everything passes, confirm with a green checkmark summary.
