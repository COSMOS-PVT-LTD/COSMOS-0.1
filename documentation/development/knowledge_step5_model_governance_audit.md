# COSMOS Step 5 — Model Governance Audit

**Document ID:** `COSMOS-STEP5-MODEL-GOVERNANCE-AUDIT-001`  
**Phase:** Step 5 — Missing Model Governance & Non-Implementation Audit  
**Baseline SHA:** `32dd3170440342ade8d879239b40707465553ad4`  
**Audit Date:** 2026-08-23  
**Authority:** Governance-only — **no implementation authorized**

---

## Executive Summary

Step 5 audited all **15** `knowledge/models/*.py` files classified as **E — MISSING_REQUIRED** in `knowledge_models_gap_analysis.md` (COSMOS-KG-MODELS-GAP-002). Each model was traced against the live repository, canonical replacements, runtime consumers, tests, and the controlled local RAG pipeline.

**Result:** No genuine current capability gaps (M6) were identified. **Zero model files were created or modified.**

| Disposition | Count |
|---|---|
| M1 — Already Covered | 0 |
| M2 — Consolidated | 10 |
| M3 — Future Capability | 5 |
| M4 — Superseded | 0 |
| M5 — ADR Required | 0 *(within the 15-model set)* |
| M6 — Genuine Current Gap | **0** |
| M7 — Legacy / Non-Essential | 0 |

**Default decision applied:** DEFER / DO NOT IMPLEMENT for all 15 models.

Two additional models outside this set — `empirical_relation.py` and `sentence.py` — are classified **F — MISSING_DECISION_REQUIRED** and are tracked as ADR-pending items (see decision register).

Certification claims remain unchanged:

```text
TEST-QUALIFIED: YES | INTEGRATION-QUALIFIED: YES
PRODUCTION-QUALIFIED: NO | PRODUCTION-READY: NO
FILE-LEVEL 100% MATCH: NO
Controlled local RAG: VERIFIED | provider_invoked: False
```

---

## Methodology

1. **Authoritative list derivation** — Extracted the 15 E-disposition models from `knowledge_models_gap_analysis.md` and cross-checked against `kg_reconciliation_registry.json` entries.
2. **Live repository verification** — Confirmed file absence under `knowledge/models/` (only 11 model files exist).
3. **Reverse import scan** — Searched entire repository for imports of missing model modules; **zero hits**.
4. **Canonical replacement mapping** — Traced each frozen responsibility to W3 parsers, W4 extraction, ontology, graph, existing domain models, or ID-reference patterns.
5. **Runtime consumer analysis** — Identified actual consumers of equivalent capability (not hypothetical frozen-tree consumers).
6. **Test evidence** — Referenced existing unit/integration tests proving current behavior.
7. **RAG pipeline trace** — Verified W1→W11 controlled path does not require standalone missing models.
8. **Disposition classification** — Applied M1–M7 decision tree per Step 5 §17.
9. **Frozen integrity** — Confirmed no `knowledge/` implementation changes in Step 5.

---

## Authoritative Model List (15)

Derived from `knowledge_models_gap_analysis.md` §36-Model Reconciliation (E disposition only):

| # | Frozen Path | KG Ref | Gap Analysis Disp |
|---|---|---|---|
| 1 | `knowledge/models/appendix.py` | KG-014 | E |
| 2 | `knowledge/models/assumption.py` | KG-022 | E |
| 3 | `knowledge/models/boundary_condition.py` | KG-019+ | E |
| 4 | `knowledge/models/chapter.py` | KG-014 | E |
| 5 | `knowledge/models/correlation.py` | KG-019+ | E |
| 6 | `knowledge/models/design_rule.py` | KG-019 | E |
| 7 | `knowledge/models/experiment.py` | KG-019 | E |
| 8 | `knowledge/models/failure_mode.py` | KG-019 | E |
| 9 | `knowledge/models/glossary.py` | KG-014 | E |
| 10 | `knowledge/models/manufacturing_process.py` | KG-019 | E |
| 11 | `knowledge/models/physical_law.py` | KG-019+ | E |
| 12 | `knowledge/models/process.py` | KG-019 | E |
| 13 | `knowledge/models/property.py` | KG-019 | E |
| 14 | `knowledge/models/section.py` | KG-014 | E |
| 15 | `knowledge/models/simulation.py` | KG-019 | E |

