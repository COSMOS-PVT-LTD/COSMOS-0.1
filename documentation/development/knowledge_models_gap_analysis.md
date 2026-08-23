# Knowledge Models Gap Analysis

**Document ID:** COSMOS-KG-MODELS-GAP-002
**Date:** 2026-08-23
**Type:** RECONCILIATION ONLY
**Frozen source:** `documentation/COSMOS_0.1_FREEZED.md` Part 3 — `knowledge/models/`

## Summary

| Metric | Count |
|--------|-------|
| Models expected (frozen) | **36** |
| A EXACT_MATCH | **11** |
| C CONSOLIDATED | **8** |
| E MISSING_REQUIRED | **15** |
| F MISSING_DECISION_REQUIRED | **2** |

**Rule applied:** No duplicate Quantity/Unit/Dimension/Entity/Graph models created for filename matching.

---

## 36-Model Reconciliation

| # | Frozen Path | Disp | Current Path | Symbol(s) | Equivalent? | Create? | Duplicate Risk | KG | Test |
|---|-------------|------|--------------|-----------|-------------|---------|----------------|-----|------|
| 1 | `appendix.py` | E | `—` | `—` | NO | YES (future block) | LOW | KG-014 | NO |
| 2 | `assumption.py` | E | `—` | `—` | NO | YES (future block) | LOW | KG-022 | NO |
| 3 | `boundary_condition.py` | E | `—` | `—` | NO | YES (future block) | LOW | KG-019+ | NO |
| 4 | `chapter.py` | E | `—` | `—` | NO | YES (future block) | LOW | KG-014 | NO |
| 5 | `citation.py` | C | `knowledge/parsers/w3/models.py` | `ParsedCitation` | YES | NO | NONE | KG-018 | test_w3_parsing.py |
| 6 | `component.py` | C | `knowledge/graph/entity.py` | `CanonicalEntityType` | YES | NO | NONE | KG-019 | NO |
| 7 | `constant.py` | A | `knowledge/models/constant.py` | `knowledge.models.constant.Constant` | YES | NO | NONE | KG-020 | test_constant.py |
| 8 | `correlation.py` | E | `—` | `—` | NO | YES (future block) | LOW | KG-019+ | NO |
| 9 | `design_rule.py` | E | `—` | `—` | NO | YES (future block) | LOW | KG-019 | NO |
| 10 | `dimension.py` | A | `knowledge/models/dimension.py` | `knowledge.models.dimension.Dimension` | YES | NO | NONE | KG-020/042 | test_dimension.py [FROZEN] |
| 11 | `document.py` | A | `knowledge/models/document.py` | `knowledge.models.document.Document` | YES | NO | NONE | KG-014 | test_repository.py |
| 12 | `empirical_relation.py` | F | `—` | `—` | NO | DECISION | — | — | NO |
| 13 | `engineering_domain.py` | A | `knowledge/models/engineering_domain.py` | `knowledge.models.engineering_domain.EngineeringDomain` | YES | NO | NONE | KG-026 | test_ontology.py |
| 14 | `equation.py` | A | `knowledge/models/equation.py` | `knowledge.models.equation.Equation` | YES | NO | NONE | KG-021 | test_extraction.py |
| 15 | `experiment.py` | E | `—` | `—` | NO | YES (future block) | LOW | KG-019 | NO |
| 16 | `failure_mode.py` | E | `—` | `—` | NO | YES (future block) | LOW | KG-019 | NO |
| 17 | `figure.py` | C | `knowledge/parsers/w3/models.py` | `ParsedFigure` | YES | NO | NONE | KG-016 | test_w3_parsing.py |
| 18 | `glossary.py` | E | `—` | `—` | NO | YES (future block) | LOW | KG-014 | NO |
| 19 | `manufacturing_process.py` | E | `—` | `—` | NO | YES (future block) | LOW | KG-019 | NO |
| 20 | `material.py` | A | `knowledge/models/material.py` | `knowledge.models.material.Material` | YES | NO | NONE | KG-019 | test_material.py |
| 21 | `metadata.py` | C | `knowledge/ingestion/models.py` | `IngestionResult` | YES | NO | NONE | KG-009 | NO |
| 22 | `ontology_edge.py` | C | `knowledge/ontology/models.py` | `TaxonomyEdge` | YES | NO | NONE | KG-026 | test_w5_ontology.py |
| 23 | `ontology_node.py` | C | `knowledge/ontology/models.py` | `OntologyTerm` | YES | NO | NONE | KG-024 | test_w5_ontology.py |
| 24 | `paragraph.py` | C | `knowledge/parsers/w3/models.py` | `ParsedParagraph` | YES | NO | NONE | KG-014 | test_w3_parsing.py |
| 25 | `physical_law.py` | E | `—` | `—` | NO | YES (future block) | LOW | KG-019+ | NO |
| 26 | `process.py` | E | `—` | `—` | NO | YES (future block) | LOW | KG-019 | NO |
| 27 | `property.py` | E | `—` | `—` | NO | YES (future block) | LOW | KG-019 | NO |
| 28 | `quantity.py` | A | `knowledge/models/quantity.py` | `knowledge.models.quantity.Quantity` | YES | NO | NONE | KG-020/042 | test_quantity.py [FROZEN] |
| 29 | `reference.py` | A | `knowledge/models/reference.py` | `knowledge.models.reference.Reference` | YES | NO | NONE | KG-018 | INDIRECT |
| 30 | `section.py` | E | `—` | `—` | NO | YES (future block) | LOW | KG-014 | NO |
| 31 | `sentence.py` | F | `—` | `—` | NO | DECISION | — | KG-014 | NO |
| 32 | `simulation.py` | E | `—` | `—` | NO | YES (future block) | LOW | KG-019 | NO |
| 33 | `subsystem.py` | A | `knowledge/models/subsystem.py` | `knowledge.models.subsystem.Subsystem` | YES | NO | NONE | KG-019 | test_material.py |
| 34 | `table.py` | C | `knowledge/parsers/w3/models.py` | `ParsedTable` | YES | NO | NONE | KG-015 | test_w3_parsing.py |
| 35 | `unit.py` | A | `knowledge/models/unit.py` | `knowledge.models.unit.Unit` | YES | NO | NONE | KG-020/042 | test_unit.py [FROZEN] |
| 36 | `variable.py` | A | `knowledge/models/variable.py` | `knowledge.models.variable.Variable` | YES | NO | NONE | KG-021 | test_extraction.py |

