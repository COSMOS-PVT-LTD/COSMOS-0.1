# Knowledge File-Level Traceability Matrix

**Document ID:** COSMOS-KG-FILE-TRACE-002
**Date:** 2026-08-23
**Authority:** Technical Owner Reconciliation Directive
**Phase:** RECONCILIATION ONLY — no implementation

## Disposition Key

| Code | Label |
|------|-------|
| A | EXACT_MATCH |
| B | RELOCATED |
| C | CONSOLIDATED |
| D | SUPERSEDED |
| E | MISSING_REQUIRED |
| F | MISSING_DECISION_REQUIRED |
| G | EXTRA_JUSTIFIED |
| H | EXTRA_REVIEW_REQUIRED |

## Summary

| Metric | Value |
|--------|-------|
| Frozen files reconciled | 175 |
| Current knowledge .py files | 148 |
| A EXACT_MATCH | 12 |
| B RELOCATED | 27 |
| C CONSOLIDATED | 48 |
| D SUPERSEDED | 16 |
| E MISSING_REQUIRED | 67 |
| F MISSING_DECISION_REQUIRED | 5 |
| G EXTRA_JUSTIFIED (current only) | 100 |
| H EXTRA_REVIEW_REQUIRED (current only) | 36 |

**FILE-LEVEL EXACT MATCH:** 12/175 = 6.9%
**CAPABILITY ADDRESSED (A+B+C+D):** 103/175 = 58.9%

---

## Master Table (Frozen → Current)