**Not in this audit set (F — decision required):** `empirical_relation.py`, `sentence.py` — require ADR before any implementation decision.

---

## Model-by-Model Findings

### 1. `section.py` — M2 CONSOLIDATED

| Field | Finding |
|---|---|
| **Frozen purpose** | Canonical domain model for document sections (structural hierarchy, title, identity). |
| **Current representation** | `knowledge/parsers/models.py` → `DocumentSection`; composed in W3 `ParsedDocument.sections`. |
| **Runtime consumers** | `knowledge/parsers/w3/structure.py`, `knowledge/parsers/w3/models.py`, W3 parse pipeline. |
| **Tests** | `tests/unit_tests/knowledge/parsers/test_parsers.py` |
| **RAG relevance** | **Indirect** — sections provide document structure for parsing/extraction; no standalone Section domain entity needed in RAG retrieval. |
| **Capability gap** | **NO** — file absence only. |
| **Recommendation** | **DO NOT IMPLEMENT** — use `DocumentSection`. |

### 2. `chapter.py` — M2 CONSOLIDATED

| Field | Finding |
|---|---|
| **Frozen purpose** | Top-level document chapter entity with identity and hierarchy. |
| **Current representation** | `DocumentSection` with `level` and `parent_section_id` — top-level sections (level=1) serve as chapters. |
| **Runtime consumers** | W3 structure builders (`knowledge/parsers/w3/structure.py`). |
| **Tests** | `test_parsers.py` (DocumentSection contract) |
| **RAG relevance** | **Indirect** — same as section. |
| **Capability gap** | **NO** |
| **Recommendation** | **DO NOT IMPLEMENT** — chapter semantics via section hierarchy. |

### 3. `appendix.py` — M3 FUTURE CAPABILITY

| Field | Finding |
|---|---|
| **Frozen purpose** | Dedicated appendix entity (lettered appendices, cross-references). |
| **Current representation** | Generic `DocumentSection` can hold appendix content; no appendix-specific typing or parser. |
| **Runtime consumers** | None requiring `Appendix` class. |
| **Tests** | None (no appendix-specific contract). |
| **RAG relevance** | **Low** — appendix content retrievable as sections/paragraphs if present in source. |
| **Capability gap** | **NO for current authorized capability** — dedicated appendix semantics deferred (MCAP-049 `appendix_parser.py`). |
| **Recommendation** | **DEFER** until appendix parser ADR/block authorization. |

### 4. `glossary.py` — M3 FUTURE CAPABILITY

| Field | Finding |
|---|---|
| **Frozen purpose** | Glossary term collection model for definitional knowledge. |
| **Current representation** | Ontology aliases/terms (`OntologyTerm`, `OntologyAlias`) partially cover definitional semantics; no glossary container model. |
| **Runtime consumers** | None. |
| **Tests** | `test_w5_ontology.py` (ontology terms, not glossary model). |
| **RAG relevance** | **Low** — term definitions retrievable via ontology resolution when registered. |
| **Capability gap** | **NO for current pipeline** — glossary parser absent (MCAP-050). |
| **Recommendation** | **DEFER** — implement glossary parser + model only with future block authorization. |

### 5. `assumption.py` — M2 CONSOLIDATED

| Field | Finding |
|---|---|
| **Frozen purpose** | First-class assumption entity for engineering analysis. |
| **Current representation** | `EngineeringDomain.assumptions: tuple[str, ...]` (opaque ID refs); graph `CLAIM` entity type; ontology terms. |
| **Runtime consumers** | `knowledge/models/engineering_domain.py`; W11 interface assumptions metadata. |
| **Tests** | `tests/unit_tests/knowledge/test_engineering_domain.py` |
| **RAG relevance** | **Indirect** — assumptions surface in domain context and reasoning constraints, not as standalone retrieval targets. |
| **Capability gap** | **NO** — ID-reference pattern sufficient for current scope. |
| **Recommendation** | **DO NOT IMPLEMENT** standalone Assumption model. |

