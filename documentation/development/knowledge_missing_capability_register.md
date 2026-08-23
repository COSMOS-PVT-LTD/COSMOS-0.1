# Knowledge Missing Capability Register

**Document ID:** COSMOS-KG-MISSING-CAP-001
**Date:** 2026-08-23
**Phase:** REGISTER ONLY — no implementation authorized

**Total entries:** 72 (E: 67, F: 5)

---

| ID | Architecture File | Required Capability | Reason | Dependencies | Substitute | Impact | Proposed Block | Test Req | Prod Impact |
|----|-------------------|-------------------|--------|--------------|------------|--------|----------------|----------|-------------|
| MCAP-001 | `knowledge/exporters/database_exporter.py` | Export | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-002 | `knowledge/exporters/graph_exporter.py` | Export | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-003 | `knowledge/exporters/html_exporter.py` | Export | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-004 | `knowledge/exporters/json_exporter.py` | Export | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-005 | `knowledge/exporters/latex_exporter.py` | Export | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-006 | `knowledge/exporters/markdown_exporter.py` | Export | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-007 | `knowledge/exporters/yaml_exporter.py` | Export | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-008 | `knowledge/extraction/abbreviation_extractor.py` | KG-019 | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-009 | `knowledge/extraction/assumption_extractor.py` | KG-019 | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-010 | `knowledge/extraction/boundary_condition_extractor.py` | KG-019 | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-011 | `knowledge/extraction/correlation_extractor.py` | KG-019 | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-012 | `knowledge/extraction/design_rule_extractor.py` | KG-019 | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-013 | `knowledge/extraction/experiment_extractor.py` | KG-019 | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-014 | `knowledge/extraction/failure_mode_extractor.py` | KG-019 | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-015 | `knowledge/extraction/glossary_extractor.py` | KG-019 | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-016 | `knowledge/extraction/manufacturing_extractor.py` | KG-019 | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-017 | `knowledge/extraction/physical_law_extractor.py` | KG-019 | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-018 | `knowledge/extraction/process_extractor.py` | KG-019 | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-019 | `knowledge/extraction/property_extractor.py` | KG-019 | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-020 | `knowledge/extraction/simulation_extractor.py` | KG-019 | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-021 | `knowledge/graph/citation_graph.py` | citation_graph.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-022 | `knowledge/graph/concept_graph.py` | concept_graph.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | ADR required | Unit + integration | Deferred until approved |
| MCAP-023 | `knowledge/indexing/citation_index.py` | citation_index.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-024 | `knowledge/indexing/equation_index.py` | equation_index.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-025 | `knowledge/indexing/variable_index.py` | variable_index.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-026 | `knowledge/ingestion/batch_loader.py` | batch loader.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-027 | `knowledge/ingestion/epub_loader.py` | epub loader.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-028 | `knowledge/ingestion/image_loader.py` | image loader.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-029 | `knowledge/ingestion/latex_loader.py` | latex loader.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-030 | `knowledge/ingestion/markitdown_loader.py` | markitdown loader.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-031 | `knowledge/ingestion/ocr_loader.py` | ocr loader.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-032 | `knowledge/models/appendix.py` | Appendix model | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-033 | `knowledge/models/assumption.py` | Assumption | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-034 | `knowledge/models/boundary_condition.py` | Boundary condition | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-035 | `knowledge/models/chapter.py` | Chapter model | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-036 | `knowledge/models/correlation.py` | Correlation | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-037 | `knowledge/models/design_rule.py` | Design rule | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-038 | `knowledge/models/empirical_relation.py` | Empirical relation | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | ADR required | Unit + integration | Deferred until approved |
| MCAP-039 | `knowledge/models/experiment.py` | Experiment | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-040 | `knowledge/models/failure_mode.py` | Failure mode | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-041 | `knowledge/models/glossary.py` | Glossary model | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-042 | `knowledge/models/manufacturing_process.py` | Manufacturing process | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-043 | `knowledge/models/physical_law.py` | Physical law | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-044 | `knowledge/models/process.py` | Process | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-045 | `knowledge/models/property.py` | Property | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-046 | `knowledge/models/section.py` | Section model | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-047 | `knowledge/models/sentence.py` | Sentence model | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | ADR required | Unit + integration | Deferred until approved |
| MCAP-048 | `knowledge/models/simulation.py` | Simulation | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-049 | `knowledge/parsers/appendix_parser.py` | appendix_parser.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-050 | `knowledge/parsers/glossary_parser.py` | glossary_parser.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-051 | `knowledge/parsers/sentence_parser.py` | sentence_parser.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | ADR required | Unit + integration | Deferred until approved |
| MCAP-052 | `knowledge/reasoning/equation_reasoner.py` | equation_reasoner.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-053 | `knowledge/repositories/chapter_repository.py` | chapter repository | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-054 | `knowledge/repositories/component_repository.py` | component repository | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-055 | `knowledge/repositories/constant_repository.py` | constant repository | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-056 | `knowledge/repositories/correlation_repository.py` | correlation repository | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-057 | `knowledge/repositories/design_rule_repository.py` | design_rule repository | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-058 | `knowledge/repositories/equation_repository.py` | equation repository | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-059 | `knowledge/repositories/figure_repository.py` | figure repository | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-060 | `knowledge/repositories/material_repository.py` | material repository | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-061 | `knowledge/repositories/property_repository.py` | property repository | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-062 | `knowledge/repositories/section_repository.py` | section repository | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-063 | `knowledge/repositories/simulation_repository.py` | simulation repository | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-064 | `knowledge/repositories/subsystem_repository.py` | subsystem repository | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-065 | `knowledge/repositories/table_repository.py` | table repository | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-066 | `knowledge/repositories/variable_repository.py` | variable repository | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-067 | `knowledge/search/citation_search.py` | citation_search.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-068 | `knowledge/search/equation_search.py` | equation_search.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-069 | `knowledge/search/variable_search.py` | variable_search.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-070 | `knowledge/utils/text_utils.py` | text_utils.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | ADR required | Unit + integration | Deferred until approved |
| MCAP-071 | `knowledge/validation/ambiguity_detector.py` | ambiguity_detector.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |
| MCAP-072 | `knowledge/validation/citation_validator.py` | citation_validator.py | Frozen Part-3 file absent | See traceability | `None` | File-level gap; capability may be partial | KG-BLOCK-013+ | Unit + integration | Deferred until approved |

---

## Priority Tiers (Proposed — Not Authorized)

### Tier 1 — Architecture decisions (F)

- `knowledge/models/sentence.py` — sentence granularity vs paragraph-only parsing
- `knowledge/models/empirical_relation.py` — relation to correlation/physical_law
- `knowledge/graph/concept_graph.py` — concept graph vs engineering graph
- `knowledge/utils/text_utils.py` — shared text helpers scope
- `knowledge/parsers/sentence_parser.py` — depends on sentence model ADR

### Tier 2 — High-value missing (E, grouped)

- **Exporters (7):** `knowledge/exporters/*` — export pipeline for engineering handoff
- **Entity repositories (15):** `knowledge/repositories/*_repository.py` — persistence layer
- **Format loaders (5):** epub, latex, image, ocr, markitdown
- **Domain extractors (12):** process, simulation, failure_mode, design_rule, etc.

### Tier 3 — Deferred domain models (E)

- Chapter/section/appendix/glossary canonical models
- physical_law, correlation, assumption, boundary_condition, property, process, etc.

**Implementation gate:** CLOSED until ADRs approved.