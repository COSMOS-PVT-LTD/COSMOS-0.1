# Knowledge Model Architecture Decisions

**Document ID:** COSMOS-KG-MODEL-ADR-PREP-001  
**Date:** 2026-08-23  
**Phase:** GOVERNANCE — no implementation  
**Authority:** Master Prompt §7

---

## Summary

| Category | Count |
|----------|-------|
| EXACT_MATCH — no action | 11 |
| CONSOLIDATED — approve, no new file | 8 |
| GAP-5 DECISION_REQUIRED | 2 |
| GAP-1 deferred domain models | 11 |
| GAP-3 structure — consolidate to W3 | 4 |
| GAP-6 legacy/non-essential (defer) | 0 |

**Rule applied:** No duplicate Quantity, Unit, Dimension, Entity, Graph, or Search models for filename matching.

---

## Complete 36-Model Decision Table

| # | Frozen File | Frozen Purpose | Existing Equivalent | Current Implementation | Current Consumers | Capability Status | Duplicate Risk | Recommendation | ADR Required | Implementation Required |
|---|-------------|----------------|---------------------|------------------------|-------------------|-------------------|----------------|----------------|--------------|------------------------|
| 1 | `document.py` | Canonical document entity | YES — exact | `knowledge/models/document.py` → `Document` | `repository/repository.py`, ingestion, graph | **IMPLEMENTED** | NONE | **APPROVE** exact match | NO | NO |
| 2 | `chapter.py` | Document chapter structure | YES — parser layer | `parsers/models.py` → `DocumentSection`; `w3/structure.py` | W3 parsing pipeline | **CONSOLIDATED** | HIGH if duplicated | **CONSOLIDATE** into W3 structure; no `models/chapter.py` | NO | NO |
| 3 | `section.py` | Document section structure | YES — parser layer | `DocumentSection` hierarchy in W3 | W3 parsing, indexing | **CONSOLIDATED** | HIGH | **CONSOLIDATE** into W3; no separate model file | NO | NO |
| 4 | `paragraph.py` | Paragraph parse artifact | YES | `parsers/w3/models.py` → `ParsedParagraph` | W3 pipeline, W4 extraction context | **CONSOLIDATED** | HIGH | **CONSOLIDATE** — parser artifact not domain model | NO | NO |
| 5 | `sentence.py` | Sentence-level granularity | NO | None — no `sentence` references in `knowledge/` | None | **DECISION_REQUIRED** | MEDIUM | **SUPERSEDE** — paragraph/section provenance sufficient for current RAG | **YES** (ADR-005) | NO (unless ADR approves NLP) |
| 6 | `figure.py` | Figure parse artifact | YES | `parsers/w3/models.py` → `ParsedFigure` | W3 figures extractor | **CONSOLIDATED** | HIGH | **CONSOLIDATE** | NO | NO |
| 7 | `table.py` | Table parse artifact | YES | `parsers/w3/models.py` → `ParsedTable` | W3 tables extractor | **CONSOLIDATED** | HIGH | **CONSOLIDATE** | NO | NO |
| 8 | `appendix.py` | Appendix structure | PARTIAL — section typing | `DocumentSection` may represent; no appendix-specific type | None dedicated | **PARTIAL** | LOW | **CONSOLIDATE** into W3 structure typing; parser gap remains | NO | Parser only (not model) |
| 9 | `glossary.py` | Glossary term entity | NO dedicated model | None | None | **MISSING** | LOW | **DEFER** — implement glossary parser/extractor first; model follows ADR | NO | Later (GAP-1 parser) |
| 10 | `reference.py` | Bibliographic reference | YES — exact | `knowledge/models/reference.py` → `Reference` | `document.py`, domain models | **IMPLEMENTED** | NONE | **APPROVE** | NO | NO |
| 11 | `citation.py` | In-text citation occurrence | YES | `parsers/w3/models.py` → `CitationOccurrence`; claims in W4 | W3 references, W4 claims | **CONSOLIDATED** | HIGH | **CONSOLIDATE** | NO | NO |
| 12 | `equation.py` | Canonical equation | YES — exact | `knowledge/models/equation.py` → `Equation` | W4, graph, validation | **IMPLEMENTED** | NONE | **APPROVE** | NO | NO |
| 13 | `variable.py` | Canonical variable | YES — exact | `knowledge/models/variable.py` → `Variable` | W4, quantity, graph | **IMPLEMENTED** | NONE | **APPROVE** | NO | NO |
| 14 | `constant.py` | Canonical constant | YES — exact | `knowledge/models/constant.py` → `Constant` | W4, graph | **IMPLEMENTED** | NONE | **APPROVE** | NO | NO |
| 15 | `unit.py` | Unit of measure | YES — exact FROZEN | `knowledge/models/unit.py` → `Unit` | quantity, validation | **IMPLEMENTED** | NONE | **APPROVE** — DO NOT MODIFY | NO | NO |
| 16 | `dimension.py` | Physical dimension | YES — exact FROZEN | `knowledge/models/dimension.py` → `Dimension` | quantity, validation | **IMPLEMENTED** | NONE | **APPROVE** — DO NOT MODIFY | NO | NO |
| 17 | `quantity.py` | Quantity with unit | YES — exact FROZEN | `knowledge/models/quantity.py` → `Quantity` | W4, validation, graph | **IMPLEMENTED** | NONE | **APPROVE** — DO NOT MODIFY | NO | NO |
| 18 | `physical_law.py` | Physical law domain concept | PARTIAL — graph entity | `CanonicalEntityType` + W4 entity kinds; no dedicated model | W4 regex entity extraction | **PARTIAL** | HIGH | **DEFER** distinct model to KG-BLOCK-017; use graph entity interim | YES (ADR-002) | YES (future) |
| 19 | `correlation.py` | Empirical correlation | PARTIAL — graph/claim | W4 claims + graph relationships | Extraction pipeline | **PARTIAL** | HIGH | **DEFER** to BLOCK-017; relationship typing in graph interim | YES (ADR-002) | YES (future) |
| 20 | `empirical_relation.py` | Empirical relation (generic) | OVERLAPS correlation | None distinct | None | **DECISION_REQUIRED** | HIGH | **CONSOLIDATE** into correlation/physical_law taxonomy as graph edge types | **YES** (ADR-006) | NO |
| 21 | `assumption.py` | Engineering assumption | PARTIAL — W4 claims | Claim extraction in `w4/claims.py` | W10 evidence classification | **PARTIAL** | MEDIUM | **CONSOLIDATE** via claims; dedicated model only if ADR-002 approves | YES (ADR-002) | NO (now) |
| 22 | `boundary_condition.py` | BC domain concept | PARTIAL — entity patterns | W4 generic entities | W4 pipeline | **PARTIAL** | MEDIUM | **DEFER** to BLOCK-017 or CONSOLIDATE as entity kind | YES (ADR-002) | Later |
| 23 | `material.py` | Material entity | YES — exact | `knowledge/models/material.py` → `Material` | W4, ontology | **IMPLEMENTED** | NONE | **APPROVE** | NO | NO |
| 24 | `property.py` | Material/entity property | NO dedicated model | Quantity/variable patterns in W4 | W4 quantities | **PARTIAL** | HIGH | **DEFER** — property as quantity+context unless domain requires distinct type | YES (ADR-002) | Later |
| 25 | `component.py` | Component entity | YES — graph typing | `graph/entity.py` → `CanonicalEntityType`; W4 extraction | Graph construction, W4 | **CONSOLIDATED** | HIGH | **CONSOLIDATE** — graph entity, not models/ file | NO | NO |
| 26 | `subsystem.py` | Subsystem entity | YES — exact | `knowledge/models/subsystem.py` → `Subsystem` | Foundation models | **IMPLEMENTED** | NONE | **APPROVE** | NO | NO |
| 27 | `engineering_domain.py` | Domain taxonomy | YES — exact | `knowledge/models/engineering_domain.py` | Ontology, W4 | **IMPLEMENTED** | NONE | **APPROVE** | NO | NO |
| 28 | `process.py` | Process domain concept | PARTIAL — W4 kind | `ExtractedEntityKind.PROCESS` → `CanonicalEntityType.OTHER` | W4 entities | **PARTIAL** | MEDIUM | **CONSOLIDATE** in W4; dedicated model deferred | YES (ADR-002) | Later |
| 29 | `manufacturing_process.py` | Manufacturing process | PARTIAL | W4 PROCESS kind | W4 | **PARTIAL** | MEDIUM | **CONSOLIDATE** / defer distinct model | YES (ADR-002) | Later |
| 30 | `experiment.py` | Experiment entity | PARTIAL | W4 `EXPERIMENT` kind | W4 | **PARTIAL** | MEDIUM | **CONSOLIDATE** / defer | YES (ADR-002) | Later |
| 31 | `simulation.py` | Simulation entity | NO | None | None | **MISSING** | LOW | **DEFER** to BLOCK-017 | YES (ADR-002) | Later |
| 32 | `design_rule.py` | Design rule | PARTIAL — claims | W4 claims pattern | Validation | **PARTIAL** | MEDIUM | **CONSOLIDATE** via claims; model deferred | YES (ADR-002) | Later |
| 33 | `failure_mode.py` | Failure mode (FMECA) | NO | None | None | **MISSING** | LOW | **DEFER** to BLOCK-017 | YES (ADR-002) | Later |
| 34 | `ontology_node.py` | Ontology term node | YES | `ontology/models.py` → `OntologyTerm` | W5 registry, validation | **CONSOLIDATED** | HIGH | **CONSOLIDATE** | NO | NO |
| 35 | `ontology_edge.py` | Taxonomy edge | YES | `ontology/models.py` → `TaxonomyEdge` | W5 taxonomy | **CONSOLIDATED** | HIGH | **CONSOLIDATE** | NO | NO |
| 36 | `metadata.py` | Document/ingestion metadata | YES — distributed | `ingestion/models.py` → `IngestionResult`; source vault metadata | W1/W2/W6 | **CONSOLIDATED** | MEDIUM | **CONSOLIDATE** — metadata at boundaries, not single model | NO | NO |

