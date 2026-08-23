# Knowledge File-Level Architecture Reconciliation

**Document ID:** COSMOS-KG-FILE-RECON-MASTER-002
**Date:** 2026-08-23
**Type:** RECONCILIATION ONLY — no code changes authorized
**Authority:** COSMOS Technical Owner Reconciliation Directive

---

## Executive Summary

Reconciliation of **current `knowledge/`** against frozen Part-3 Knowledge Folder Architecture.
Every frozen architectural `.py` file receives exactly one disposition **A–F**.
Current-only files receive **G** or **H** in the reverse inventory.

| Certification Metric | Result |
|---------------------|--------|
| FILE-LEVEL EXACT MATCH (A) | **12 / 175 = 6.9%** |
| CAPABILITY ADDRESSED (A+B+C+D) | **103 / 175 = 58.9%** |
| MISSING REQUIRED (E) | **67** |
| MISSING DECISION REQUIRED (F) | **5** |
| Current implementation files | **148** |
| Regression baseline | **1219 passed, 5 skipped** |
| BLOCK-001→011 | **FROZEN — unchanged** |
| BLOCK-012 | **READY FOR HUMAN FREEZE APPROVAL** |
| FILE-LEVEL CERTIFIED 100% | **NO** |

**Conclusion:** Capability-faithful KG-001→051 reference implementation with deliberate structural refinement.
Not superficial path matching. Formal approval required for deviations before certification.

---

## Disposition Summary

| Code | Label | Count | % of 175 |
|------|-------|-------|----------|
| A | EXACT_MATCH | 12 | 6.9% |
| B | RELOCATED | 27 | 15.4% |
| C | CONSOLIDATED | 48 | 27.4% |
| D | SUPERSEDED | 16 | 9.1% |
| E | MISSING_REQUIRED | 67 | 38.3% |
| F | MISSING_DECISION_REQUIRED | 5 | 2.9% |

---

## A — EXACT_MATCH (12)

```text
knowledge/__init__.py
knowledge/models/constant.py
knowledge/models/dimension.py
knowledge/models/document.py
knowledge/models/engineering_domain.py
knowledge/models/equation.py
knowledge/models/material.py
knowledge/models/quantity.py
knowledge/models/reference.py
knowledge/models/subsystem.py
knowledge/models/unit.py
knowledge/models/variable.py
```

Protected frozen interfaces: `quantity.py`, `unit.py`, `dimension.py` (BLOCK-007+).

---

## B — RELOCATED (27)

Frozen path preserved capability at a different module path. See traceability matrix for symbol-level mapping.

Representative examples:

