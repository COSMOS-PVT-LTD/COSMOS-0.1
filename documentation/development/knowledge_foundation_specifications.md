# Knowledge Foundation — Specifications

**Document ID:** `COSMOS-KF-SPECS-001`  
**Freeze:** `KG-KF-MASTER-PLAN-EXEC-2026-08-23`

This is the authoritative specification pack for the completed knowledge infrastructure. Implementation lives under `knowledge/`. Frozen KG-BLOCK-001→013 files are not modified by this layer.

---

## Architecture

Pipeline: Source/Vault → Ingestion → Parsing → Extraction → Ontology → Canonical entity → Validation/Approval → Graph/Index → Controlled retrieval → AI/Physics.

Reconciliation: 175/175 closed, E/F/H = 0. ADRs: KF-001→010.

## Canonical models

Required entities exist under `knowledge/models/`. Layers are not collapsed:

```text
Source artifact → Parsed artifact → Extracted candidate → Canonical entity → Validated entity
```

`EngineeringRelation` kinds: PhysicalLaw, Correlation, EmpiricalRelation, DesignRule. EmpiricalRelation is a **sibling**, not a Correlation subtype.

## Ontology

Canonical identity is `OntologyRegistry`. Aliases (LOX, CH4, Re, Bartz) resolve without rewriting semantics. `EngineeringRelationship` has definition, source/destination kinds, cardinality, and acyclic flags via `relationship_spec()`.

## Graph

The concept graph is the relationship store. Typed graphs are **views** (`knowledge/graph/typed_views.py`). Integrity checks orphans, invalid relationships, duplicates, missing sources, illegal cycles on `is_a`/`part_of`/`depends_on`/`supersedes`/`derived_from`, and surfaces `contradicts` pairs.

## Provenance

`ProvenanceTrace` is required on engineering entities: source reference, document, chapter/section/page when known, extraction method, reviewer, version. Unknown-source equations cannot be approved.

## Validation and lifecycle

```text
IMPORTED → EXTRACTED → CANDIDATE → REVIEWED → APPROVED → DEPRECATED → ARCHIVED / SUPERSEDED
```

Approved knowledge is superseded, not destructively edited. Schema, units/dimensions, provenance, applicability, authority, and numeric contradictions are validated.

## Search and RAG

Query → classify → keyword/equation/variable/citation/semantic retrieval → authority rank → policy filter → evidence + provenance. Unapproved items cannot outrank approved items. Embeddings are retrieval aids only.

## Ingestion and extraction

Office formats (PDF/DOCX/PPTX/XLSX/HTML/MD/LaTeX/EPUB) use existing adapters. PDF binary identity is preserved; the PDF adapter **does not fabricate text**. OCR/image loaders fail closed. Extractors emit candidates only.

## Approval workflow

Human review is mandatory. Roles: ingest, extract, review, approve, deprecate, archive, supersede, modify ontology/rules. Audit events hash the payload.

## Developer API

See `knowledge_foundation_developer_api.md`. Physics modules must use `PhysicsKnowledgeGateway` / `EngineeringQueryService`, including `find_source()`.