---

## Consolidation Register (Formal)

| Frozen Model | Canonical Location | Symbol | Justification |
|--------------|-------------------|--------|---------------|
| `paragraph.py` | `knowledge/parsers/w3/models.py` | `ParsedParagraph` | W3 parse artifact, not domain entity |
| `figure.py` | `knowledge/parsers/w3/models.py` | `ParsedFigure` | W3 figure extraction model |
| `table.py` | `knowledge/parsers/w3/models.py` | `ParsedTable` | W3 table extraction model |
| `citation.py` | `knowledge/parsers/w3/models.py` | `ParsedCitation` | Citation parse artifact |
| `component.py` | `knowledge/graph/entity.py` | `CanonicalEntityType` | Graph entity typing |
| `ontology_node.py` | `knowledge/ontology/models.py` | `OntologyTerm` | W5 ontology term |
| `ontology_edge.py` | `knowledge/ontology/models.py` | `TaxonomyEdge` | W5 taxonomy edge |
| `metadata.py` | `knowledge/ingestion/models.py` | `IngestionResult` | Distributed metadata at ingestion boundary |

---

## Protected Models (DO NOT MODIFY)

| File | Protection |
|------|------------|
| `knowledge/models/quantity.py` | FROZEN BLOCK-007+ |
| `knowledge/models/unit.py` | FROZEN BLOCK-007+ |
| `knowledge/models/dimension.py` | FROZEN BLOCK-007+ |