| # | Frozen Path | Disp | Current Path | Symbol(s) | Capability | KG | BLOCK | Test | Justification |
|---|-------------|------|--------------|-----------|------------|-----|-------|------|---------------|
| 1 | `knowledge/__init__.py` | A | `knowledge/__init__.py` | `—` | Package root | — | — | N/A | Exact match |
| 2 | `knowledge/exporters/database_exporter.py` | E | `—` | `—` | Export | — | — | NO | Exporter package not implemented |
| 3 | `knowledge/exporters/graph_exporter.py` | E | `—` | `—` | Export | — | — | NO | Exporter package not implemented |
| 4 | `knowledge/exporters/html_exporter.py` | E | `—` | `—` | Export | — | — | NO | Exporter package not implemented |
| 5 | `knowledge/exporters/json_exporter.py` | E | `—` | `—` | Export | — | — | NO | Exporter package not implemented |
| 6 | `knowledge/exporters/latex_exporter.py` | E | `—` | `—` | Export | — | — | NO | Exporter package not implemented |
| 7 | `knowledge/exporters/markdown_exporter.py` | E | `—` | `—` | Export | — | — | NO | Exporter package not implemented |
| 8 | `knowledge/exporters/yaml_exporter.py` | E | `—` | `—` | Export | — | — | NO | Exporter package not implemented |
| 9 | `knowledge/extraction/abbreviation_extractor.py` | E | `—` | `—` | KG-019 | — | NO | Extraction abbreviation_extractor | W4 |
| 10 | `knowledge/extraction/assumption_extractor.py` | E | `—` | `—` | KG-019 | — | NO | Extraction assumption_extractor | W4 |
| 11 | `knowledge/extraction/boundary_condition_extractor.py` | E | `—` | `—` | KG-019 | — | NO | Extraction boundary_condition_extractor | W4 |
| 12 | `knowledge/extraction/component_extractor.py` | C | `knowledge/extraction/w4/entities.py` | `extract_entities` | KG-019 | BLOCK-007 | test_w4_extraction.py | Extraction component_extractor | W4 |
| 13 | `knowledge/extraction/constant_extractor.py` | C | `knowledge/extraction/w4/entities.py` | `extract_entities` | KG-019 | BLOCK-007 | test_w4_extraction.py | Extraction constant_extractor | W4 |
| 14 | `knowledge/extraction/correlation_extractor.py` | E | `—` | `—` | KG-019 | — | NO | Extraction correlation_extractor | W4 |
| 15 | `knowledge/extraction/design_rule_extractor.py` | E | `—` | `—` | KG-019 | — | NO | Extraction design_rule_extractor | W4 |
| 16 | `knowledge/extraction/dimension_extractor.py` | C | `knowledge/extraction/w4/entities.py` | `extract_entities` | KG-019 | BLOCK-007 | test_w4_extraction.py | Extraction dimension_extractor | W4 |
| 17 | `knowledge/extraction/engineering_domain_extractor.py` | C | `knowledge/extraction/w4/entities.py` | `extract_entities` | KG-019 | BLOCK-007 | test_w4_extraction.py | Extraction engineering_domain_extractor | W4 |
| 18 | `knowledge/extraction/equation_extractor.py` | C | `knowledge/extraction/w4/equations.py` | `extract_equation_candidates` | equation_extractor.py | KG-021 | BLOCK-007 | test_w4_extraction.py | Extraction |
| 19 | `knowledge/extraction/experiment_extractor.py` | E | `—` | `—` | KG-019 | — | NO | Extraction experiment_extractor | W4 |
| 20 | `knowledge/extraction/extraction_pipeline.py` | B | `knowledge/extraction/w4/pipeline.py` | `extract_document; W4ExtractionPipeline` | extraction_pipeline.py | KG-019-023 | BLOCK-007 | test_w4_extraction.py | Extraction |
| 21 | `knowledge/extraction/failure_mode_extractor.py` | E | `—` | `—` | KG-019 | — | NO | Extraction failure_mode_extractor | W4 |
| 22 | `knowledge/extraction/glossary_extractor.py` | E | `—` | `—` | KG-019 | — | NO | Extraction glossary_extractor | W4 |
| 23 | `knowledge/extraction/manufacturing_extractor.py` | E | `—` | `—` | KG-019 | — | NO | Extraction manufacturing_extractor | W4 |
| 24 | `knowledge/extraction/material_extractor.py` | C | `knowledge/extraction/w4/entities.py` | `extract_entities` | material_extractor.py | KG-019 | BLOCK-007 | test_w4_extraction.py | Extraction |
| 25 | `knowledge/extraction/physical_law_extractor.py` | E | `—` | `—` | KG-019 | — | NO | Extraction physical_law_extractor | W4 |
| 26 | `knowledge/extraction/process_extractor.py` | E | `—` | `—` | KG-019 | — | NO | Extraction process_extractor | W4 |
| 27 | `knowledge/extraction/property_extractor.py` | E | `—` | `—` | KG-019 | — | NO | Extraction property_extractor | W4 |
| 28 | `knowledge/extraction/quantity_extractor.py` | B | `knowledge/extraction/w4/quantities.py` | `extract_quantities` | quantity_extractor.py | KG-020 | BLOCK-007 | test_w4_extraction.py | Extraction |
| 29 | `knowledge/extraction/simulation_extractor.py` | E | `—` | `—` | KG-019 | — | NO | Extraction simulation_extractor | W4 |
| 30 | `knowledge/extraction/subsystem_extractor.py` | C | `knowledge/extraction/w4/entities.py` | `extract_entities` | KG-019 | BLOCK-007 | test_w4_extraction.py | Extraction subsystem_extractor | W4 |
| 31 | `knowledge/extraction/unit_extractor.py` | C | `knowledge/extraction/w4/entities.py` | `extract_entities` | KG-019 | BLOCK-007 | test_w4_extraction.py | Extraction unit_extractor | W4 |
| 32 | `knowledge/extraction/variable_extractor.py` | C | `knowledge/extraction/w4/entities.py` | `extract_entities` | variable_extractor.py | KG-021 | BLOCK-007 | test_w4_extraction.py | Extraction |
| 33 | `knowledge/graph/citation_graph.py` | E | `—` | `—` | citation_graph.py | KG-038 | — | NO | Graph layer |
| 34 | `knowledge/graph/concept_graph.py` | F | `—` | `—` | concept_graph.py | KG-035 | — | NO | Graph layer |
| 35 | `knowledge/graph/dependency_graph.py` | C | `knowledge/graph/query.py` | `GraphQueryService.traverse` | dependency_graph.py | KG-030 | BLOCK-003 | test_query.py | Graph layer |
| 36 | `knowledge/graph/engineering_graph.py` | C | `knowledge/graph/construction.py` | `GraphConstructor` | engineering_graph.py | KG-028 | BLOCK-003 | test_construction.py | Graph layer |
| 37 | `knowledge/graph/equation_graph.py` | C | `knowledge/graph/construction.py` | `GraphConstructor` | equation_graph.py | KG-028 | BLOCK-003 | test_construction.py | Graph layer |
| 38 | `knowledge/graph/graph_manager.py` | C | `knowledge/graph/construction.py + query.py` | `GraphConstructor.construct; GraphQueryService` | graph_manager.py | KG-028-031 | BLOCK-003 | test_construction.py; test_query.py | Graph layer |
| 39 | `knowledge/graph/relationship_builder.py` | B | `knowledge/graph/construction.py` | `GraphConstructor + extraction/w4/relationships.py` | relationship_builder.py | KG-023 | BLOCK-003/007 | test_construction.py | Graph layer |
| 40 | `knowledge/graph/variable_graph.py` | C | `knowledge/graph/construction.py` | `GraphConstructor` | variable_graph.py | KG-028 | BLOCK-003 | test_construction.py | Graph layer |
| 41 | `knowledge/indexing/citation_index.py` | E | `—` | `—` | citation_index.py | KG-033 | — | NO | Indexing |
| 42 | `knowledge/indexing/equation_index.py` | E | `—` | `—` | equation_index.py | KG-033 | — | NO | Indexing |
| 43 | `knowledge/indexing/graph_index.py` | B | `knowledge/indexing/w7/graph_index.py` | `InMemoryGraphIndex` | graph_index.py | KG-035 | BLOCK-010 | test_w7_indexing.py | Indexing |
| 44 | `knowledge/indexing/index_manager.py` | C | `knowledge/indexing/builder.py + w7/bundle.py` | `KnowledgeIndexBuilder.build; W7IndexBuilder.build` | index_manager.py | KG-033-035 | BLOCK-004/010 | test_indexing.py; test_w7_indexing.py | Indexing |
| 45 | `knowledge/indexing/keyword_index.py` | B | `knowledge/indexing/lexical.py` | `InMemoryLexicalIndex` | keyword_index.py | KG-033 | BLOCK-004 | test_indexing.py | Indexing |
| 46 | `knowledge/indexing/semantic_index.py` | B | `knowledge/indexing/semantic.py + w7/vector.py` | `InMemorySemanticIndex; InMemoryVectorIndex` | semantic_index.py | KG-034 | BLOCK-004/010 | test_indexing.py | Indexing |
| 47 | `knowledge/indexing/variable_index.py` | E | `—` | `—` | variable_index.py | KG-033 | — | NO | Indexing |
| 48 | `knowledge/ingestion/batch_loader.py` | E | `—` | `—` | batch loader.py | KG-013 | — | NO | Ingestion layer |
| 49 | `knowledge/ingestion/docx_loader.py` | B | `knowledge/ingestion_adapters/docx.py` | `DocxIngestionAdapter.ingest` | docx loader.py | KG-010 | BLOCK-005 | test_adapters.py | Ingestion layer |
| 50 | `knowledge/ingestion/epub_loader.py` | E | `—` | `—` | epub loader.py | KG-010 | — | NO | Ingestion layer |
| 51 | `knowledge/ingestion/html_loader.py` | B | `knowledge/ingestion_adapters/html.py` | `HtmlIngestionAdapter.ingest` | html loader.py | KG-012 | BLOCK-005 | test_adapters.py | Ingestion layer |
| 52 | `knowledge/ingestion/image_loader.py` | E | `—` | `—` | image loader.py | KG-016 | — | NO | Ingestion layer |
| 53 | `knowledge/ingestion/ingestion_pipeline.py` | C | `knowledge/ingestion_adapters/registry.py` | `IngestionOrchestrator` | ingestion pipeline.py | KG-009-013 | BLOCK-005 | test_adapters.py | Ingestion layer |
| 54 | `knowledge/ingestion/latex_loader.py` | E | `—` | `—` | latex loader.py | KG-012 | — | NO | Ingestion layer |
| 55 | `knowledge/ingestion/markdown_loader.py` | B | `knowledge/ingestion_adapters/html.py` | `MarkdownIngestionAdapter.ingest` | markdown loader.py | KG-012 | BLOCK-005 | test_adapters.py | Ingestion layer |
| 56 | `knowledge/ingestion/markitdown_loader.py` | E | `—` | `—` | markitdown loader.py | KG-009 | — | NO | Ingestion layer |
| 57 | `knowledge/ingestion/metadata_loader.py` | C | `knowledge/ingestion/models.py` | `IngestionResult` | metadata loader.py | KG-009 | BLOCK-002 | test_ingestion.py | Ingestion layer |
| 58 | `knowledge/ingestion/ocr_loader.py` | E | `—` | `—` | ocr loader.py | KG-016 | — | NO | Ingestion layer |
| 59 | `knowledge/ingestion/pdf_loader.py` | B | `knowledge/ingestion_adapters/pdf.py` | `PdfIngestionAdapter.ingest` | pdf loader.py | KG-009 | BLOCK-005 | test_adapters.py | Ingestion layer |
| 60 | `knowledge/models/appendix.py` | E | `—` | `—` | Appendix model | KG-014 | — | NO | Model disposition E |
| 61 | `knowledge/models/assumption.py` | E | `—` | `—` | Assumption | KG-022 | — | NO | Model disposition E |
| 62 | `knowledge/models/boundary_condition.py` | E | `—` | `—` | Boundary condition | KG-019+ | — | NO | Model disposition E |
| 63 | `knowledge/models/chapter.py` | E | `—` | `—` | Chapter model | KG-014 | — | NO | Model disposition E |
| 64 | `knowledge/models/citation.py` | C | `knowledge/parsers/w3/models.py` | `ParsedCitation` | Citation | KG-018 | BLOCK-006 | test_w3_parsing.py | Model disposition C |
| 65 | `knowledge/models/component.py` | C | `knowledge/graph/entity.py` | `CanonicalEntityType` | Component typing | KG-019 | — | NO | Model disposition C |
| 66 | `knowledge/models/constant.py` | A | `knowledge/models/constant.py` | `knowledge.models.constant.Constant` | Canonical constant | KG-020 | Pre-KG | test_constant.py | Exact path match |
| 67 | `knowledge/models/correlation.py` | E | `—` | `—` | Correlation | KG-019+ | — | NO | Model disposition E |
| 68 | `knowledge/models/design_rule.py` | E | `—` | `—` | Design rule | KG-019 | — | NO | Model disposition E |
| 69 | `knowledge/models/dimension.py` | A | `knowledge/models/dimension.py` | `knowledge.models.dimension.Dimension` | Canonical dimension | KG-020/042 | BLOCK-007 | test_dimension.py [FROZEN] | Exact path match |
| 70 | `knowledge/models/document.py` | A | `knowledge/models/document.py` | `knowledge.models.document.Document` | Canonical document | KG-014 | Pre-KG | test_repository.py | Exact path match |
| 71 | `knowledge/models/empirical_relation.py` | F | `—` | `—` | Empirical relation | — | — | NO | Model disposition F |
| 72 | `knowledge/models/engineering_domain.py` | A | `knowledge/models/engineering_domain.py` | `knowledge.models.engineering_domain.EngineeringDomain` | Canonical engineering_domain | KG-026 | Pre-KG | test_ontology.py | Exact path match |
| 73 | `knowledge/models/equation.py` | A | `knowledge/models/equation.py` | `knowledge.models.equation.Equation` | Canonical equation | KG-021 | Pre-KG | test_extraction.py | Exact path match |
| 74 | `knowledge/models/experiment.py` | E | `—` | `—` | Experiment | KG-019 | — | NO | Model disposition E |
| 75 | `knowledge/models/failure_mode.py` | E | `—` | `—` | Failure mode | KG-019 | — | NO | Model disposition E |
| 76 | `knowledge/models/figure.py` | C | `knowledge/parsers/w3/models.py` | `ParsedFigure` | Figure | KG-016 | BLOCK-006 | test_w3_parsing.py | Model disposition C |
| 77 | `knowledge/models/glossary.py` | E | `—` | `—` | Glossary model | KG-014 | — | NO | Model disposition E |
| 78 | `knowledge/models/manufacturing_process.py` | E | `—` | `—` | Manufacturing process | KG-019 | — | NO | Model disposition E |
| 79 | `knowledge/models/material.py` | A | `knowledge/models/material.py` | `knowledge.models.material.Material` | Canonical material | KG-019 | Pre-KG | test_material.py | Exact path match |
| 80 | `knowledge/models/metadata.py` | C | `knowledge/ingestion/models.py` | `IngestionResult` | Metadata | KG-009 | — | NO | Model disposition C |
| 81 | `knowledge/models/ontology_edge.py` | C | `knowledge/ontology/models.py` | `TaxonomyEdge` | Ontology edge | KG-026 | — | test_w5_ontology.py | Model disposition C |
| 82 | `knowledge/models/ontology_node.py` | C | `knowledge/ontology/models.py` | `OntologyTerm` | Ontology node | KG-024 | — | test_w5_ontology.py | Model disposition C |
| 83 | `knowledge/models/paragraph.py` | C | `knowledge/parsers/w3/models.py` | `ParsedParagraph` | Paragraph | KG-014 | BLOCK-006 | test_w3_parsing.py | Model disposition C |
| 84 | `knowledge/models/physical_law.py` | E | `—` | `—` | Physical law | KG-019+ | — | NO | Model disposition E |
| 85 | `knowledge/models/process.py` | E | `—` | `—` | Process | KG-019 | — | NO | Model disposition E |
| 86 | `knowledge/models/property.py` | E | `—` | `—` | Property | KG-019 | — | NO | Model disposition E |
| 87 | `knowledge/models/quantity.py` | A | `knowledge/models/quantity.py` | `knowledge.models.quantity.Quantity` | Canonical quantity | KG-020/042 | BLOCK-007 | test_quantity.py [FROZEN] | Exact path match |
| 88 | `knowledge/models/reference.py` | A | `knowledge/models/reference.py` | `knowledge.models.reference.Reference` | Canonical reference | KG-018 | Pre-KG | INDIRECT | Exact path match |
| 89 | `knowledge/models/section.py` | E | `—` | `—` | Section model | KG-014 | — | NO | Model disposition E |
| 90 | `knowledge/models/sentence.py` | F | `—` | `—` | Sentence model | KG-014 | — | NO | Model disposition F |
| 91 | `knowledge/models/simulation.py` | E | `—` | `—` | Simulation | KG-019 | — | NO | Model disposition E |
| 92 | `knowledge/models/subsystem.py` | A | `knowledge/models/subsystem.py` | `knowledge.models.subsystem.Subsystem` | Canonical subsystem | KG-019 | Pre-KG | test_material.py | Exact path match |
| 93 | `knowledge/models/table.py` | C | `knowledge/parsers/w3/models.py` | `ParsedTable` | Table | KG-015 | BLOCK-006 | test_w3_parsing.py | Model disposition C |
| 94 | `knowledge/models/unit.py` | A | `knowledge/models/unit.py` | `knowledge.models.unit.Unit` | Canonical unit | KG-020/042 | BLOCK-007 | test_unit.py [FROZEN] | Exact path match |
| 95 | `knowledge/models/variable.py` | A | `knowledge/models/variable.py` | `knowledge.models.variable.Variable` | Canonical variable | KG-021 | Pre-KG | test_extraction.py | Exact path match |
| 96 | `knowledge/ontology/aerospace.py` | D | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | Domain aerospace | KG-026 | BLOCK-008 | test_w5_ontology.py | Static module superseded by registry |
| 97 | `knowledge/ontology/combustion.py` | D | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | Domain combustion | KG-026 | BLOCK-008 | test_w5_ontology.py | Static module superseded by registry |
| 98 | `knowledge/ontology/compressible_flow.py` | D | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | Domain compressible_flow | KG-026 | BLOCK-008 | test_w5_ontology.py | Static module superseded by registry |
| 99 | `knowledge/ontology/controls.py` | D | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | Domain controls | KG-026 | BLOCK-008 | test_w5_ontology.py | Static module superseded by registry |
| 100 | `knowledge/ontology/cryogenics.py` | D | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | Domain cryogenics | KG-026 | BLOCK-008 | test_w5_ontology.py | Static module superseded by registry |
| 101 | `knowledge/ontology/engineering_domains.py` | C | `knowledge/ontology/registry.py + ontology/models.py` | `OntologyRegistry; EngineeringDomain taxonomy` | Engineering domain taxonomy | KG-026 | BLOCK-008 | test_w5_ontology.py | Static domain module consolidated into registry + models |
| 102 | `knowledge/ontology/fluid_mechanics.py` | D | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | Domain fluid_mechanics | KG-026 | BLOCK-008 | test_w5_ontology.py | Static module superseded by registry |
| 103 | `knowledge/ontology/heat_transfer.py` | D | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | Domain heat_transfer | KG-026 | BLOCK-008 | test_w5_ontology.py | Static module superseded by registry |
| 104 | `knowledge/ontology/manufacturing.py` | D | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | Domain manufacturing | KG-026 | BLOCK-008 | test_w5_ontology.py | Static module superseded by registry |
| 105 | `knowledge/ontology/materials.py` | D | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | Domain materials | KG-026 | BLOCK-008 | test_w5_ontology.py | Static module superseded by registry |
| 106 | `knowledge/ontology/ontology_manager.py` | B | `knowledge/ontology/registry.py` | `OntologyRegistry` | Ontology management | KG-024 | BLOCK-008 | test_w5_ontology.py | Registry replaces manager |
| 107 | `knowledge/ontology/optimization.py` | D | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | Domain optimization | KG-026 | BLOCK-008 | test_w5_ontology.py | Static module superseded by registry |
| 108 | `knowledge/ontology/propulsion.py` | D | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | Domain propulsion | KG-026 | BLOCK-008 | test_w5_ontology.py | Static module superseded by registry |
| 109 | `knowledge/ontology/structures.py` | D | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | Domain structures | KG-026 | BLOCK-008 | test_w5_ontology.py | Static module superseded by registry |
| 110 | `knowledge/ontology/thermochemistry.py` | D | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | Domain thermochemistry | KG-026 | BLOCK-008 | test_w5_ontology.py | Static module superseded by registry |
| 111 | `knowledge/ontology/thermodynamics.py` | D | `knowledge/ontology/registry.py` | `OntologyRegistry.register_term` | Domain thermodynamics | KG-026 | BLOCK-008 | test_w5_ontology.py | Static module superseded by registry |
| 112 | `knowledge/parsers/appendix_parser.py` | E | `—` | `—` | appendix_parser.py | KG-014 | — | NO | Parser layer |
| 113 | `knowledge/parsers/bibliography_parser.py` | C | `knowledge/parsers/w3/references.py` | `extract_references` | bibliography_parser.py | KG-018 | BLOCK-006 | test_w3_parsing.py | Parser layer |
| 114 | `knowledge/parsers/chapter_parser.py` | C | `knowledge/parsers/w3/structure.py` | `parse_document_structure` | chapter_parser.py | KG-014 | BLOCK-006 | test_w3_parsing.py | Parser layer |
| 115 | `knowledge/parsers/citation_parser.py` | C | `knowledge/parsers/w3/references.py` | `extract_citations` | citation_parser.py | KG-018 | BLOCK-006 | test_w3_parsing.py | Parser layer |
| 116 | `knowledge/parsers/document_parser.py` | C | `knowledge/parsers/w3/pipeline.py` | `parse_document` | document_parser.py | KG-014 | BLOCK-006 | test_w3_parsing.py | Parser layer |
| 117 | `knowledge/parsers/figure_parser.py` | B | `knowledge/parsers/w3/figures.py` | `extract_figures` | figure_parser.py | KG-016 | BLOCK-006 | test_w3_parsing.py | Parser layer |
| 118 | `knowledge/parsers/glossary_parser.py` | E | `—` | `—` | glossary_parser.py | KG-014 | — | NO | Parser layer |
| 119 | `knowledge/parsers/heading_parser.py` | C | `knowledge/parsers/w3/structure.py` | `parse_document_structure` | heading_parser.py | KG-014 | BLOCK-006 | test_w3_parsing.py | Parser layer |
| 120 | `knowledge/parsers/metadata_parser.py` | C | `knowledge/parsers/w3/content.py` | `ParseContext` | metadata_parser.py | KG-014 | BLOCK-006 | test_w3_parsing.py | Parser layer |
| 121 | `knowledge/parsers/paragraph_parser.py` | C | `knowledge/parsers/w3/structure.py` | `parse_document_structure` | paragraph_parser.py | KG-014 | BLOCK-006 | test_w3_parsing.py | Parser layer |
| 122 | `knowledge/parsers/section_parser.py` | C | `knowledge/parsers/w3/structure.py` | `parse_document_structure` | section_parser.py | KG-014 | BLOCK-006 | test_w3_parsing.py | Parser layer |
| 123 | `knowledge/parsers/sentence_parser.py` | F | `—` | `—` | sentence_parser.py | KG-014 | — | NO | Parser layer |
| 124 | `knowledge/parsers/table_parser.py` | B | `knowledge/parsers/w3/tables.py` | `extract_tables` | table_parser.py | KG-015 | BLOCK-006 | test_w3_parsing.py | Parser layer |
| 125 | `knowledge/pipelines/document_pipeline.py.py` | C | `tests/integration_tests/kg_block012/helpers/pipeline.py` | `run_full_pipeline` | document_pipeline.py | KG-012 | BLOCK-012 | kg_block012 E2E | Pipeline |
| 126 | `knowledge/pipelines/extraction_pipeline.py.py` | B | `knowledge/extraction/w4/pipeline.py` | `extract_document` | extraction_pipeline.py | KG-019-023 | BLOCK-007 | test_w4_extraction.py | Pipeline |
| 127 | `knowledge/pipelines/indexing_pipeline.py.py` | C | `knowledge/indexing/w7/bundle.py` | `W7IndexBuilder.build` | indexing_pipeline.py | KG-033-035 | BLOCK-010 | test_w7_indexing.py | Pipeline |
| 128 | `knowledge/pipelines/knowledge_pipeline.py.py` | C | `tests/integration_tests/kg_block012/helpers/pipeline.py` | `run_full_pipeline` | knowledge_pipeline.py | KG-012 | BLOCK-012 | kg_block012 E2E | Pipeline |
| 129 | `knowledge/pipelines/validation_pipeline.py.py` | B | `knowledge/validation/engine.py` | `ValidationEngine.validate_context` | validation_pipeline.py | KG-040-044 | BLOCK-009 | test_w9_validation.py | Pipeline |
| 130 | `knowledge/reasoning/consistency_reasoner.py` | C | `knowledge/validation/conflicts.py + w10/classification.py` | `detect_conflicts; classify_evidence_item` | consistency_reasoner.py | KG-044/045 | BLOCK-009/011 | test_w9_validation.py | Reasoning |
| 131 | `knowledge/reasoning/dependency_reasoner.py` | C | `knowledge/reasoning/w10/chains.py` | `EvidenceChainBuilder` | dependency_reasoner.py | KG-046 | BLOCK-011 | test_w10_reasoning.py | Reasoning |
| 132 | `knowledge/reasoning/engineering_reasoner.py` | B | `knowledge/reasoning/reasoner.py + w10/reasoner.py` | `ProvenanceAwareReasoner; W10ProvenanceAwareReasoner` | engineering_reasoner.py | KG-045 | BLOCK-004/011 | test_reasoning.py; test_w10_reasoning.py | Reasoning |
| 133 | `knowledge/reasoning/equation_reasoner.py` | E | `—` | `—` | equation_reasoner.py | KG-045 | — | NO | Reasoning |
| 134 | `knowledge/reasoning/recommendation_engine.py` | D | `knowledge/interface/rag.py` | `ControlledRAGOrchestrator (retrieval only)` | recommendation_engine.py | KG-048 | BLOCK-011 | test_w11_interface.py | Superseded by controlled RAG |
| 135 | `knowledge/reasoning/traceability_engine.py` | C | `knowledge/reasoning/w10/chains.py` | `EvidenceChainBuilder.build_chain` | traceability_engine.py | KG-046 | BLOCK-011 | test_w10_reasoning.py | Reasoning |
| 136 | `knowledge/repositories/chapter_repository.py` | E | `—` | `—` | chapter repository | — | — | NO | Entity repo deferred — graph store primary |
| 137 | `knowledge/repositories/component_repository.py` | E | `—` | `—` | component repository | — | — | NO | Entity repo deferred — graph store primary |
| 138 | `knowledge/repositories/constant_repository.py` | E | `—` | `—` | constant repository | — | — | NO | Entity repo deferred — graph store primary |
| 139 | `knowledge/repositories/correlation_repository.py` | E | `—` | `—` | correlation repository | — | — | NO | Entity repo deferred — graph store primary |
| 140 | `knowledge/repositories/design_rule_repository.py` | E | `—` | `—` | design_rule repository | — | — | NO | Entity repo deferred — graph store primary |
| 141 | `knowledge/repositories/document_repository.py` | B | `knowledge/repository/repository.py` | `DocumentRepository` | Document persistence | Pre-KG | — | test_repository.py | Singular repository path |
| 142 | `knowledge/repositories/equation_repository.py` | E | `—` | `—` | equation repository | — | — | NO | Entity repo deferred — graph store primary |
| 143 | `knowledge/repositories/figure_repository.py` | E | `—` | `—` | figure repository | — | — | NO | Entity repo deferred — graph store primary |
| 144 | `knowledge/repositories/material_repository.py` | E | `—` | `—` | material repository | — | — | NO | Entity repo deferred — graph store primary |
| 145 | `knowledge/repositories/property_repository.py` | E | `—` | `—` | property repository | — | — | NO | Entity repo deferred — graph store primary |
| 146 | `knowledge/repositories/repository_manager.py` | C | `knowledge/repository/source_registry.py` | `SourceRegistry` | Repository management | KG-005 | BLOCK-001 | test_source_registry.py | Source registry |
| 147 | `knowledge/repositories/section_repository.py` | E | `—` | `—` | section repository | — | — | NO | Entity repo deferred — graph store primary |
| 148 | `knowledge/repositories/simulation_repository.py` | E | `—` | `—` | simulation repository | — | — | NO | Entity repo deferred — graph store primary |
| 149 | `knowledge/repositories/subsystem_repository.py` | E | `—` | `—` | subsystem repository | — | — | NO | Entity repo deferred — graph store primary |
| 150 | `knowledge/repositories/table_repository.py` | E | `—` | `—` | table repository | — | — | NO | Entity repo deferred — graph store primary |
| 151 | `knowledge/repositories/variable_repository.py` | E | `—` | `—` | variable repository | — | — | NO | Entity repo deferred — graph store primary |
| 152 | `knowledge/search/citation_search.py` | E | `—` | `—` | citation_search.py | KG-038 | — | NO | Search |
| 153 | `knowledge/search/equation_search.py` | E | `—` | `—` | equation_search.py | KG-036 | — | NO | Search |
| 154 | `knowledge/search/graph_search.py` | B | `knowledge/search/w8/graph_search.py` | `GraphSearchEngine` | graph_search.py | KG-038 | BLOCK-010 | test_w8_search.py | Search |
| 155 | `knowledge/search/hybrid_search.py` | B | `knowledge/search/w8/hybrid.py` | `HybridSearchEngine` | hybrid_search.py | KG-039 | BLOCK-010 | test_w8_search.py | Search |
| 156 | `knowledge/search/keyword_search.py` | B | `knowledge/search/w8/keyword.py` | `KeywordSearchEngine` | keyword_search.py | KG-036 | BLOCK-010 | test_w8_search.py | Search |
| 157 | `knowledge/search/search_engine.py` | B | `knowledge/search/engine.py` | `KnowledgeSearchEngine` | search_engine.py | KG-036-039 | BLOCK-004 | test_search.py | Search |
| 158 | `knowledge/search/semantic_search.py` | B | `knowledge/search/w8/semantic.py` | `SemanticVectorSearchEngine` | semantic_search.py | KG-037 | BLOCK-010 | test_w8_search.py | Search |
| 159 | `knowledge/search/variable_search.py` | E | `—` | `—` | variable_search.py | KG-036 | — | NO | Search |
| 160 | `knowledge/utils/equation_utils.py` | C | `knowledge/parsers/w3/equations.py + extraction/w4/equations.py` | `extract_equations; extract_equation_candidates` | equation_utils.py | KG-017/021 | BLOCK-006/007 | test_w4_extraction.py | Utils |
| 161 | `knowledge/utils/graph_utils.py` | C | `knowledge/graph/serialization.py + query.py` | `canonical_graph_record_digest; GraphQueryService` | graph_utils.py | KG-032 | BLOCK-003 | test_serialization.py | Utils |
| 162 | `knowledge/utils/hashing.py` | B | `knowledge/source/integrity.py` | `sha256_text_digest; sha256_bytes_digest` | hashing.py | KG-006 | BLOCK-005 | test_source.py | Utils |
| 163 | `knowledge/utils/logging_utils.py` | D | `core project logging (outside knowledge/)` | `—` | logging_utils.py | — | — | test_logger.py | Superseded by project-level logging |
| 164 | `knowledge/utils/markdown_utils.py` | B | `knowledge/ingestion_adapters/html.py` | `Markdown normalization` | markdown_utils.py | KG-012 | BLOCK-005 | test_adapters.py | Utils |
| 165 | `knowledge/utils/parsing_utils.py` | C | `knowledge/parsers/w3/structure.py + ingestion_adapters/normalize.py` | `parse_document_structure; normalize` | parsing_utils.py | KG-014 | BLOCK-005/006 | test_w3_parsing.py | Utils |
| 166 | `knowledge/utils/text_utils.py` | F | `—` | `—` | text_utils.py | — | — | NO | Utils |
| 167 | `knowledge/validation/ambiguity_detector.py` | E | `—` | `—` | ambiguity_detector.py | KG-044 | — | NO | Validation |
| 168 | `knowledge/validation/citation_validator.py` | E | `—` | `—` | citation_validator.py | KG-041 | — | NO | Validation |
| 169 | `knowledge/validation/consistency_validator.py` | B | `knowledge/validation/conflicts.py` | `detect_conflicts` | consistency_validator.py | KG-044 | BLOCK-009 | test_w9_validation.py | Validation |
| 170 | `knowledge/validation/dimension_validator.py` | C | `knowledge/validation/units.py` | `validate_units` | dimension_validator.py | KG-042 | BLOCK-009 | test_w9_validation.py | Validation |
| 171 | `knowledge/validation/duplicate_detector.py` | B | `knowledge/validation/duplicates.py` | `detect_duplicates` | duplicate_detector.py | KG-043 | BLOCK-009 | test_w9_validation.py | Validation |
| 172 | `knowledge/validation/equation_validator.py` | C | `knowledge/validation/schema.py` | `validate_schema` | equation_validator.py | KG-040 | BLOCK-009 | test_w9_validation.py | Validation |
| 173 | `knowledge/validation/ontology_validator.py` | B | `knowledge/ontology/validation.py` | `validate_taxonomy_edge` | ontology_validator.py | KG-024 | BLOCK-008 | test_w5_ontology.py | Validation |
| 174 | `knowledge/validation/source_validator.py` | C | `knowledge/validation/provenance.py + source/integrity.py` | `validate_provenance; verify_digest` | source_validator.py | KG-041 | BLOCK-005/009 | test_w9_validation.py | Validation |
| 175 | `knowledge/validation/unit_validator.py` | C | `knowledge/validation/units.py` | `validate_units` | unit_validator.py | KG-042 | BLOCK-009 | test_w9_validation.py | Validation |