- `knowledge/extraction/extraction_pipeline.py` → `knowledge/extraction/w4/pipeline.py` (`extract_document; W4ExtractionPipeline`)
- `knowledge/extraction/quantity_extractor.py` → `knowledge/extraction/w4/quantities.py` (`extract_quantities`)
- `knowledge/graph/relationship_builder.py` → `knowledge/graph/construction.py` (`GraphConstructor + extraction/w4/relationships.py`)
- `knowledge/indexing/graph_index.py` → `knowledge/indexing/w7/graph_index.py` (`InMemoryGraphIndex`)
- `knowledge/indexing/keyword_index.py` → `knowledge/indexing/lexical.py` (`InMemoryLexicalIndex`)
- `knowledge/indexing/semantic_index.py` → `knowledge/indexing/semantic.py + w7/vector.py` (`InMemorySemanticIndex; InMemoryVectorIndex`)
- `knowledge/ingestion/docx_loader.py` → `knowledge/ingestion_adapters/docx.py` (`DocxIngestionAdapter.ingest`)
- `knowledge/ingestion/html_loader.py` → `knowledge/ingestion_adapters/html.py` (`HtmlIngestionAdapter.ingest`)
- `knowledge/ingestion/markdown_loader.py` → `knowledge/ingestion_adapters/html.py` (`MarkdownIngestionAdapter.ingest`)
- `knowledge/ingestion/pdf_loader.py` → `knowledge/ingestion_adapters/pdf.py` (`PdfIngestionAdapter.ingest`)
- `knowledge/ontology/ontology_manager.py` → `knowledge/ontology/registry.py` (`OntologyRegistry`)
- `knowledge/parsers/figure_parser.py` → `knowledge/parsers/w3/figures.py` (`extract_figures`)
- `knowledge/parsers/table_parser.py` → `knowledge/parsers/w3/tables.py` (`extract_tables`)
- `knowledge/pipelines/extraction_pipeline.py.py` → `knowledge/extraction/w4/pipeline.py` (`extract_document`)
- `knowledge/pipelines/validation_pipeline.py.py` → `knowledge/validation/engine.py` (`ValidationEngine.validate_context`)
- `knowledge/reasoning/engineering_reasoner.py` → `knowledge/reasoning/reasoner.py + w10/reasoner.py` (`ProvenanceAwareReasoner; W10ProvenanceAwareReasoner`)
- `knowledge/repositories/document_repository.py` → `knowledge/repository/repository.py` (`DocumentRepository`)
- `knowledge/search/graph_search.py` → `knowledge/search/w8/graph_search.py` (`GraphSearchEngine`)
- `knowledge/search/hybrid_search.py` → `knowledge/search/w8/hybrid.py` (`HybridSearchEngine`)
- `knowledge/search/keyword_search.py` → `knowledge/search/w8/keyword.py` (`KeywordSearchEngine`)
- `knowledge/search/search_engine.py` → `knowledge/search/engine.py` (`KnowledgeSearchEngine`)
- `knowledge/search/semantic_search.py` → `knowledge/search/w8/semantic.py` (`SemanticVectorSearchEngine`)
- `knowledge/utils/hashing.py` → `knowledge/source/integrity.py` (`sha256_text_digest; sha256_bytes_digest`)
- `knowledge/utils/markdown_utils.py` → `knowledge/ingestion_adapters/html.py` (`Markdown normalization`)
- `knowledge/validation/consistency_validator.py` → `knowledge/validation/conflicts.py` (`detect_conflicts`)
- `knowledge/validation/duplicate_detector.py` → `knowledge/validation/duplicates.py` (`detect_duplicates`)
- `knowledge/validation/ontology_validator.py` → `knowledge/ontology/validation.py` (`validate_taxonomy_edge`)

---

## C — CONSOLIDATED (48)

