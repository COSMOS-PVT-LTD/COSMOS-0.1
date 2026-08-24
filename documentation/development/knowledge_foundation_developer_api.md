# Knowledge Foundation — Developer API

**Document ID:** `COSMOS-KF-DEV-API-001`  
**Freeze:** `KG-KF-REMAINING-PHASES-FREEZE-2026-08-23`

Physics modules and AI callers must use the controlled surface. Do not copy equations into `physics/` modules.

## Start a working store

```python
from knowledge.foundation import KnowledgeFoundationService

service = KnowledgeFoundationService.with_seed_corpus()
query = service.query_service()
bartz = query.find_correlation("Bartz")[0]
```

## Physics boundary

```python
from knowledge.foundation import KnowledgeFoundationService

gateway = KnowledgeFoundationService.with_seed_corpus().physics()
correlation = gateway.get_approved_correlation("Bartz", reynolds_number=5.0e4)
law = gateway.get_approved_law("First Law")
```

## Engineering queries

`EngineeringQueryService` supports:

- `find_equation`
- `find_correlation`
- `find_physical_law`
- `find_material`
- `find_property`
- `find_design_rule`
- `find_boundary_condition`
- `find_failure_mode`
- `find_experiment`
- `find_simulation`

Default constraint: `require_approved=True`. Unapproved knowledge cannot outrank approved knowledge.

## Ingest → review → approve

Extracted equations remain `CANDIDATE` until a reviewer approves them.

```python
from knowledge.foundation import KnowledgeFoundationService
from knowledge.foundation.equation_approval import EquationReviewDecision

service = KnowledgeFoundationService.with_seed_corpus()
draft = service.ingest_markdown(markdown, source_id="SRC-1", artifact_id="ART-1", reference_id="REF-1")
reviewed = service.review_equation(draft.normalized_equations[0], EquationReviewDecision.APPROVE)
```

Unknown-source equations cannot be approved. Dimensionally inconsistent equations cannot be approved when a check is supplied.

## Search and answers

```python
result = service.search("Bartz regenerative cooling")
answer = service.answer("Bartz")
```

Answers include supporting IDs, assumptions, evidence, contradictions, and confidence.

## Governance

Roles: `INGESTOR`, `EXTRACTOR`, `REVIEWER`, `APPROVER`, `ARCHIVIST`, `ONTOLOGY_EDITOR`, `AUDITOR`.

Approval is machine-enforced. Ingestors cannot approve.

## Persistence

```python
digest = service.persist("kf-snapshot.json")
payload = service.load_snapshot("kf-snapshot.json")
```

The snapshot hash is verified on load.

## What this is not

- Not PRODUCTION-READY
- Not a substitute for ingesting the real COSMOS reference library
- OCR and image loaders remain fail-closed
- Embeddings are a retrieval aid, not the knowledge of record