### 6. `boundary_condition.py` — M3 FUTURE CAPABILITY

| Field | Finding |
|---|---|
| **Frozen purpose** | CFD/FEA boundary condition entity. |
| **Current representation** | None as first-class model; no `ExtractedEntityKind` for boundary conditions. |
| **Runtime consumers** | None. |
| **Tests** | None. |
| **RAG relevance** | **None for current controlled RAG** — no boundary_condition_extractor (MCAP-010). |
| **Capability gap** | **NO for authorized capability** — future simulation/CFD domain. |
| **Recommendation** | **DEFER** to future KG block with simulation domain pack. |

### 7. `correlation.py` — M3 FUTURE CAPABILITY

| Field | Finding |
|---|---|
| **Frozen purpose** | Empirical correlation entity (e.g., heat-transfer correlations). |
| **Current representation** | Overlaps with `empirical_relation.py` (F — ADR pending); equations/quantities cover numeric relationships partially. |
| **Runtime consumers** | None. |
| **Tests** | None. |
| **RAG relevance** | **None currently** — no correlation_extractor (MCAP-011). |
| **Capability gap** | **NO** — requires ADR on correlation vs empirical_relation first. |
| **Recommendation** | **DEFER** — resolve empirical_relation ADR before any correlation model. |

### 8. `design_rule.py` — M3 FUTURE CAPABILITY

| Field | Finding |
|---|---|
| **Frozen purpose** | Engineering design rule entity with traceability. |
| **Current representation** | None; design rules referenced in frozen tree extractors/repos (all deferred). |
| **Runtime consumers** | None in live code. |
| **Tests** | None. |
| **RAG relevance** | **None** — no design_rule_extractor (MCAP-012). |
| **Capability gap** | **NO for current pipeline** |
| **Recommendation** | **DEFER** to future domain extraction block. |

### 9. `experiment.py` — M2 CONSOLIDATED

| Field | Finding |
|---|---|
| **Frozen purpose** | Experiment entity linking test campaigns to knowledge. |
| **Current representation** | `ExtractedEntityKind.EXPERIMENT` → `CanonicalEntityType.OTHER` → graph candidate nodes. |
| **Runtime consumers** | `knowledge/extraction/entity.py`, `knowledge/extraction/w4/entities.py` |
| **Tests** | W4 extraction tests (entity kind mapping). |
| **RAG relevance** | **Indirect** — experiments retrievable as graph entities when extracted. |
| **Capability gap** | **NO** — extraction + graph path sufficient. |
| **Recommendation** | **DO NOT IMPLEMENT** standalone Experiment model. |

### 10. `failure_mode.py` — M2 CONSOLIDATED

| Field | Finding |
|---|---|
| **Frozen purpose** | Failure mode entity for reliability/safety analysis. |
| **Current representation** | `Subsystem.failure_mode_ids: tuple[str, ...]` (opaque refs); graph nodes via extraction. |
| **Runtime consumers** | `knowledge/models/subsystem.py` |
| **Tests** | `tests/unit_tests/knowledge/test_subsystem.py` (`failure_mode_ids`, `failure_mode_count`) |
| **RAG relevance** | **Indirect** — failure modes referenced by subsystem, not standalone retrieval in current RAG. |
| **Capability gap** | **NO** |
| **Recommendation** | **DO NOT IMPLEMENT** — ID-reference + graph pattern. |

### 11. `manufacturing_process.py` — M2 CONSOLIDATED

| Field | Finding |
|---|---|
| **Frozen purpose** | Manufacturing process entity. |
| **Current representation** | `ExtractedEntityKind.PROCESS` → `CanonicalEntityType.OTHER`; `EngineeringDomainCategory.MANUFACTURING`. |
| **Runtime consumers** | `knowledge/extraction/entity.py` |
| **Tests** | Extraction entity kind tests. |
| **RAG relevance** | **Indirect** |
| **Capability gap** | **NO** |
| **Recommendation** | **DO NOT IMPLEMENT** — process kind + ontology sufficient. |

### 12. `physical_law.py` — M2 CONSOLIDATED