- `knowledge/extraction/component_extractor.py` → `knowledge/extraction/w4/entities.py` (`extract_entities`)
- `knowledge/extraction/constant_extractor.py` → `knowledge/extraction/w4/entities.py` (`extract_entities`)
- `knowledge/extraction/dimension_extractor.py` → `knowledge/extraction/w4/entities.py` (`extract_entities`)
- `knowledge/extraction/engineering_domain_extractor.py` → `knowledge/extraction/w4/entities.py` (`extract_entities`)
- `knowledge/extraction/equation_extractor.py` → `knowledge/extraction/w4/equations.py` (`extract_equation_candidates`)
- `knowledge/extraction/material_extractor.py` → `knowledge/extraction/w4/entities.py` (`extract_entities`)
- `knowledge/extraction/subsystem_extractor.py` → `knowledge/extraction/w4/entities.py` (`extract_entities`)
- `knowledge/extraction/unit_extractor.py` → `knowledge/extraction/w4/entities.py` (`extract_entities`)
- `knowledge/extraction/variable_extractor.py` → `knowledge/extraction/w4/entities.py` (`extract_entities`)
- `knowledge/graph/dependency_graph.py` → `knowledge/graph/query.py` (`GraphQueryService.traverse`)
- `knowledge/graph/engineering_graph.py` → `knowledge/graph/construction.py` (`GraphConstructor`)
- `knowledge/graph/equation_graph.py` → `knowledge/graph/construction.py` (`GraphConstructor`)
- `knowledge/graph/graph_manager.py` → `knowledge/graph/construction.py + query.py` (`GraphConstructor.construct; GraphQueryService`)
- `knowledge/graph/variable_graph.py` → `knowledge/graph/construction.py` (`GraphConstructor`)
- `knowledge/indexing/index_manager.py` → `knowledge/indexing/builder.py + w7/bundle.py` (`KnowledgeIndexBuilder.build; W7IndexBuilder.build`)
- `knowledge/ingestion/ingestion_pipeline.py` → `knowledge/ingestion_adapters/registry.py` (`IngestionOrchestrator`)
- `knowledge/ingestion/metadata_loader.py` → `knowledge/ingestion/models.py` (`IngestionResult`)
- `knowledge/models/citation.py` → `knowledge/parsers/w3/models.py` (`ParsedCitation`)
- `knowledge/models/component.py` → `knowledge/graph/entity.py` (`CanonicalEntityType`)
- `knowledge/models/figure.py` → `knowledge/parsers/w3/models.py` (`ParsedFigure`)
- `knowledge/models/metadata.py` → `knowledge/ingestion/models.py` (`IngestionResult`)
- `knowledge/models/ontology_edge.py` → `knowledge/ontology/models.py` (`TaxonomyEdge`)
- `knowledge/models/ontology_node.py` → `knowledge/ontology/models.py` (`OntologyTerm`)
- `knowledge/models/paragraph.py` → `knowledge/parsers/w3/models.py` (`ParsedParagraph`)
- `knowledge/models/table.py` → `knowledge/parsers/w3/models.py` (`ParsedTable`)
- `knowledge/ontology/engineering_domains.py` → `knowledge/ontology/registry.py + ontology/models.py` (`OntologyRegistry; EngineeringDomain taxonomy`)
- `knowledge/parsers/bibliography_parser.py` → `knowledge/parsers/w3/references.py` (`extract_references`)
- `knowledge/parsers/chapter_parser.py` → `knowledge/parsers/w3/structure.py` (`parse_document_structure`)
- `knowledge/parsers/citation_parser.py` → `knowledge/parsers/w3/references.py` (`extract_citations`)
- `knowledge/parsers/document_parser.py` → `knowledge/parsers/w3/pipeline.py` (`parse_document`)
- `knowledge/parsers/heading_parser.py` → `knowledge/parsers/w3/structure.py` (`parse_document_structure`)
- `knowledge/parsers/metadata_parser.py` → `knowledge/parsers/w3/content.py` (`ParseContext`)
- `knowledge/parsers/paragraph_parser.py` → `knowledge/parsers/w3/structure.py` (`parse_document_structure`)
- `knowledge/parsers/section_parser.py` → `knowledge/parsers/w3/structure.py` (`parse_document_structure`)
- `knowledge/pipelines/document_pipeline.py.py` → `tests/integration_tests/kg_block012/helpers/pipeline.py` (`run_full_pipeline`)
- `knowledge/pipelines/indexing_pipeline.py.py` → `knowledge/indexing/w7/bundle.py` (`W7IndexBuilder.build`)
- `knowledge/pipelines/knowledge_pipeline.py.py` → `tests/integration_tests/kg_block012/helpers/pipeline.py` (`run_full_pipeline`)
- `knowledge/reasoning/consistency_reasoner.py` → `knowledge/validation/conflicts.py + w10/classification.py` (`detect_conflicts; classify_evidence_item`)
- `knowledge/reasoning/dependency_reasoner.py` → `knowledge/reasoning/w10/chains.py` (`EvidenceChainBuilder`)
- `knowledge/reasoning/traceability_engine.py` → `knowledge/reasoning/w10/chains.py` (`EvidenceChainBuilder.build_chain`)
- `knowledge/repositories/repository_manager.py` → `knowledge/repository/source_registry.py` (`SourceRegistry`)
- `knowledge/utils/equation_utils.py` → `knowledge/parsers/w3/equations.py + extraction/w4/equations.py` (`extract_equations; extract_equation_candidates`)
- `knowledge/utils/graph_utils.py` → `knowledge/graph/serialization.py + query.py` (`canonical_graph_record_digest; GraphQueryService`)
- `knowledge/utils/parsing_utils.py` → `knowledge/parsers/w3/structure.py + ingestion_adapters/normalize.py` (`parse_document_structure; normalize`)
- `knowledge/validation/dimension_validator.py` → `knowledge/validation/units.py` (`validate_units`)
- `knowledge/validation/equation_validator.py` → `knowledge/validation/schema.py` (`validate_schema`)
- `knowledge/validation/source_validator.py` → `knowledge/validation/provenance.py + source/integrity.py` (`validate_provenance; verify_digest`)
- `knowledge/validation/unit_validator.py` → `knowledge/validation/units.py` (`validate_units`)

---

## D — SUPERSEDED (16)

