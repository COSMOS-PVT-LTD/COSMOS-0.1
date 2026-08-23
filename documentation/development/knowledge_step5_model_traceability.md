# COSMOS Step 5 — Model Traceability

**Document ID:** `COSMOS-STEP5-MODEL-TRACEABILITY-001`  
**Date:** 2026-08-23  
**Baseline SHA:** `32dd3170440342ade8d879239b40707465553ad4`

---

## Traceability Method

For each of the 15 missing models, this document records:

```text
Frozen Architecture File
        ↓
Original Intended Responsibility
        ↓
Current Canonical Replacement / Consolidation
        ↓
Current Runtime Consumers
        ↓
Current Tests
        ↓
Current RAG Relevance
        ↓
Actual Gap?
        ↓
Disposition
```

**Import scan result (all 15 models):** `grep "from knowledge.models.<model>"` → **0 matches** across entire repository.

---

## 1. `appendix.py`

| Layer | Trace |
|---|---|
| **Frozen file** | `knowledge/models/appendix.py` — **ABSENT** |
| **Intended responsibility** | Dedicated appendix entity with identity, letter designation, parent document linkage |
| **Canonical replacement** | `DocumentSection` (`knowledge/parsers/models.py`) — generic structural section |
| **Symbols** | `DocumentSection.section_id`, `.title`, `.level`, `.parent_section_id` |
| **Runtime consumers** | `knowledge/parsers/w3/structure.py` (section building) |
| **Tests** | `tests/unit_tests/knowledge/parsers/test_parsers.py` |
| **RAG path** | W3 parse → W4 extract → graph → W7 index → W8 search — appendix content flows as sections/paragraphs |
| **Gap** | File absent; capability partial (no appendix-specific semantics) |
| **Disposition** | M3 — FUTURE CAPABILITY |

---

## 2. `assumption.py`

| Layer | Trace |
|---|---|
| **Frozen file** | `knowledge/models/assumption.py` — **ABSENT** |
| **Intended responsibility** | First-class assumption with identity, scope, validation state |
| **Canonical replacement** | `EngineeringDomain.assumptions: tuple[str, ...]`; `CanonicalEntityType.CLAIM`; `OntologyTerm` |
| **Symbols** | `EngineeringDomain.assumptions`, `assumption_count()`, `CanonicalEntityType.CLAIM` |
| **Runtime consumers** | `knowledge/models/engineering_domain.py`; `knowledge/graph/entity.py`; W11 `CursorDevelopmentContext` assumptions metadata |
| **Tests** | `tests/unit_tests/knowledge/test_engineering_domain.py` (physical_laws + assumptions tuples) |
| **RAG path** | Assumptions surface as domain metadata and reasoning constraints, not direct retrieval targets |
| **Gap** | None for authorized capability |
| **Disposition** | M2 — CONSOLIDATED |

---

## 3. `boundary_condition.py`

| Layer | Trace |
|---|---|
| **Frozen file** | `knowledge/models/boundary_condition.py` — **ABSENT** |
| **Intended responsibility** | CFD/FEA boundary condition with type, value, surface reference |
| **Canonical replacement** | None — no `ExtractedEntityKind`, no graph entity type, no domain model field |
| **Symbols** | — |
| **Runtime consumers** | None |
| **Tests** | None |
| **RAG path** | Not on authorized path; `boundary_condition_extractor.py` deferred (MCAP-010) |
| **Gap** | File absent; capability absent but **not required** by current authorization |
| **Disposition** | M3 — FUTURE CAPABILITY |

---

## 4. `chapter.py`

| Layer | Trace |
|---|---|
| **Frozen file** | `knowledge/models/chapter.py` — **ABSENT** |
| **Intended responsibility** | Top-level document chapter with number, title, section children |
| **Canonical replacement** | `DocumentSection` with `level=1` and `parent_section_id=None` |
| **Symbols** | `DocumentSection` |
| **Runtime consumers** | `knowledge/parsers/w3/structure.py` (markdown/HTML heading → sections) |
| **Tests** | `tests/unit_tests/knowledge/parsers/test_parsers.py` |
| **RAG path** | Chapter structure informs parse hierarchy; retrieval uses entity/graph indexes |
| **Gap** | None |
| **Disposition** | M2 — CONSOLIDATED |

---

## 5. `correlation.py`

| Layer | Trace |
|---|---|
| **Frozen file** | `knowledge/models/correlation.py` — **ABSENT** |
| **Intended responsibility** | Empirical correlation (e.g., Nusselt number correlations) |
| **Canonical replacement** | Partial overlap: `Equation`, `Quantity`; ADR-pending `empirical_relation.py` (F) |
| **Symbols** | `knowledge.models.equation.Equation`, `knowledge.models.quantity.Quantity` |
| **Runtime consumers** | Equation/quantity models (existing A-match files) |
| **Tests** | `test_extraction.py`, `test_quantity.py` |
| **RAG path** | Correlations retrievable as equations/quantities when extracted; no dedicated correlation type |
| **Gap** | File absent; dedicated correlation semantics not required for current RAG |
| **Disposition** | M3 — FUTURE CAPABILITY (ADR on empirical_relation first) |