---

## Special Model Analysis (Master Prompt §7)

### `sentence.py` / `sentence_parser.py`

| Criterion | Finding |
|-----------|---------|
| Required by extraction? | NO — W4 operates on paragraphs/sections |
| Required by provenance? | NO — `LocationAnchor` uses line/section/block |
| Required by evidence chains? | NO — W10 chains use document/section anchors |
| Required by search? | NO |
| Required by RAG context? | NO — context packaged at paragraph/claim level |
| **Decision** | **SUPERSEDE** — sentence infrastructure not justified |

### `empirical_relation.py`

| Criterion | Finding |
|-----------|---------|
| Distinct from correlation? | Unclear in frozen tree — overlapping semantics |
| Graph representation | Relationship edge between entities |
| **Decision** | **CONSOLIDATE** as graph relationship taxonomy; ADR-006 required |

### `chapter.py` / `section.py`

| Criterion | Finding |
|-----------|---------|
| Equivalent | `DocumentSection` in `parsers/models.py` |
| Consumers | W3 structure parser only |
| **Decision** | **CONSOLIDATE** — do not create `models/chapter.py` |

### `physical_law.py` / `correlation.py` / `property.py` / `process.py` / `simulation.py`

| Criterion | Finding |
|-----------|---------|
| Pipeline need now? | PARTIAL — generic W4 entity extraction covers basics |
| Distinct semantics? | YES for production engineering domain |
| Duplicate risk? | HIGH if created without ADR-002 |
| **Decision** | **DEFER** to KG-BLOCK-017; interim via graph entities + W4 kinds |

---

## Protected Models — Immutable Without Change Control

| File | Block | Action |
|------|-------|--------|
| `knowledge/models/quantity.py` | BLOCK-007+ FROZEN | NO modification |
| `knowledge/models/unit.py` | BLOCK-007+ FROZEN | NO modification |
| `knowledge/models/dimension.py` | BLOCK-007+ FROZEN | NO modification |

---

## Model Strategy Conclusion

```text
DO NOT create 25 missing model files to match frozen tree.
APPROVE 11 exact models.
APPROVE 8 consolidations.
SUPERSEDE sentence model (pending ADR-005).
CONSOLIDATE empirical_relation (pending ADR-006).
DEFER 11 domain models to KG-BLOCK-017 with ADR-002 gate.
```

**NO IMPLEMENTATION AUTHORIZED.**