- `knowledge/ontology/aerospace.py` → `knowledge/ontology/registry.py` — Static module superseded by registry
- `knowledge/ontology/combustion.py` → `knowledge/ontology/registry.py` — Static module superseded by registry
- `knowledge/ontology/compressible_flow.py` → `knowledge/ontology/registry.py` — Static module superseded by registry
- `knowledge/ontology/controls.py` → `knowledge/ontology/registry.py` — Static module superseded by registry
- `knowledge/ontology/cryogenics.py` → `knowledge/ontology/registry.py` — Static module superseded by registry
- `knowledge/ontology/fluid_mechanics.py` → `knowledge/ontology/registry.py` — Static module superseded by registry
- `knowledge/ontology/heat_transfer.py` → `knowledge/ontology/registry.py` — Static module superseded by registry
- `knowledge/ontology/manufacturing.py` → `knowledge/ontology/registry.py` — Static module superseded by registry
- `knowledge/ontology/materials.py` → `knowledge/ontology/registry.py` — Static module superseded by registry
- `knowledge/ontology/optimization.py` → `knowledge/ontology/registry.py` — Static module superseded by registry
- `knowledge/ontology/propulsion.py` → `knowledge/ontology/registry.py` — Static module superseded by registry
- `knowledge/ontology/structures.py` → `knowledge/ontology/registry.py` — Static module superseded by registry
- `knowledge/ontology/thermochemistry.py` → `knowledge/ontology/registry.py` — Static module superseded by registry
- `knowledge/ontology/thermodynamics.py` → `knowledge/ontology/registry.py` — Static module superseded by registry
- `knowledge/reasoning/recommendation_engine.py` → `knowledge/interface/rag.py` — Superseded by controlled RAG
- `knowledge/utils/logging_utils.py` → `core project logging (outside knowledge/)` — Superseded by project-level logging

---

## E — MISSING_REQUIRED (67)

- `knowledge/exporters/database_exporter.py` — Export (—)
- `knowledge/exporters/graph_exporter.py` — Export (—)
- `knowledge/exporters/html_exporter.py` — Export (—)
- `knowledge/exporters/json_exporter.py` — Export (—)
- `knowledge/exporters/latex_exporter.py` — Export (—)
- `knowledge/exporters/markdown_exporter.py` — Export (—)
- `knowledge/exporters/yaml_exporter.py` — Export (—)
- `knowledge/extraction/abbreviation_extractor.py` — KG-019 (—)
- `knowledge/extraction/assumption_extractor.py` — KG-019 (—)
- `knowledge/extraction/boundary_condition_extractor.py` — KG-019 (—)
- `knowledge/extraction/correlation_extractor.py` — KG-019 (—)
- `knowledge/extraction/design_rule_extractor.py` — KG-019 (—)
- `knowledge/extraction/experiment_extractor.py` — KG-019 (—)
- `knowledge/extraction/failure_mode_extractor.py` — KG-019 (—)
- `knowledge/extraction/glossary_extractor.py` — KG-019 (—)
- `knowledge/extraction/manufacturing_extractor.py` — KG-019 (—)
- `knowledge/extraction/physical_law_extractor.py` — KG-019 (—)
- `knowledge/extraction/process_extractor.py` — KG-019 (—)
- `knowledge/extraction/property_extractor.py` — KG-019 (—)
- `knowledge/extraction/simulation_extractor.py` — KG-019 (—)
- `knowledge/graph/citation_graph.py` — citation_graph.py (KG-038)
- `knowledge/indexing/citation_index.py` — citation_index.py (KG-033)
- `knowledge/indexing/equation_index.py` — equation_index.py (KG-033)
- `knowledge/indexing/variable_index.py` — variable_index.py (KG-033)
- `knowledge/ingestion/batch_loader.py` — batch loader.py (KG-013)
- `knowledge/ingestion/epub_loader.py` — epub loader.py (KG-010)
- `knowledge/ingestion/image_loader.py` — image loader.py (KG-016)
- `knowledge/ingestion/latex_loader.py` — latex loader.py (KG-012)
- `knowledge/ingestion/markitdown_loader.py` — markitdown loader.py (KG-009)
- `knowledge/ingestion/ocr_loader.py` — ocr loader.py (KG-016)
- `knowledge/models/appendix.py` — Appendix model (KG-014)
- `knowledge/models/assumption.py` — Assumption (KG-022)
- `knowledge/models/boundary_condition.py` — Boundary condition (KG-019+)
- `knowledge/models/chapter.py` — Chapter model (KG-014)
- `knowledge/models/correlation.py` — Correlation (KG-019+)
- `knowledge/models/design_rule.py` — Design rule (KG-019)
- `knowledge/models/experiment.py` — Experiment (KG-019)
- `knowledge/models/failure_mode.py` — Failure mode (KG-019)
- `knowledge/models/glossary.py` — Glossary model (KG-014)
- `knowledge/models/manufacturing_process.py` — Manufacturing process (KG-019)
- `knowledge/models/physical_law.py` — Physical law (KG-019+)
- `knowledge/models/process.py` — Process (KG-019)
- `knowledge/models/property.py` — Property (KG-019)
- `knowledge/models/section.py` — Section model (KG-014)
- `knowledge/models/simulation.py` — Simulation (KG-019)
- `knowledge/parsers/appendix_parser.py` — appendix_parser.py (KG-014)
- `knowledge/parsers/glossary_parser.py` — glossary_parser.py (KG-014)
- `knowledge/reasoning/equation_reasoner.py` — equation_reasoner.py (KG-045)
- `knowledge/repositories/chapter_repository.py` — chapter repository (—)
- `knowledge/repositories/component_repository.py` — component repository (—)
- `knowledge/repositories/constant_repository.py` — constant repository (—)
- `knowledge/repositories/correlation_repository.py` — correlation repository (—)
- `knowledge/repositories/design_rule_repository.py` — design_rule repository (—)
- `knowledge/repositories/equation_repository.py` — equation repository (—)
- `knowledge/repositories/figure_repository.py` — figure repository (—)
- `knowledge/repositories/material_repository.py` — material repository (—)
- `knowledge/repositories/property_repository.py` — property repository (—)
- `knowledge/repositories/section_repository.py` — section repository (—)
- `knowledge/repositories/simulation_repository.py` — simulation repository (—)
- `knowledge/repositories/subsystem_repository.py` — subsystem repository (—)
- `knowledge/repositories/table_repository.py` — table repository (—)
- `knowledge/repositories/variable_repository.py` — variable repository (—)
- `knowledge/search/citation_search.py` — citation_search.py (KG-038)
- `knowledge/search/equation_search.py` — equation_search.py (KG-036)
- `knowledge/search/variable_search.py` — variable_search.py (KG-036)
- `knowledge/validation/ambiguity_detector.py` — ambiguity_detector.py (KG-044)
- `knowledge/validation/citation_validator.py` — citation_validator.py (KG-041)