---

## 6. `design_rule.py`

| Layer | Trace |
|---|---|
| **Frozen file** | `knowledge/models/design_rule.py` — **ABSENT** |
| **Intended responsibility** | Traceable engineering design rule with applicability conditions |
| **Canonical replacement** | None active; frozen `design_rule_extractor.py` and `design_rule_repository.py` deferred |
| **Symbols** | — |
| **Runtime consumers** | None |
| **Tests** | None |
| **RAG path** | Not on authorized path (MCAP-012 extractor deferred) |
| **Gap** | File absent; capability absent but not blocking current pipeline |
| **Disposition** | M3 — FUTURE CAPABILITY |

---

## 7. `experiment.py`

| Layer | Trace |
|---|---|
| **Frozen file** | `knowledge/models/experiment.py` — **ABSENT** |
| **Intended responsibility** | Experiment/campaign entity linking tests to knowledge |
| **Canonical replacement** | `ExtractedEntityKind.EXPERIMENT` → `CanonicalEntityType.OTHER` → graph candidate node |
| **Symbols** | `CandidateEntityExtraction`, `ExtractedEntityKind.EXPERIMENT` |
| **Runtime consumers** | `knowledge/extraction/entity.py`, `knowledge/extraction/w4/entities.py`, `GraphConstructor` |
| **Tests** | W4 extraction unit tests; BLOCK-012 integration (entity extraction chain) |
| **RAG path** | Experiments as graph entities when extracted → indexed → searchable |
| **Gap** | None |
| **Disposition** | M2 — CONSOLIDATED |

---

## 8. `failure_mode.py`

| Layer | Trace |
|---|---|
| **Frozen file** | `knowledge/models/failure_mode.py` — **ABSENT** |
| **Intended responsibility** | Failure mode with severity, cause, effect (FMEA) |
| **Canonical replacement** | `Subsystem.failure_mode_ids: tuple[str, ...]`; graph nodes via extraction |
| **Symbols** | `Subsystem.failure_mode_ids`, `failure_mode_count()` |
| **Runtime consumers** | `knowledge/models/subsystem.py` |
| **Tests** | `tests/unit_tests/knowledge/test_subsystem.py` |
| **RAG path** | Failure modes referenced by subsystem IDs; not standalone RAG retrieval type |
| **Gap** | None for authorized capability |
| **Disposition** | M2 — CONSOLIDATED |

---

## 9. `glossary.py`

| Layer | Trace |
|---|---|
| **Frozen file** | `knowledge/models/glossary.py` — **ABSENT** |
| **Intended responsibility** | Glossary container with term-definition pairs |
| **Canonical replacement** | `OntologyTerm` + `OntologyAlias` (partial definitional coverage) |
| **Symbols** | `OntologyTerm`, `OntologyAlias`, `OntologyRegistry.resolve_alias()` |
| **Runtime consumers** | `knowledge/ontology/registry.py`, `OntologyManager` facade |
| **Tests** | `tests/unit_tests/knowledge/ontology/test_w5_ontology.py`; `test_compat_ontology.py` |
| **RAG path** | Term resolution via ontology; no glossary container parsing |
| **Gap** | File absent; glossary parser deferred (MCAP-050) |
| **Disposition** | M3 — FUTURE CAPABILITY |

---

## 10. `manufacturing_process.py`

| Layer | Trace |
|---|---|
| **Frozen file** | `knowledge/models/manufacturing_process.py` — **ABSENT** |
| **Intended responsibility** | Manufacturing process with steps, parameters, materials |
| **Canonical replacement** | `ExtractedEntityKind.PROCESS`; `EngineeringDomainCategory.MANUFACTURING` |
| **Symbols** | `ExtractedEntityKind.PROCESS`, `EngineeringDomainCategory` |
| **Runtime consumers** | `knowledge/extraction/entity.py`, `knowledge/models/engineering_domain.py` |
| **Tests** | W4 extraction tests |
| **RAG path** | Process entities as graph candidates when extracted |
| **Gap** | None |
| **Disposition** | M2 — CONSOLIDATED |

---

## 11. `physical_law.py`

| Layer | Trace |
|---|---|
| **Frozen file** | `knowledge/models/physical_law.py` — **ABSENT** |
| **Intended responsibility** | Named physical law with formal statement and domain |
| **Canonical replacement** | `EngineeringDomain.physical_laws: tuple[str, ...]`; ontology term registration |
| **Symbols** | `EngineeringDomain.physical_laws`, `physical_law_count()` |
| **Runtime consumers** | `knowledge/models/engineering_domain.py` |
| **Tests** | `tests/unit_tests/knowledge/test_engineering_domain.py` |
| **RAG path** | Laws referenced by domain ID tuples; equations may express law relationships |
| **Gap** | None |
| **Disposition** | M2 — CONSOLIDATED |