---

## Reverse Inventory (Current Extra Files)

| # | Current Path | Disp | Architectural Role |
|---|--------------|------|--------------------|
| 1 | `knowledge/extraction/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 2 | `knowledge/extraction/claim.py` | H | Non-frozen path replacing frozen capability — see master table |
| 3 | `knowledge/extraction/entity.py` | H | Non-frozen path replacing frozen capability — see master table |
| 4 | `knowledge/extraction/equation.py` | H | Non-frozen path replacing frozen capability — see master table |
| 5 | `knowledge/extraction/exceptions.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 6 | `knowledge/extraction/w4/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 7 | `knowledge/extraction/w4/claims.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 8 | `knowledge/extraction/w4/entities.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 9 | `knowledge/extraction/w4/equations.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 10 | `knowledge/extraction/w4/exceptions.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 11 | `knowledge/extraction/w4/identity.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 12 | `knowledge/extraction/w4/models.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 13 | `knowledge/extraction/w4/pipeline.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 14 | `knowledge/extraction/w4/provenance.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 15 | `knowledge/extraction/w4/quantities.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 16 | `knowledge/extraction/w4/registry.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 17 | `knowledge/extraction/w4/relationships.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 18 | `knowledge/graph/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 19 | `knowledge/graph/construction.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 20 | `knowledge/graph/contracts.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 21 | `knowledge/graph/entity.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 22 | `knowledge/graph/exceptions.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 23 | `knowledge/graph/lifecycle.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 24 | `knowledge/graph/memory_store.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 25 | `knowledge/graph/provenance.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 26 | `knowledge/graph/query.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 27 | `knowledge/graph/relationship.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 28 | `knowledge/graph/repository.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 29 | `knowledge/graph/serialization.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 30 | `knowledge/graph/snapshot.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 31 | `knowledge/graph/source_identity.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 32 | `knowledge/graph/validation.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 33 | `knowledge/indexing/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 34 | `knowledge/indexing/builder.py` | H | Non-frozen path replacing frozen capability — see master table |
| 35 | `knowledge/indexing/exceptions.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 36 | `knowledge/indexing/lexical.py` | H | Non-frozen path replacing frozen capability — see master table |
| 37 | `knowledge/indexing/models.py` | H | Non-frozen path replacing frozen capability — see master table |
| 38 | `knowledge/indexing/semantic.py` | H | Non-frozen path replacing frozen capability — see master table |
| 39 | `knowledge/indexing/w7/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 40 | `knowledge/indexing/w7/bundle.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 41 | `knowledge/indexing/w7/graph_index.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 42 | `knowledge/indexing/w7/vector.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 43 | `knowledge/ingestion/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 44 | `knowledge/ingestion/base.py` | H | Non-frozen path replacing frozen capability — see master table |
| 45 | `knowledge/ingestion/exceptions.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 46 | `knowledge/ingestion/models.py` | H | Non-frozen path replacing frozen capability — see master table |
| 47 | `knowledge/ingestion_adapters/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 48 | `knowledge/ingestion_adapters/base.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 49 | `knowledge/ingestion_adapters/docx.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 50 | `knowledge/ingestion_adapters/exceptions.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 51 | `knowledge/ingestion_adapters/html.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 52 | `knowledge/ingestion_adapters/normalize.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 53 | `knowledge/ingestion_adapters/pdf.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 54 | `knowledge/ingestion_adapters/pptx.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 55 | `knowledge/ingestion_adapters/registry.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 56 | `knowledge/ingestion_adapters/repository.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 57 | `knowledge/ingestion_adapters/xlsx.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 58 | `knowledge/interface/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 59 | `knowledge/interface/context.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 60 | `knowledge/interface/cursor.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 61 | `knowledge/interface/engineering.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 62 | `knowledge/interface/exceptions.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 63 | `knowledge/interface/identity.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 64 | `knowledge/interface/models.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 65 | `knowledge/interface/rag.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 66 | `knowledge/models/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 67 | `knowledge/ontology/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 68 | `knowledge/ontology/aliases.py` | H | Non-frozen path replacing frozen capability — see master table |
| 69 | `knowledge/ontology/canonicalization.py` | H | Non-frozen path replacing frozen capability — see master table |
| 70 | `knowledge/ontology/exceptions.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 71 | `knowledge/ontology/identity.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 72 | `knowledge/ontology/models.py` | H | Non-frozen path replacing frozen capability — see master table |
| 73 | `knowledge/ontology/registry.py` | H | Non-frozen path replacing frozen capability — see master table |
| 74 | `knowledge/ontology/relationships.py` | H | Non-frozen path replacing frozen capability — see master table |
| 75 | `knowledge/ontology/taxonomy.py` | H | Non-frozen path replacing frozen capability — see master table |
| 76 | `knowledge/ontology/validation.py` | H | Non-frozen path replacing frozen capability — see master table |
| 77 | `knowledge/parsers/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 78 | `knowledge/parsers/base.py` | H | Non-frozen path replacing frozen capability — see master table |
| 79 | `knowledge/parsers/exceptions.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 80 | `knowledge/parsers/models.py` | H | Non-frozen path replacing frozen capability — see master table |
| 81 | `knowledge/parsers/pdf_normalizer.py` | H | Non-frozen path replacing frozen capability — see master table |
| 82 | `knowledge/parsers/w3/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 83 | `knowledge/parsers/w3/content.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 84 | `knowledge/parsers/w3/equations.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 85 | `knowledge/parsers/w3/exceptions.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 86 | `knowledge/parsers/w3/figures.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 87 | `knowledge/parsers/w3/identity.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 88 | `knowledge/parsers/w3/models.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 89 | `knowledge/parsers/w3/pipeline.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 90 | `knowledge/parsers/w3/references.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 91 | `knowledge/parsers/w3/registry.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 92 | `knowledge/parsers/w3/structure.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 93 | `knowledge/parsers/w3/tables.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 94 | `knowledge/reasoning/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 95 | `knowledge/reasoning/context.py` | H | Non-frozen path replacing frozen capability — see master table |
| 96 | `knowledge/reasoning/evidence.py` | H | Non-frozen path replacing frozen capability — see master table |
| 97 | `knowledge/reasoning/exceptions.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 98 | `knowledge/reasoning/reasoner.py` | H | Non-frozen path replacing frozen capability — see master table |
| 99 | `knowledge/reasoning/w10/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 100 | `knowledge/reasoning/w10/chains.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 101 | `knowledge/reasoning/w10/classification.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 102 | `knowledge/reasoning/w10/context.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 103 | `knowledge/reasoning/w10/identity.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 104 | `knowledge/reasoning/w10/models.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 105 | `knowledge/reasoning/w10/reasoner.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 106 | `knowledge/repository/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 107 | `knowledge/repository/repository.py` | H | Non-frozen path replacing frozen capability — see master table |
| 108 | `knowledge/repository/source_registry.py` | H | Non-frozen path replacing frozen capability — see master table |
| 109 | `knowledge/repository/source_repository.py` | H | Non-frozen path replacing frozen capability — see master table |
| 110 | `knowledge/search/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 111 | `knowledge/search/contracts.py` | H | Non-frozen path replacing frozen capability — see master table |
| 112 | `knowledge/search/engine.py` | H | Non-frozen path replacing frozen capability — see master table |
| 113 | `knowledge/search/exceptions.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 114 | `knowledge/search/w8/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 115 | `knowledge/search/w8/graph_search.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 116 | `knowledge/search/w8/hybrid.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 117 | `knowledge/search/w8/keyword.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 118 | `knowledge/search/w8/semantic.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 119 | `knowledge/search/w8/validation_aware.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 120 | `knowledge/source/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 121 | `knowledge/source/exceptions.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 122 | `knowledge/source/integrity.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 123 | `knowledge/source/license.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 124 | `knowledge/source/vault.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 125 | `knowledge/validation/__init__.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 126 | `knowledge/validation/conflicts.py` | H | Non-frozen path replacing frozen capability — see master table |
| 127 | `knowledge/validation/duplicates.py` | H | Non-frozen path replacing frozen capability — see master table |
| 128 | `knowledge/validation/engine.py` | H | Non-frozen path replacing frozen capability — see master table |
| 129 | `knowledge/validation/exceptions.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 130 | `knowledge/validation/identity.py` | G | KG block subpackage / W1-W2 extension / graph contract |
| 131 | `knowledge/validation/models.py` | H | Non-frozen path replacing frozen capability — see master table |
| 132 | `knowledge/validation/provenance.py` | H | Non-frozen path replacing frozen capability — see master table |
| 133 | `knowledge/validation/registry.py` | H | Non-frozen path replacing frozen capability — see master table |
| 134 | `knowledge/validation/rules.py` | H | Non-frozen path replacing frozen capability — see master table |
| 135 | `knowledge/validation/schema.py` | H | Non-frozen path replacing frozen capability — see master table |
| 136 | `knowledge/validation/units.py` | H | Non-frozen path replacing frozen capability — see master table |