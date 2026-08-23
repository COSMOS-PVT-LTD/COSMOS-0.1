# COSMOS Step 5 — Model Disposition Matrix

**Document ID:** `COSMOS-STEP5-DISPOSITION-MATRIX-001`  
**Date:** 2026-08-23  
**Baseline SHA:** `32dd3170440342ade8d879239b40707465553ad4`

---

## Summary Counts

| Disposition | Count | Action |
|---|---|---|
| M1 — Already Covered | 0 | — |
| M2 — Consolidated | 10 | Do not implement; document consolidation |
| M3 — Future Capability | 5 | Defer |
| M4 — Superseded | 0 | — |
| M5 — ADR Required | 0 | *(within 15-model set)* |
| M6 — Genuine Current Gap | **0** | No implementation authorized |
| M7 — Legacy / Non-Essential | 0 | — |

---

## Full Disposition Matrix

| Model | Frozen Path | Intended Capability | Current Representation | Runtime Consumers | Tests | RAG Relevance | Capability Gap | Disposition | Action |
|---|---|---|---|---|---|---|---|---|---|
| Appendix | `knowledge/models/appendix.py` | Lettered appendix entity with cross-refs | `DocumentSection` (generic); no appendix typing | None | None | Low — content as sections | **NO** (file only) | **M3** | DEFER |
| Assumption | `knowledge/models/assumption.py` | Engineering assumption entity | `EngineeringDomain.assumptions` + graph CLAIM + ontology | `engineering_domain.py`, W11 interface | `test_engineering_domain.py` | Indirect | **NO** | **M2** | DO NOT IMPLEMENT |
| Boundary Condition | `knowledge/models/boundary_condition.py` | CFD/FEA boundary condition | None (no extractor/entity kind) | None | None | None | **NO** (future domain) | **M3** | DEFER |
| Chapter | `knowledge/models/chapter.py` | Top-level document chapter | `DocumentSection` (level=1, hierarchy) | `parsers/w3/structure.py` | `test_parsers.py` | Indirect | **NO** | **M2** | DO NOT IMPLEMENT |
| Correlation | `knowledge/models/correlation.py` | Empirical correlation entity | Overlaps `empirical_relation` (F); equations/quantities partial | None | None | None | **NO** | **M3** | DEFER (ADR first) |
| Design Rule | `knowledge/models/design_rule.py` | Engineering design rule | None; extractor/repo deferred | None | None | None | **NO** | **M3** | DEFER |
| Experiment | `knowledge/models/experiment.py` | Test campaign entity | `ExtractedEntityKind.EXPERIMENT` → graph | `extraction/entity.py`, `extraction/w4/` | W4 extraction tests | Indirect | **NO** | **M2** | DO NOT IMPLEMENT |
| Failure Mode | `knowledge/models/failure_mode.py` | Reliability failure mode | `Subsystem.failure_mode_ids` + graph nodes | `models/subsystem.py` | `test_subsystem.py` | Indirect | **NO** | **M2** | DO NOT IMPLEMENT |
| Glossary | `knowledge/models/glossary.py` | Glossary term collection | `OntologyTerm`/`OntologyAlias` (partial) | `ontology/registry.py` | `test_w5_ontology.py` | Low | **NO** (parser absent) | **M3** | DEFER |
| Manufacturing Process | `knowledge/models/manufacturing_process.py` | Manufacturing process entity | `ExtractedEntityKind.PROCESS` + domain category | `extraction/entity.py` | W4 extraction tests | Indirect | **NO** | **M2** | DO NOT IMPLEMENT |
| Physical Law | `knowledge/models/physical_law.py` | Conservation/physics law entity | `EngineeringDomain.physical_laws` + ontology | `models/engineering_domain.py` | `test_engineering_domain.py` | Indirect | **NO** | **M2** | DO NOT IMPLEMENT |
| Process | `knowledge/models/process.py` | Generic engineering process | `ExtractedEntityKind.PROCESS` → graph | `extraction/entity.py` | W4 extraction tests | Indirect | **NO** | **M2** | DO NOT IMPLEMENT |
| Property | `knowledge/models/property.py` | Material/engineering property | `Material` inline validators + `Quantity` | `models/material.py`, `models/quantity.py` | `test_material.py`, `test_quantity.py` | Indirect | **NO** | **M2** | DO NOT IMPLEMENT |
| Section | `knowledge/models/section.py` | Document section entity | `DocumentSection` in `parsers/models.py` | `parsers/w3/structure.py`, `parsers/w3/models.py` | `test_parsers.py` | Indirect | **NO** | **M2** | DO NOT IMPLEMENT |
| Simulation | `knowledge/models/simulation.py` | Simulation case/study | `Subsystem.simulation_case_ids`, `Quantity` sim refs | `models/subsystem.py`, `models/quantity.py` | `test_subsystem.py` | Indirect | **NO** | **M2** | DO NOT IMPLEMENT |

---

## Consolidation Map (M2 Models)

| Missing Model | Canonical Location | Symbol / Pattern |
|---|---|---|
| `section.py` | `knowledge/parsers/models.py` | `DocumentSection` |
| `chapter.py` | `knowledge/parsers/models.py` | `DocumentSection` (level + parent hierarchy) |
| `assumption.py` | `knowledge/models/engineering_domain.py` | `assumptions: tuple[str, ...]` |
| `experiment.py` | `knowledge/extraction/entity.py` | `ExtractedEntityKind.EXPERIMENT` |
| `failure_mode.py` | `knowledge/models/subsystem.py` | `failure_mode_ids: tuple[str, ...]` |
| `manufacturing_process.py` | `knowledge/extraction/entity.py` | `ExtractedEntityKind.PROCESS` |
| `physical_law.py` | `knowledge/models/engineering_domain.py` | `physical_laws: tuple[str, ...]` |
| `process.py` | `knowledge/extraction/entity.py` | `ExtractedEntityKind.PROCESS` |
| `property.py` | `knowledge/models/material.py`, `quantity.py` | Inline property validators + measured quantities |
| `simulation.py` | `knowledge/models/subsystem.py`, `quantity.py` | `simulation_case_ids`, simulation relationship fields |

---

## Deferred Map (M3 Models)

| Missing Model | Deferred Dependency | Proposed Future Block |
|---|---|---|
| `appendix.py` | `appendix_parser.py` (MCAP-049) | KG-BLOCK-014+ (not authorized) |
| `glossary.py` | `glossary_parser.py` (MCAP-050) | KG-BLOCK-014+ (not authorized) |
| `boundary_condition.py` | `boundary_condition_extractor.py` (MCAP-010) | Simulation/CFD domain pack |
| `correlation.py` | `empirical_relation.py` ADR + `correlation_extractor.py` | ADR then future block |
| `design_rule.py` | `design_rule_extractor.py` (MCAP-012) | Domain extraction block |

---

## Prohibited Actions

The following are **explicitly prohibited** without separate authorization:

- Creating any of the 15 missing `knowledge/models/*.py` files
- Creating empty shells, aliases, or placeholder classes for file-level match gaming
- Duplicating `Entity`, `Quantity`, `Unit`, `Dimension`, `Graph`, or equivalent models
- Modifying frozen KG-BLOCK-001→013 implementation for model restoration