---

## 12. `process.py`

| Layer | Trace |
|---|---|
| **Frozen file** | `knowledge/models/process.py` — **ABSENT** |
| **Intended responsibility** | Generic engineering process entity |
| **Canonical replacement** | `ExtractedEntityKind.PROCESS` → graph candidate |
| **Symbols** | `ExtractedEntityKind.PROCESS`, `CandidateEntityExtraction` |
| **Runtime consumers** | `knowledge/extraction/entity.py`, `GraphConstructor` |
| **Tests** | W4 extraction tests |
| **RAG path** | Process labels searchable via graph/lexical indexes when extracted |
| **Gap** | None |
| **Disposition** | M2 — CONSOLIDATED |

---

## 13. `property.py`

| Layer | Trace |
|---|---|
| **Frozen file** | `knowledge/models/property.py` — **ABSENT** |
| **Intended responsibility** | Standalone material/engineering property (density, conductivity, etc.) |
| **Canonical replacement** | `Material` inline property validators; `Quantity` for measured values with units |
| **Symbols** | `Material` (mechanical/thermal/electrical validators), `Quantity` |
| **Runtime consumers** | `knowledge/models/material.py`, `knowledge/models/quantity.py` |
| **Tests** | `test_material.py`, `test_quantity.py` [FROZEN BLOCK-007] |
| **RAG path** | Properties retrieved via material/quantity graph nodes and indexes |
| **Gap** | None — separate Property class would duplicate existing models |
| **Disposition** | M2 — CONSOLIDATED |

---

## 14. `section.py`

| Layer | Trace |
|---|---|
| **Frozen file** | `knowledge/models/section.py` — **ABSENT** |
| **Intended responsibility** | Document section with identity, title, hierarchy |
| **Canonical replacement** | `DocumentSection` in `knowledge/parsers/models.py` |
| **Symbols** | `DocumentSection`, `NormalizedParsedDocument.sections` |
| **Runtime consumers** | `knowledge/parsers/w3/structure.py`, `knowledge/parsers/w3/models.py` |
| **Tests** | `tests/unit_tests/knowledge/parsers/test_parsers.py`; `test_w3_parsing.py` |
| **RAG path** | Sections provide parse structure; Phase-C `ambiguity_detector` uses `parsed_document.sections` |
| **Gap** | None |
| **Disposition** | M2 — CONSOLIDATED |

---

## 15. `simulation.py`

| Layer | Trace |
|---|---|
| **Frozen file** | `knowledge/models/simulation.py` — **ABSENT** |
| **Intended responsibility** | Simulation case/study with inputs, outputs, solver reference |
| **Canonical replacement** | `Subsystem.simulation_case_ids`, `related_simulation_ids`; `Quantity` simulation relationship fields |
| **Symbols** | `Subsystem.simulation_case_ids`, `related_simulation_ids` |
| **Runtime consumers** | `knowledge/models/subsystem.py`, `knowledge/models/quantity.py` |
| **Tests** | `tests/unit_tests/knowledge/test_subsystem.py` |
| **RAG path** | Simulation references via subsystem/quantity ID tuples |
| **Gap** | None |
| **Disposition** | M2 — CONSOLIDATED |

---

## Existing Model Inventory (Verification)

Live `knowledge/models/*.py` files (11 — all A-match):

```text
constant.py, dimension.py, document.py, engineering_domain.py,
equation.py, material.py, quantity.py, reference.py,
subsystem.py, unit.py, variable.py
```

Missing from frozen 36-model set: **15 E + 2 F + 8 C** (C models consolidated elsewhere per gap analysis).

---

## RAG Pipeline Traceability (All 15 Models)

| Pipeline Stage | Relevance to Missing Models |
|---|---|
| Source / Ingestion | No missing model required |
| W3 Parsing | `section`, `chapter` → `DocumentSection` (covered) |
| W4 Extraction | `experiment`, `process`, `manufacturing_process` → `ExtractedEntityKind` (covered) |
| Ontology | `assumption`, `physical_law`, `glossary` → domain tuples + ontology terms (partial) |
| Graph | All M2 entities → graph candidate nodes via extraction |
| W7 Indexing | Indexes graph entities — no model-file dependency |
| W8 Search | Searches indexed entities — no model-file dependency |
| W9 Validation | `validate_context` — no missing model dependency |
| W10 Reasoning | Evidence/context models — no missing model dependency |
| Controlled RAG | `provider_invoked=False` — verified without missing models |
| Context Packaging | W11 — no missing model dependency |
| Engineering Interface | Payload built from packaged context — no missing model dependency |

**Conclusion:** None of the 15 missing models block the authorized controlled local RAG pipeline.
