# Knowledge Architecture Decision Gate Table

**Document ID:** COSMOS-KG-DECISION-GATE-001
**Date:** 2026-08-23
**Status:** PENDING TECHNICAL OWNER APPROVAL
**Authority:** Architecture Decision Gate Directive

> No implementation authorized until this register is approved.

## Summary

| Disposition Category | Items |
|---------------------|-------|
| E MISSING_REQUIRED | 67 |
| F MISSING_DECISION_REQUIRED | 5 |
| B RELOCATED | 27 |
| C CONSOLIDATED | 48 |
| D SUPERSEDED | 16 |
| H EXTRA_REVIEW_REQUIRED | 36 |
| **TOTAL** | **199** |

### Recommended Actions (pending approval)

| Action | Count |
|--------|-------|
| CONSOLIDATE | 73 |
| APPROVE | 36 |
| IMPLEMENT | 31 |
| SUPERSEDE | 18 |
| RELOCATE | 14 |
| REMOVE FROM ARCHITECTURE | 14 |
| COMPATIBILITY FACADE | 13 |

---

## Decision Table

| ID | Disp | Path / Item | Current / Canonical | Symbol(s) | **Recommended Action** | Rationale | Owner Decision |
|----|------|-------------|---------------------|-----------|------------------------|-----------|----------------|
| DG-001 | E | `knowledge/exporters/database_exporter.py` | `—` | `—` | **IMPLEMENT** | Export handoff required; defer to KG-BLOCK-014 | PENDING |
| DG-002 | E | `knowledge/exporters/graph_exporter.py` | `—` | `—` | **IMPLEMENT** | Export handoff required; defer to KG-BLOCK-014 | PENDING |
| DG-003 | E | `knowledge/exporters/html_exporter.py` | `—` | `—` | **IMPLEMENT** | Export handoff required; defer to KG-BLOCK-014 | PENDING |
| DG-004 | E | `knowledge/exporters/json_exporter.py` | `—` | `—` | **IMPLEMENT** | Export handoff required; defer to KG-BLOCK-014 | PENDING |
| DG-005 | E | `knowledge/exporters/latex_exporter.py` | `—` | `—` | **IMPLEMENT** | Export handoff required; defer to KG-BLOCK-014 | PENDING |
| DG-006 | E | `knowledge/exporters/markdown_exporter.py` | `—` | `—` | **IMPLEMENT** | Export handoff required; defer to KG-BLOCK-014 | PENDING |
| DG-007 | E | `knowledge/exporters/yaml_exporter.py` | `—` | `—` | **IMPLEMENT** | Export handoff required; defer to KG-BLOCK-014 | PENDING |
| DG-008 | E | `knowledge/extraction/abbreviation_extractor.py` | `—` | `—` | **IMPLEMENT** | Parser-level capability not covered by W3/W4 generic paths | PENDING |
| DG-009 | E | `knowledge/extraction/assumption_extractor.py` | `—` | `—` | **CONSOLIDATE** | Extend W4 entity/claim pipeline; no per-entity file duplication | PENDING |
| DG-010 | E | `knowledge/extraction/boundary_condition_extractor.py` | `—` | `—` | **CONSOLIDATE** | Extend W4 entity/claim pipeline; no per-entity file duplication | PENDING |
| DG-011 | C | `knowledge/extraction/component_extractor.py` | `knowledge/extraction/w4/entities.py` | `extract_entities` | **CONSOLIDATE** | Canonical: `knowledge/extraction/w4/entities.py` (`extract_entities`) | PENDING |
| DG-012 | C | `knowledge/extraction/constant_extractor.py` | `knowledge/extraction/w4/entities.py` | `extract_entities` | **CONSOLIDATE** | Canonical: `knowledge/extraction/w4/entities.py` (`extract_entities`) | PENDING |
| DG-013 | E | `knowledge/extraction/correlation_extractor.py` | `—` | `—` | **CONSOLIDATE** | Extend W4 entity/claim pipeline; no per-entity file duplication | PENDING |
| DG-014 | E | `knowledge/extraction/design_rule_extractor.py` | `—` | `—` | **CONSOLIDATE** | Extend W4 entity/claim pipeline; no per-entity file duplication | PENDING |
| DG-015 | C | `knowledge/extraction/dimension_extractor.py` | `knowledge/extraction/w4/entities.py` | `extract_entities` | **CONSOLIDATE** | Canonical: `knowledge/extraction/w4/entities.py` (`extract_entities`) | PENDING |
| DG-016 | C | `knowledge/extraction/engineering_domain_extractor.py` | `knowledge/extraction/w4/entities.py` | `extract_entities` | **CONSOLIDATE** | Canonical: `knowledge/extraction/w4/entities.py` (`extract_entities`) | PENDING |
| DG-017 | C | `knowledge/extraction/equation_extractor.py` | `knowledge/extraction/w4/equations.py` | `extract_equation_candidates` | **CONSOLIDATE** | Canonical: `knowledge/extraction/w4/equations.py` (`extract_equation_candidates`) | PENDING |
| DG-018 | E | `knowledge/extraction/experiment_extractor.py` | `—` | `—` | **CONSOLIDATE** | Extend W4 entity/claim pipeline; no per-entity file duplication | PENDING |
| DG-019 | B | `knowledge/extraction/extraction_pipeline.py` | `knowledge/extraction/w4/pipeline.py` | `extract_document; W4ExtractionPipeline` | **RELOCATE** | Accept `knowledge/extraction/w4/pipeline.py` as canonical; frozen path abandoned | PENDING |
| DG-020 | E | `knowledge/extraction/failure_mode_extractor.py` | `—` | `—` | **CONSOLIDATE** | Extend W4 entity/claim pipeline; no per-entity file duplication | PENDING |
| DG-021 | E | `knowledge/extraction/glossary_extractor.py` | `—` | `—` | **IMPLEMENT** | Parser-level capability not covered by W3/W4 generic paths | PENDING |
| DG-022 | E | `knowledge/extraction/manufacturing_extractor.py` | `—` | `—` | **CONSOLIDATE** | Extend W4 entity/claim pipeline; no per-entity file duplication | PENDING |
| DG-023 | C | `knowledge/extraction/material_extractor.py` | `knowledge/extraction/w4/entities.py` | `extract_entities` | **CONSOLIDATE** | Canonical: `knowledge/extraction/w4/entities.py` (`extract_entities`) | PENDING |
| DG-024 | E | `knowledge/extraction/physical_law_extractor.py` | `—` | `—` | **CONSOLIDATE** | Extend W4 entity/claim pipeline; no per-entity file duplication | PENDING |
| DG-025 | E | `knowledge/extraction/process_extractor.py` | `—` | `—` | **CONSOLIDATE** | Extend W4 entity/claim pipeline; no per-entity file duplication | PENDING |
| DG-026 | E | `knowledge/extraction/property_extractor.py` | `—` | `—` | **CONSOLIDATE** | Extend W4 entity/claim pipeline; no per-entity file duplication | PENDING |
| DG-027 | B | `knowledge/extraction/quantity_extractor.py` | `knowledge/extraction/w4/quantities.py` | `extract_quantities` | **RELOCATE** | Accept `knowledge/extraction/w4/quantities.py` as canonical; frozen path abandoned | PENDING |
| DG-028 | E | `knowledge/extraction/simulation_extractor.py` | `—` | `—` | **CONSOLIDATE** | Extend W4 entity/claim pipeline; no per-entity file duplication | PENDING |
| DG-029 | C | `knowledge/extraction/subsystem_extractor.py` | `knowledge/extraction/w4/entities.py` | `extract_entities` | **CONSOLIDATE** | Canonical: `knowledge/extraction/w4/entities.py` (`extract_entities`) | PENDING |
| DG-030 | C | `knowledge/extraction/unit_extractor.py` | `knowledge/extraction/w4/entities.py` | `extract_entities` | **CONSOLIDATE** | Canonical: `knowledge/extraction/w4/entities.py` (`extract_entities`) | PENDING |
| DG-031 | C | `knowledge/extraction/variable_extractor.py` | `knowledge/extraction/w4/entities.py` | `extract_entities` | **CONSOLIDATE** | Canonical: `knowledge/extraction/w4/entities.py` (`extract_entities`) | PENDING |
| DG-032 | E | `knowledge/graph/citation_graph.py` | `—` | `—` | **CONSOLIDATE** | Citation edges in graph/construction + w4 relationships | PENDING |
| DG-033 | F | `knowledge/graph/concept_graph.py` | `—` | `—` | **CONSOLIDATE** | Concept traversal via engineering graph + ontology registry (ADR-007) | PENDING |
| DG-034 | C | `knowledge/graph/dependency_graph.py` | `knowledge/graph/query.py` | `GraphQueryService.traverse` | **CONSOLIDATE** | Canonical: `knowledge/graph/query.py` (`GraphQueryService.traverse`) | PENDING |
| DG-035 | C | `knowledge/graph/engineering_graph.py` | `knowledge/graph/construction.py` | `GraphConstructor` | **CONSOLIDATE** | Canonical: `knowledge/graph/construction.py` (`GraphConstructor`) | PENDING |
| DG-036 | C | `knowledge/graph/equation_graph.py` | `knowledge/graph/construction.py` | `GraphConstructor` | **CONSOLIDATE** | Canonical: `knowledge/graph/construction.py` (`GraphConstructor`) | PENDING |
| DG-037 | C | `knowledge/graph/graph_manager.py` | `knowledge/graph/construction.py + query.py` | `GraphConstructor.construct; GraphQueryService` | **CONSOLIDATE** | Canonical: `knowledge/graph/construction.py + query.py` (`GraphConstructor.construct; GraphQueryService`) | PENDING |
| DG-038 | B | `knowledge/graph/relationship_builder.py` | `knowledge/graph/construction.py` | `GraphConstructor + extraction/w4/relationships.py` | **RELOCATE** | Accept `knowledge/graph/construction.py` as canonical; frozen path abandoned | PENDING |
| DG-039 | C | `knowledge/graph/variable_graph.py` | `knowledge/graph/construction.py` | `GraphConstructor` | **CONSOLIDATE** | Canonical: `knowledge/graph/construction.py` (`GraphConstructor`) | PENDING |
| DG-040 | E | `knowledge/indexing/citation_index.py` | `—` | `—` | **CONSOLIDATE** | Typed facets on lexical/semantic/w7 indexes; no separate index files | PENDING |
| DG-041 | E | `knowledge/indexing/equation_index.py` | `—` | `—` | **CONSOLIDATE** | Typed facets on lexical/semantic/w7 indexes; no separate index files | PENDING |
| DG-042 | B | `knowledge/indexing/graph_index.py` | `knowledge/indexing/w7/graph_index.py` | `InMemoryGraphIndex` | **COMPATIBILITY FACADE** | Canonical: `knowledge/indexing/w7/graph_index.py`; facade preserves frozen import path | PENDING |
| DG-043 | C | `knowledge/indexing/index_manager.py` | `knowledge/indexing/builder.py + w7/bundle.py` | `KnowledgeIndexBuilder.build; W7IndexBuilder.build` | **CONSOLIDATE** | Canonical: `knowledge/indexing/builder.py + w7/bundle.py` (`KnowledgeIndexBuilder.build; W7IndexBuilder.build`) | PENDING |
| DG-044 | B | `knowledge/indexing/keyword_index.py` | `knowledge/indexing/lexical.py` | `InMemoryLexicalIndex` | **COMPATIBILITY FACADE** | Canonical: `knowledge/indexing/lexical.py`; facade preserves frozen import path | PENDING |
| DG-045 | B | `knowledge/indexing/semantic_index.py` | `knowledge/indexing/semantic.py + w7/vector.py` | `InMemorySemanticIndex; InMemoryVectorIndex` | **COMPATIBILITY FACADE** | Canonical: `knowledge/indexing/semantic.py + w7/vector.py`; facade preserves frozen import path | PENDING |
| DG-046 | E | `knowledge/indexing/variable_index.py` | `—` | `—` | **CONSOLIDATE** | Typed facets on lexical/semantic/w7 indexes; no separate index files | PENDING |
| DG-047 | E | `knowledge/ingestion/batch_loader.py` | `—` | `—` | **IMPLEMENT** | Operational batch ingest; KG-BLOCK-013+ | PENDING |
| DG-048 | B | `knowledge/ingestion/docx_loader.py` | `knowledge/ingestion_adapters/docx.py` | `DocxIngestionAdapter.ingest` | **COMPATIBILITY FACADE** | Canonical: `knowledge/ingestion_adapters/docx.py`; facade preserves frozen import path | PENDING |
| DG-049 | E | `knowledge/ingestion/epub_loader.py` | `—` | `—` | **IMPLEMENT** | Format adapter gap; implement in ingestion_adapters when prioritized | PENDING |
| DG-050 | B | `knowledge/ingestion/html_loader.py` | `knowledge/ingestion_adapters/html.py` | `HtmlIngestionAdapter.ingest` | **COMPATIBILITY FACADE** | Canonical: `knowledge/ingestion_adapters/html.py`; facade preserves frozen import path | PENDING |
| DG-051 | E | `knowledge/ingestion/image_loader.py` | `—` | `—` | **IMPLEMENT** | Format adapter gap; implement in ingestion_adapters when prioritized | PENDING |
| DG-052 | C | `knowledge/ingestion/ingestion_pipeline.py` | `knowledge/ingestion_adapters/registry.py` | `IngestionOrchestrator` | **CONSOLIDATE** | Canonical: `knowledge/ingestion_adapters/registry.py` (`IngestionOrchestrator`) | PENDING |
| DG-053 | E | `knowledge/ingestion/latex_loader.py` | `—` | `—` | **IMPLEMENT** | Format adapter gap; implement in ingestion_adapters when prioritized | PENDING |
| DG-054 | B | `knowledge/ingestion/markdown_loader.py` | `knowledge/ingestion_adapters/html.py` | `MarkdownIngestionAdapter.ingest` | **COMPATIBILITY FACADE** | Canonical: `knowledge/ingestion_adapters/html.py`; facade preserves frozen import path | PENDING |
| DG-055 | E | `knowledge/ingestion/markitdown_loader.py` | `—` | `—` | **IMPLEMENT** | Format adapter gap; implement in ingestion_adapters when prioritized | PENDING |
| DG-056 | C | `knowledge/ingestion/metadata_loader.py` | `knowledge/ingestion/models.py` | `IngestionResult` | **CONSOLIDATE** | Canonical: `knowledge/ingestion/models.py` (`IngestionResult`) | PENDING |
| DG-057 | E | `knowledge/ingestion/ocr_loader.py` | `—` | `—` | **IMPLEMENT** | Format adapter gap; implement in ingestion_adapters when prioritized | PENDING |
| DG-058 | B | `knowledge/ingestion/pdf_loader.py` | `knowledge/ingestion_adapters/pdf.py` | `PdfIngestionAdapter.ingest` | **COMPATIBILITY FACADE** | Canonical: `knowledge/ingestion_adapters/pdf.py`; facade preserves frozen import path | PENDING |
| DG-059 | E | `knowledge/models/appendix.py` | `—` | `—` | **CONSOLIDATE** | Structure artifacts belong in parsers/w3 structure models, not domain models/ | PENDING |
| DG-060 | E | `knowledge/models/assumption.py` | `—` | `—` | **IMPLEMENT** | Domain model deferred to KG-BLOCK-017 after ADR-002; graph entities interim | PENDING |
| DG-061 | E | `knowledge/models/boundary_condition.py` | `—` | `—` | **IMPLEMENT** | Domain model deferred to KG-BLOCK-017 after ADR-002; graph entities interim | PENDING |
| DG-062 | E | `knowledge/models/chapter.py` | `—` | `—` | **CONSOLIDATE** | Structure artifacts belong in parsers/w3 structure models, not domain models/ | PENDING |
| DG-063 | C | `knowledge/models/citation.py` | `knowledge/parsers/w3/models.py` | `ParsedCitation` | **CONSOLIDATE** | Canonical: `knowledge/parsers/w3/models.py` (`ParsedCitation`) | PENDING |
| DG-064 | C | `knowledge/models/component.py` | `knowledge/graph/entity.py` | `CanonicalEntityType` | **CONSOLIDATE** | Canonical: `knowledge/graph/entity.py` (`CanonicalEntityType`) | PENDING |
| DG-065 | E | `knowledge/models/correlation.py` | `—` | `—` | **IMPLEMENT** | Domain model deferred to KG-BLOCK-017 after ADR-002; graph entities interim | PENDING |
| DG-066 | E | `knowledge/models/design_rule.py` | `—` | `—` | **IMPLEMENT** | Domain model deferred to KG-BLOCK-017 after ADR-002; graph entities interim | PENDING |
| DG-067 | F | `knowledge/models/empirical_relation.py` | `—` | `—` | **CONSOLIDATE** | Model as graph relationship type; merge with correlation/physical_law taxonomy | PENDING |
| DG-068 | E | `knowledge/models/experiment.py` | `—` | `—` | **IMPLEMENT** | Domain model deferred to KG-BLOCK-017 after ADR-002; graph entities interim | PENDING |
| DG-069 | E | `knowledge/models/failure_mode.py` | `—` | `—` | **IMPLEMENT** | Domain model deferred to KG-BLOCK-017 after ADR-002; graph entities interim | PENDING |
| DG-070 | C | `knowledge/models/figure.py` | `knowledge/parsers/w3/models.py` | `ParsedFigure` | **CONSOLIDATE** | Canonical: `knowledge/parsers/w3/models.py` (`ParsedFigure`) | PENDING |
| DG-071 | E | `knowledge/models/glossary.py` | `—` | `—` | **CONSOLIDATE** | Structure artifacts belong in parsers/w3 structure models, not domain models/ | PENDING |
| DG-072 | E | `knowledge/models/manufacturing_process.py` | `—` | `—` | **IMPLEMENT** | Domain model deferred to KG-BLOCK-017 after ADR-002; graph entities interim | PENDING |
| DG-073 | C | `knowledge/models/metadata.py` | `knowledge/ingestion/models.py` | `IngestionResult` | **CONSOLIDATE** | Canonical: `knowledge/ingestion/models.py` (`IngestionResult`) | PENDING |
| DG-074 | C | `knowledge/models/ontology_edge.py` | `knowledge/ontology/models.py` | `TaxonomyEdge` | **CONSOLIDATE** | Canonical: `knowledge/ontology/models.py` (`TaxonomyEdge`) | PENDING |
| DG-075 | C | `knowledge/models/ontology_node.py` | `knowledge/ontology/models.py` | `OntologyTerm` | **CONSOLIDATE** | Canonical: `knowledge/ontology/models.py` (`OntologyTerm`) | PENDING |
| DG-076 | C | `knowledge/models/paragraph.py` | `knowledge/parsers/w3/models.py` | `ParsedParagraph` | **CONSOLIDATE** | Canonical: `knowledge/parsers/w3/models.py` (`ParsedParagraph`) | PENDING |
| DG-077 | E | `knowledge/models/physical_law.py` | `—` | `—` | **IMPLEMENT** | Domain model deferred to KG-BLOCK-017 after ADR-002; graph entities interim | PENDING |
| DG-078 | E | `knowledge/models/process.py` | `—` | `—` | **IMPLEMENT** | Domain model deferred to KG-BLOCK-017 after ADR-002; graph entities interim | PENDING |
| DG-079 | E | `knowledge/models/property.py` | `—` | `—` | **IMPLEMENT** | Domain model deferred to KG-BLOCK-017 after ADR-002; graph entities interim | PENDING |
| DG-080 | E | `knowledge/models/section.py` | `—` | `—` | **CONSOLIDATE** | Structure artifacts belong in parsers/w3 structure models, not domain models/ | PENDING |
| DG-081 | F | `knowledge/models/sentence.py` | `—` | `—` | **SUPERSEDE** | Paragraph-level W3 parsing sufficient; no sentence domain model | PENDING |
| DG-082 | E | `knowledge/models/simulation.py` | `—` | `—` | **IMPLEMENT** | Domain model deferred to KG-BLOCK-017 after ADR-002; graph entities interim | PENDING |
| DG-083 | C | `knowledge/models/table.py` | `knowledge/parsers/w3/models.py` | `ParsedTable` | **CONSOLIDATE** | Canonical: `knowledge/parsers/w3/models.py` (`ParsedTable`) | PENDING |
| DG-084 | D | `knowledge/ontology/aerospace.py` | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | **SUPERSEDE** | Static module superseded by `knowledge/ontology/registry.py` dynamic registry | PENDING |
| DG-085 | D | `knowledge/ontology/combustion.py` | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | **SUPERSEDE** | Static module superseded by `knowledge/ontology/registry.py` dynamic registry | PENDING |
| DG-086 | D | `knowledge/ontology/compressible_flow.py` | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | **SUPERSEDE** | Static module superseded by `knowledge/ontology/registry.py` dynamic registry | PENDING |
| DG-087 | D | `knowledge/ontology/controls.py` | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | **SUPERSEDE** | Static module superseded by `knowledge/ontology/registry.py` dynamic registry | PENDING |
| DG-088 | D | `knowledge/ontology/cryogenics.py` | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | **SUPERSEDE** | Static module superseded by `knowledge/ontology/registry.py` dynamic registry | PENDING |
| DG-089 | C | `knowledge/ontology/engineering_domains.py` | `knowledge/ontology/registry.py + ontology/models.py` | `OntologyRegistry; EngineeringDomain taxonomy` | **CONSOLIDATE** | Canonical: `knowledge/ontology/registry.py + ontology/models.py` (`OntologyRegistry; EngineeringDomain taxonomy`) | PENDING |
| DG-090 | D | `knowledge/ontology/fluid_mechanics.py` | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | **SUPERSEDE** | Static module superseded by `knowledge/ontology/registry.py` dynamic registry | PENDING |
| DG-091 | D | `knowledge/ontology/heat_transfer.py` | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | **SUPERSEDE** | Static module superseded by `knowledge/ontology/registry.py` dynamic registry | PENDING |
| DG-092 | D | `knowledge/ontology/manufacturing.py` | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | **SUPERSEDE** | Static module superseded by `knowledge/ontology/registry.py` dynamic registry | PENDING |
| DG-093 | D | `knowledge/ontology/materials.py` | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | **SUPERSEDE** | Static module superseded by `knowledge/ontology/registry.py` dynamic registry | PENDING |
| DG-094 | B | `knowledge/ontology/ontology_manager.py` | `knowledge/ontology/registry.py` | `OntologyRegistry` | **COMPATIBILITY FACADE** | Canonical: `knowledge/ontology/registry.py`; facade preserves frozen import path | PENDING |
| DG-095 | D | `knowledge/ontology/optimization.py` | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | **SUPERSEDE** | Static module superseded by `knowledge/ontology/registry.py` dynamic registry | PENDING |
| DG-096 | D | `knowledge/ontology/propulsion.py` | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | **SUPERSEDE** | Static module superseded by `knowledge/ontology/registry.py` dynamic registry | PENDING |
| DG-097 | D | `knowledge/ontology/structures.py` | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | **SUPERSEDE** | Static module superseded by `knowledge/ontology/registry.py` dynamic registry | PENDING |
| DG-098 | D | `knowledge/ontology/thermochemistry.py` | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | **SUPERSEDE** | Static module superseded by `knowledge/ontology/registry.py` dynamic registry | PENDING |
| DG-099 | D | `knowledge/ontology/thermodynamics.py` | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | **SUPERSEDE** | Static module superseded by `knowledge/ontology/registry.py` dynamic registry | PENDING |
| DG-100 | E | `knowledge/parsers/appendix_parser.py` | `—` | `—` | **IMPLEMENT** | Parser-level capability not covered by W3/W4 generic paths | PENDING |
| DG-101 | C | `knowledge/parsers/bibliography_parser.py` | `knowledge/parsers/w3/references.py` | `extract_references` | **CONSOLIDATE** | Canonical: `knowledge/parsers/w3/references.py` (`extract_references`) | PENDING |
| DG-102 | C | `knowledge/parsers/chapter_parser.py` | `knowledge/parsers/w3/structure.py` | `parse_document_structure` | **CONSOLIDATE** | Canonical: `knowledge/parsers/w3/structure.py` (`parse_document_structure`) | PENDING |
| DG-103 | C | `knowledge/parsers/citation_parser.py` | `knowledge/parsers/w3/references.py` | `extract_citations` | **CONSOLIDATE** | Canonical: `knowledge/parsers/w3/references.py` (`extract_citations`) | PENDING |
| DG-104 | C | `knowledge/parsers/document_parser.py` | `knowledge/parsers/w3/pipeline.py` | `parse_document` | **CONSOLIDATE** | Canonical: `knowledge/parsers/w3/pipeline.py` (`parse_document`) | PENDING |
| DG-105 | B | `knowledge/parsers/figure_parser.py` | `knowledge/parsers/w3/figures.py` | `extract_figures` | **RELOCATE** | Accept `knowledge/parsers/w3/figures.py` as canonical; frozen path abandoned | PENDING |
| DG-106 | E | `knowledge/parsers/glossary_parser.py` | `—` | `—` | **IMPLEMENT** | Parser-level capability not covered by W3/W4 generic paths | PENDING |
| DG-107 | C | `knowledge/parsers/heading_parser.py` | `knowledge/parsers/w3/structure.py` | `parse_document_structure` | **CONSOLIDATE** | Canonical: `knowledge/parsers/w3/structure.py` (`parse_document_structure`) | PENDING |
| DG-108 | C | `knowledge/parsers/metadata_parser.py` | `knowledge/parsers/w3/content.py` | `ParseContext` | **CONSOLIDATE** | Canonical: `knowledge/parsers/w3/content.py` (`ParseContext`) | PENDING |
| DG-109 | C | `knowledge/parsers/paragraph_parser.py` | `knowledge/parsers/w3/structure.py` | `parse_document_structure` | **CONSOLIDATE** | Canonical: `knowledge/parsers/w3/structure.py` (`parse_document_structure`) | PENDING |
| DG-110 | C | `knowledge/parsers/section_parser.py` | `knowledge/parsers/w3/structure.py` | `parse_document_structure` | **CONSOLIDATE** | Canonical: `knowledge/parsers/w3/structure.py` (`parse_document_structure`) | PENDING |
| DG-111 | F | `knowledge/parsers/sentence_parser.py` | `—` | `—` | **SUPERSEDE** | Superseded by paragraph/structure parsing unless NLP block authorized | PENDING |
| DG-112 | B | `knowledge/parsers/table_parser.py` | `knowledge/parsers/w3/tables.py` | `extract_tables` | **RELOCATE** | Accept `knowledge/parsers/w3/tables.py` as canonical; frozen path abandoned | PENDING |
| DG-113 | C | `knowledge/pipelines/document_pipeline.py.py` | `tests/integration_tests/kg_block012/helpers/pipeline.py` | `run_full_pipeline` | **CONSOLIDATE** | Canonical: `tests/integration_tests/kg_block012/helpers/pipeline.py` (`run_full_pipeline`) | PENDING |
| DG-114 | B | `knowledge/pipelines/extraction_pipeline.py.py` | `knowledge/extraction/w4/pipeline.py` | `extract_document` | **RELOCATE** | Accept `knowledge/extraction/w4/pipeline.py` as canonical; frozen path abandoned | PENDING |
| DG-115 | C | `knowledge/pipelines/indexing_pipeline.py.py` | `knowledge/indexing/w7/bundle.py` | `W7IndexBuilder.build` | **CONSOLIDATE** | Canonical: `knowledge/indexing/w7/bundle.py` (`W7IndexBuilder.build`) | PENDING |
| DG-116 | C | `knowledge/pipelines/knowledge_pipeline.py.py` | `tests/integration_tests/kg_block012/helpers/pipeline.py` | `run_full_pipeline` | **CONSOLIDATE** | Canonical: `tests/integration_tests/kg_block012/helpers/pipeline.py` (`run_full_pipeline`) | PENDING |
| DG-117 | B | `knowledge/pipelines/validation_pipeline.py.py` | `knowledge/validation/engine.py` | `ValidationEngine.validate_context` | **RELOCATE** | Accept `knowledge/validation/engine.py` as canonical; frozen path abandoned | PENDING |
| DG-118 | C | `knowledge/reasoning/consistency_reasoner.py` | `knowledge/validation/conflicts.py + w10/classification.py` | `detect_conflicts; classify_evidence_item` | **CONSOLIDATE** | Canonical: `knowledge/validation/conflicts.py + w10/classification.py` (`detect_conflicts; classify_evidence_item`) | PENDING |
| DG-119 | C | `knowledge/reasoning/dependency_reasoner.py` | `knowledge/reasoning/w10/chains.py` | `EvidenceChainBuilder` | **CONSOLIDATE** | Canonical: `knowledge/reasoning/w10/chains.py` (`EvidenceChainBuilder`) | PENDING |
| DG-120 | B | `knowledge/reasoning/engineering_reasoner.py` | `knowledge/reasoning/reasoner.py + w10/reasoner.py` | `ProvenanceAwareReasoner; W10ProvenanceAwareReasoner` | **RELOCATE** | Accept `knowledge/reasoning/reasoner.py + w10/reasoner.py` as canonical; frozen path abandoned | PENDING |
| DG-121 | E | `knowledge/reasoning/equation_reasoner.py` | `—` | `—` | **CONSOLIDATE** | Equation reasoning in reasoning/w10/reasoner.py | PENDING |
| DG-122 | D | `knowledge/reasoning/recommendation_engine.py` | `knowledge/interface/rag.py` | `ControlledRAGOrchestrator (retrieval only)` | **SUPERSEDE** | Controlled RAG (`interface/rag.py`) replaces recommender; no auto-promotion | PENDING |
| DG-123 | C | `knowledge/reasoning/traceability_engine.py` | `knowledge/reasoning/w10/chains.py` | `EvidenceChainBuilder.build_chain` | **CONSOLIDATE** | Canonical: `knowledge/reasoning/w10/chains.py` (`EvidenceChainBuilder.build_chain`) | PENDING |
| DG-124 | E | `knowledge/repositories/chapter_repository.py` | `—` | `—` | **REMOVE FROM ARCHITECTURE** | Graph-primary persistence; entity repos supersede frozen plural tree (ADR-001) | PENDING |
| DG-125 | E | `knowledge/repositories/component_repository.py` | `—` | `—` | **REMOVE FROM ARCHITECTURE** | Graph-primary persistence; entity repos supersede frozen plural tree (ADR-001) | PENDING |
| DG-126 | E | `knowledge/repositories/constant_repository.py` | `—` | `—` | **REMOVE FROM ARCHITECTURE** | Graph-primary persistence; entity repos supersede frozen plural tree (ADR-001) | PENDING |
| DG-127 | E | `knowledge/repositories/correlation_repository.py` | `—` | `—` | **REMOVE FROM ARCHITECTURE** | Graph-primary persistence; entity repos supersede frozen plural tree (ADR-001) | PENDING |
| DG-128 | E | `knowledge/repositories/design_rule_repository.py` | `—` | `—` | **REMOVE FROM ARCHITECTURE** | Graph-primary persistence; entity repos supersede frozen plural tree (ADR-001) | PENDING |
| DG-129 | B | `knowledge/repositories/document_repository.py` | `knowledge/repository/repository.py` | `DocumentRepository` | **RELOCATE** | Accept `knowledge/repository/repository.py` as canonical; frozen path abandoned | PENDING |
| DG-130 | E | `knowledge/repositories/equation_repository.py` | `—` | `—` | **REMOVE FROM ARCHITECTURE** | Graph-primary persistence; entity repos supersede frozen plural tree (ADR-001) | PENDING |
| DG-131 | E | `knowledge/repositories/figure_repository.py` | `—` | `—` | **REMOVE FROM ARCHITECTURE** | Graph-primary persistence; entity repos supersede frozen plural tree (ADR-001) | PENDING |
| DG-132 | E | `knowledge/repositories/material_repository.py` | `—` | `—` | **REMOVE FROM ARCHITECTURE** | Graph-primary persistence; entity repos supersede frozen plural tree (ADR-001) | PENDING |
| DG-133 | E | `knowledge/repositories/property_repository.py` | `—` | `—` | **REMOVE FROM ARCHITECTURE** | Graph-primary persistence; entity repos supersede frozen plural tree (ADR-001) | PENDING |
| DG-134 | C | `knowledge/repositories/repository_manager.py` | `knowledge/repository/source_registry.py` | `SourceRegistry` | **CONSOLIDATE** | Canonical: `knowledge/repository/source_registry.py` (`SourceRegistry`) | PENDING |
| DG-135 | E | `knowledge/repositories/section_repository.py` | `—` | `—` | **REMOVE FROM ARCHITECTURE** | Graph-primary persistence; entity repos supersede frozen plural tree (ADR-001) | PENDING |
| DG-136 | E | `knowledge/repositories/simulation_repository.py` | `—` | `—` | **REMOVE FROM ARCHITECTURE** | Graph-primary persistence; entity repos supersede frozen plural tree (ADR-001) | PENDING |
| DG-137 | E | `knowledge/repositories/subsystem_repository.py` | `—` | `—` | **REMOVE FROM ARCHITECTURE** | Graph-primary persistence; entity repos supersede frozen plural tree (ADR-001) | PENDING |
| DG-138 | E | `knowledge/repositories/table_repository.py` | `—` | `—` | **REMOVE FROM ARCHITECTURE** | Graph-primary persistence; entity repos supersede frozen plural tree (ADR-001) | PENDING |
| DG-139 | E | `knowledge/repositories/variable_repository.py` | `—` | `—` | **REMOVE FROM ARCHITECTURE** | Graph-primary persistence; entity repos supersede frozen plural tree (ADR-001) | PENDING |
| DG-140 | E | `knowledge/search/citation_search.py` | `—` | `—` | **CONSOLIDATE** | Filter facets on hybrid/w8 search engines | PENDING |
| DG-141 | E | `knowledge/search/equation_search.py` | `—` | `—` | **CONSOLIDATE** | Filter facets on hybrid/w8 search engines | PENDING |
| DG-142 | B | `knowledge/search/graph_search.py` | `knowledge/search/w8/graph_search.py` | `GraphSearchEngine` | **COMPATIBILITY FACADE** | Canonical: `knowledge/search/w8/graph_search.py`; facade preserves frozen import path | PENDING |
| DG-143 | B | `knowledge/search/hybrid_search.py` | `knowledge/search/w8/hybrid.py` | `HybridSearchEngine` | **COMPATIBILITY FACADE** | Canonical: `knowledge/search/w8/hybrid.py`; facade preserves frozen import path | PENDING |
| DG-144 | B | `knowledge/search/keyword_search.py` | `knowledge/search/w8/keyword.py` | `KeywordSearchEngine` | **COMPATIBILITY FACADE** | Canonical: `knowledge/search/w8/keyword.py`; facade preserves frozen import path | PENDING |
| DG-145 | B | `knowledge/search/search_engine.py` | `knowledge/search/engine.py` | `KnowledgeSearchEngine` | **COMPATIBILITY FACADE** | Canonical: `knowledge/search/engine.py`; facade preserves frozen import path | PENDING |
| DG-146 | B | `knowledge/search/semantic_search.py` | `knowledge/search/w8/semantic.py` | `SemanticVectorSearchEngine` | **COMPATIBILITY FACADE** | Canonical: `knowledge/search/w8/semantic.py`; facade preserves frozen import path | PENDING |
| DG-147 | E | `knowledge/search/variable_search.py` | `—` | `—` | **CONSOLIDATE** | Filter facets on hybrid/w8 search engines | PENDING |
| DG-148 | C | `knowledge/utils/equation_utils.py` | `knowledge/parsers/w3/equations.py + extraction/w4/equations.py` | `extract_equations; extract_equation_candidates` | **CONSOLIDATE** | Canonical: `knowledge/parsers/w3/equations.py + extraction/w4/equations.py` (`extract_equations; extract_equation_candidates`) | PENDING |
| DG-149 | C | `knowledge/utils/graph_utils.py` | `knowledge/graph/serialization.py + query.py` | `canonical_graph_record_digest; GraphQueryService` | **CONSOLIDATE** | Canonical: `knowledge/graph/serialization.py + query.py` (`canonical_graph_record_digest; GraphQueryService`) | PENDING |
| DG-150 | B | `knowledge/utils/hashing.py` | `knowledge/source/integrity.py` | `sha256_text_digest; sha256_bytes_digest` | **RELOCATE** | Accept `knowledge/source/integrity.py` as canonical; frozen path abandoned | PENDING |
| DG-151 | D | `knowledge/utils/logging_utils.py` | `core project logging (outside knowledge/)` | `—` | **SUPERSEDE** | Project-level logging supersedes knowledge-local utils | PENDING |
| DG-152 | B | `knowledge/utils/markdown_utils.py` | `knowledge/ingestion_adapters/html.py` | `Markdown normalization` | **RELOCATE** | Accept `knowledge/ingestion_adapters/html.py` as canonical; frozen path abandoned | PENDING |
| DG-153 | C | `knowledge/utils/parsing_utils.py` | `knowledge/parsers/w3/structure.py + ingestion_adapters/normalize.py` | `parse_document_structure; normalize` | **CONSOLIDATE** | Canonical: `knowledge/parsers/w3/structure.py + ingestion_adapters/normalize.py` (`parse_document_structure; normalize`) | PENDING |
| DG-154 | F | `knowledge/utils/text_utils.py` | `—` | `—` | **IMPLEMENT** | Thin shared text helpers; no duplicate of parsing_utils | PENDING |
| DG-155 | E | `knowledge/validation/ambiguity_detector.py` | `—` | `—` | **IMPLEMENT** | Ambiguity detection gap; KG-BLOCK-013+ | PENDING |
| DG-156 | E | `knowledge/validation/citation_validator.py` | `—` | `—` | **IMPLEMENT** | Citation integrity validation gap; KG-BLOCK-013+ | PENDING |
| DG-157 | B | `knowledge/validation/consistency_validator.py` | `knowledge/validation/conflicts.py` | `detect_conflicts` | **RELOCATE** | Accept `knowledge/validation/conflicts.py` as canonical; frozen path abandoned | PENDING |
| DG-158 | C | `knowledge/validation/dimension_validator.py` | `knowledge/validation/units.py` | `validate_units` | **CONSOLIDATE** | Canonical: `knowledge/validation/units.py` (`validate_units`) | PENDING |
| DG-159 | B | `knowledge/validation/duplicate_detector.py` | `knowledge/validation/duplicates.py` | `detect_duplicates` | **RELOCATE** | Accept `knowledge/validation/duplicates.py` as canonical; frozen path abandoned | PENDING |
| DG-160 | C | `knowledge/validation/equation_validator.py` | `knowledge/validation/schema.py` | `validate_schema` | **CONSOLIDATE** | Canonical: `knowledge/validation/schema.py` (`validate_schema`) | PENDING |
| DG-161 | B | `knowledge/validation/ontology_validator.py` | `knowledge/ontology/validation.py` | `validate_taxonomy_edge` | **RELOCATE** | Accept `knowledge/ontology/validation.py` as canonical; frozen path abandoned | PENDING |
| DG-162 | C | `knowledge/validation/source_validator.py` | `knowledge/validation/provenance.py + source/integrity.py` | `validate_provenance; verify_digest` | **CONSOLIDATE** | Canonical: `knowledge/validation/provenance.py + source/integrity.py` (`validate_provenance; verify_digest`) | PENDING |
| DG-163 | C | `knowledge/validation/unit_validator.py` | `knowledge/validation/units.py` | `validate_units` | **CONSOLIDATE** | Canonical: `knowledge/validation/units.py` (`validate_units`) | PENDING |
| DG-164 | H | `(current) `knowledge/extraction/claim.py`` | `—` | `—` | **APPROVE** | W4 claim extraction support; canonical | PENDING |
| DG-165 | H | `(current) `knowledge/extraction/entity.py`` | `—` | `—` | **APPROVE** | W4 entity typing support; canonical | PENDING |
| DG-166 | H | `(current) `knowledge/extraction/equation.py`` | `—` | `—` | **APPROVE** | W4 equation helper; canonical | PENDING |
| DG-167 | H | `(current) `knowledge/indexing/builder.py`` | `—` | `—` | **APPROVE** | Canonical index orchestration replacing index_manager | PENDING |
| DG-168 | H | `(current) `knowledge/indexing/lexical.py`` | `—` | `—` | **APPROVE** | Canonical keyword index replacing keyword_index.py | PENDING |
| DG-169 | H | `(current) `knowledge/indexing/models.py`` | `—` | `—` | **APPROVE** | Index contract models; canonical | PENDING |
| DG-170 | H | `(current) `knowledge/indexing/semantic.py`` | `—` | `—` | **APPROVE** | Canonical semantic index replacing semantic_index.py | PENDING |
| DG-171 | H | `(current) `knowledge/ingestion/base.py`` | `—` | `—` | **APPROVE** | Ingestion contract base; canonical | PENDING |
| DG-172 | H | `(current) `knowledge/ingestion/models.py`` | `—` | `—` | **APPROVE** | IngestionResult/metadata; canonical | PENDING |
| DG-173 | H | `(current) `knowledge/ontology/aliases.py`` | `—` | `—` | **APPROVE** | W5 alias resolution; canonical | PENDING |
| DG-174 | H | `(current) `knowledge/ontology/canonicalization.py`` | `—` | `—` | **APPROVE** | W5 term canonicalization; canonical | PENDING |
| DG-175 | H | `(current) `knowledge/ontology/models.py`` | `—` | `—` | **APPROVE** | OntologyTerm/TaxonomyEdge; canonical | PENDING |
| DG-176 | H | `(current) `knowledge/ontology/registry.py`` | `—` | `—` | **APPROVE** | Replaces ontology_manager; canonical | PENDING |
| DG-177 | H | `(current) `knowledge/ontology/relationships.py`` | `—` | `—` | **APPROVE** | W5 relationship typing; canonical | PENDING |
| DG-178 | H | `(current) `knowledge/ontology/taxonomy.py`` | `—` | `—` | **APPROVE** | W5 taxonomy; canonical | PENDING |
| DG-179 | H | `(current) `knowledge/ontology/validation.py`` | `—` | `—` | **APPROVE** | Replaces ontology_validator path; canonical | PENDING |
| DG-180 | H | `(current) `knowledge/parsers/base.py`` | `—` | `—` | **APPROVE** | Parser contract base; canonical | PENDING |
| DG-181 | H | `(current) `knowledge/parsers/models.py`` | `—` | `—` | **APPROVE** | Parser shared models; canonical | PENDING |
| DG-182 | H | `(current) `knowledge/parsers/pdf_normalizer.py`` | `—` | `—` | **APPROVE** | PDF normalization; add test coverage in future block | PENDING |
| DG-183 | H | `(current) `knowledge/reasoning/context.py`` | `—` | `—` | **APPROVE** | Reasoning context assembly; canonical | PENDING |
| DG-184 | H | `(current) `knowledge/reasoning/evidence.py`` | `—` | `—` | **APPROVE** | Evidence model layer; canonical | PENDING |
| DG-185 | H | `(current) `knowledge/reasoning/reasoner.py`` | `—` | `—` | **APPROVE** | ProvenanceAwareReasoner; canonical | PENDING |
| DG-186 | H | `(current) `knowledge/repository/repository.py`` | `—` | `—` | **APPROVE** | DocumentRepository; canonical singular path | PENDING |
| DG-187 | H | `(current) `knowledge/repository/source_registry.py`` | `—` | `—` | **APPROVE** | SourceRegistry; canonical | PENDING |
| DG-188 | H | `(current) `knowledge/repository/source_repository.py`` | `—` | `—` | **APPROVE** | Source persistence; canonical | PENDING |
| DG-189 | H | `(current) `knowledge/search/contracts.py`` | `—` | `—` | **APPROVE** | Search contracts; canonical | PENDING |
| DG-190 | H | `(current) `knowledge/search/engine.py`` | `—` | `—` | **APPROVE** | KnowledgeSearchEngine; canonical | PENDING |
| DG-191 | H | `(current) `knowledge/validation/conflicts.py`` | `—` | `—` | **APPROVE** | Consistency/conflict detection; canonical | PENDING |
| DG-192 | H | `(current) `knowledge/validation/duplicates.py`` | `—` | `—` | **APPROVE** | Duplicate detection; canonical | PENDING |
| DG-193 | H | `(current) `knowledge/validation/engine.py`` | `—` | `—` | **APPROVE** | ValidationEngine; canonical | PENDING |
| DG-194 | H | `(current) `knowledge/validation/models.py`` | `—` | `—` | **APPROVE** | Validation models; canonical | PENDING |
| DG-195 | H | `(current) `knowledge/validation/provenance.py`` | `—` | `—` | **APPROVE** | Source provenance validation; canonical | PENDING |
| DG-196 | H | `(current) `knowledge/validation/registry.py`` | `—` | `—` | **APPROVE** | Validation rule registry; canonical | PENDING |
| DG-197 | H | `(current) `knowledge/validation/rules.py`` | `—` | `—` | **APPROVE** | Validation rules; canonical | PENDING |
| DG-198 | H | `(current) `knowledge/validation/schema.py`` | `—` | `—` | **APPROVE** | Schema validation; canonical | PENDING |
| DG-199 | H | `(current) `knowledge/validation/units.py`` | `—` | `—` | **APPROVE** | Unit/dimension validation; canonical | PENDING |

---

## Approval Block

| Field | Value |
|-------|-------|
| Technical Owner | __________________ |
| Date | __________________ |
| Scope | All DG-001 through DG-199 |
| Implementation Gate | CLOSED until signed |

**Note:** Registry artifact — pipeline frozen paths listed as `*.py.py` in JSON should read `knowledge/pipelines/*.py` (documentation typo only).