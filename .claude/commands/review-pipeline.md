# Pipeline Code Review

Review the file: **$ARGUMENTS**

Check against ALL project rules:

## Cypher Rules
- [ ] All Cypher queries use parameters (`$name`), never f-strings or string concatenation
- [ ] Uses MERGE not CREATE for entity nodes
- [ ] Relationships include `source_paper_id` and `confidence` properties

## NLP Rules
- [ ] Entity types only from the approved 12: Technology, Material, Disease, Device, Compound, Process, Organism, Gene, Algorithm, Phenomenon, Software, Infrastructure
- [ ] Relation labels exact match: TREATS, INHIBITS, IMPROVES, DERIVED_FROM, COMPOSED_OF, USED_IN, CAUSES, INTERACTS_WITH, SYNTHESIZED_FROM, REPLACES
- [ ] MLflow logging includes: model_name, domain, doc_count, entity_count, relation_count, entities_per_doc

## API Rules
- [ ] FastAPI handlers are `async def`
- [ ] Request/response bodies use Pydantic v2 models
- [ ] Prometheus metrics on every endpoint

## General
- [ ] Type hints on all functions
- [ ] Docstrings on all classes
- [ ] No hardcoded secrets (passwords, API keys)
- [ ] No cloud API calls (OpenAI, AWS, Azure)
- [ ] WSL2 paths only (no /mnt/c/)
- [ ] black + isort formatting

List each violation with file path, line number, and the rule broken.
If everything passes, confirm with a summary.