---

## F — MISSING_DECISION_REQUIRED (5)

- `knowledge/graph/concept_graph.py` — Graph layer
- `knowledge/models/empirical_relation.py` — Model disposition F
- `knowledge/models/sentence.py` — Model disposition F
- `knowledge/parsers/sentence_parser.py` — Parser layer
- `knowledge/utils/text_utils.py` — Utils

---

## G/H — Current Extra Files

See `knowledge_file_level_traceability_matrix.md` reverse inventory.
G = justified KG evolution (w3/w4/w7/w8/w10/interface, source vault, ingestion_adapters).
H = review required (non-frozen paths that implement frozen capabilities).

---

## Certification Blockers

1. 67 frozen files E — no implementation at expected path
2. 5 frozen files F — architecture decision required before implementation
3. Deviations in deviation register lack formal approval
4. Compatibility facades not yet implemented (plan only)
5. Exporters package entirely missing
6. Entity repositories (plural) deferred

---

## Related Documents

| # | Document |
|---|----------|
| 1 | `knowledge_file_level_traceability_matrix.md` |
| 2 | `knowledge_models_gap_analysis.md` |
| 3 | `knowledge_architecture_deviation_register.md` |
| 4 | `knowledge_rag_alignment_audit.md` |
| 5 | `knowledge_next_development_plan.md` |
| 6 | `knowledge_architecture_decision_register.md` |
| 7 | `knowledge_missing_capability_register.md` |
| 8 | `knowledge_compatibility_layer_plan.md` |
| 9 | `knowledge_certification_readiness_report.md` |

```text
FINAL CERTIFICATION: NOT FILE-LEVEL CERTIFIED 100%
CODE CHANGES: NONE
IMPLEMENTATION GATE: CLOSED (reconciliation phase only)
```