| Field | Finding |
|---|---|
| **Frozen purpose** | Physical law entity (e.g., Newton's laws, conservation laws). |
| **Current representation** | `EngineeringDomain.physical_laws: tuple[str, ...]`; ontology term registration. |
| **Runtime consumers** | `knowledge/models/engineering_domain.py` |
| **Tests** | `tests/unit_tests/knowledge/test_engineering_domain.py` (`physical_laws`) |
| **RAG relevance** | **Indirect** — laws referenced by domain, not direct RAG targets. |
| **Capability gap** | **NO** |
| **Recommendation** | **DO NOT IMPLEMENT** standalone PhysicalLaw model. |

### 13. `process.py` — M2 CONSOLIDATED

| Field | Finding |
|---|---|
| **Frozen purpose** | Generic engineering process entity. |
| **Current representation** | `ExtractedEntityKind.PROCESS` → graph candidate nodes. |
| **Runtime consumers** | `knowledge/extraction/entity.py` |
| **Tests** | W4 entity extraction tests. |
| **RAG relevance** | **Indirect** |
| **Capability gap** | **NO** |
| **Recommendation** | **DO NOT IMPLEMENT** — consolidated into extraction + graph. |

### 14. `property.py` — M2 CONSOLIDATED

| Field | Finding |
|---|---|
| **Frozen purpose** | Material/engineering property entity (density, conductivity, etc.). |
| **Current representation** | `Material` model embeds mechanical/thermal/electrical property validators inline; `Quantity` for measured values with units. |
| **Runtime consumers** | `knowledge/models/material.py`, `knowledge/models/quantity.py` |
| **Tests** | `test_material.py`, `test_quantity.py` |
| **RAG relevance** | **Indirect** — properties retrieved via material/quantity graph nodes. |
| **Capability gap** | **NO** — separate Property class would duplicate Material/Quantity. |
| **Recommendation** | **DO NOT IMPLEMENT** — duplication risk (Step 5 §10). |

### 15. `simulation.py` — M2 CONSOLIDATED

| Field | Finding |
|---|---|
| **Frozen purpose** | Simulation case/study entity. |
| **Current representation** | `Subsystem.simulation_case_ids`, `related_simulation_ids`; `Quantity` simulation relationship fields. |
| **Runtime consumers** | `knowledge/models/subsystem.py`, `knowledge/models/quantity.py` |
| **Tests** | `test_subsystem.py` (simulation ID fields) |
| **RAG relevance** | **Indirect** |
| **Capability gap** | **NO** |
| **Recommendation** | **DO NOT IMPLEMENT** — ID-reference pattern sufficient. |

---

## RAG Safety Verification

| Control | Status |
|---|---|
| `provider_invoked = False` | VERIFIED (Step 4 + BLOCK-012) |
| No mandatory cloud provider | VERIFIED |
| No LLM invocation introduced | VERIFIED (no code changes) |
| Provenance preservation | VERIFIED |
| Lifecycle preservation | VERIFIED |
| Deterministic retrieval | VERIFIED |
| Controlled context packaging | VERIFIED |

Missing models do not block the authorized W1→W11 controlled local RAG path.

---

## Unresolved Questions (Outside 15-Model Set)

| Item | Status | Action |
|---|---|---|
| `empirical_relation.py` vs `correlation.py` | F — ADR pending | Human ADR before either model |
| `sentence.py` vs paragraph-only W3 | F — ADR pending | Human ADR before sentence granularity |
| Dedicated glossary/appendix parsers | E — deferred (MCAP-049/050) | Future block authorization |
| Domain extractors (12) for missing models | E — deferred | Future KG-BLOCK-014+ (not authorized) |

---

## Implementation Recommendation

```text
NO GENUINE COMPATIBILITY FAILURES FOUND
NO MODEL IMPLEMENTATION AUTHORIZED
ALL 15 MODELS: DEFER / DO NOT IMPLEMENT
M6 ITEMS: NONE — SEPARATE AUTHORIZATION NOT REQUIRED
```

**STOP.** Do not proceed to model implementation or KG-BLOCK-014 without explicit human technical-owner authorization.
