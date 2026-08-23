"""One-shot reconciliation data generator for architecture audit. Not part of knowledge/."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

DISPOSITION = {
    "A": "EXACT_MATCH",
    "B": "RELOCATED",
    "C": "CONSOLIDATED",
    "D": "SUPERSEDED",
    "E": "MISSING_REQUIRED",
    "F": "MISSING_DECISION_REQUIRED",
    "G": "EXTRA_JUSTIFIED",
    "H": "EXTRA_REVIEW_REQUIRED",
}


def e(
    code: str,
    current: str,
    symbols: str,
    capability: str,
    kg: str,
    block: str,
    test: str,
    justification: str,
    deps: str = "",
    authority: str = "Part-3 FREEZED",
) -> dict[str, str]:
    return {
        "disposition": code,
        "disposition_label": DISPOSITION[code],
        "current": current,
        "symbols": symbols,
        "capability": capability,
        "kg": kg,
        "block": block,
        "test": test,
        "justification": justification,
        "dependencies": deps,
        "authority": authority,
    }


def build_registry() -> dict[str, dict[str, str]]:
    r: dict[str, dict[str, str]] = {}

    # Models
    for m, sym, kg, blk, tst in [
        ("document", "Document", "KG-014", "Pre-KG", "test_repository.py"),
        ("reference", "Reference", "KG-018", "Pre-KG", "INDIRECT"),
        ("equation", "Equation", "KG-021", "Pre-KG", "test_extraction.py"),
        ("variable", "Variable", "KG-021", "Pre-KG", "test_extraction.py"),
        ("constant", "Constant", "KG-020", "Pre-KG", "test_constant.py"),
        ("unit", "Unit", "KG-020/042", "BLOCK-007", "test_unit.py [FROZEN]"),
        ("dimension", "Dimension", "KG-020/042", "BLOCK-007", "test_dimension.py [FROZEN]"),
        ("quantity", "Quantity", "KG-020/042", "BLOCK-007", "test_quantity.py [FROZEN]"),
        ("material", "Material", "KG-019", "Pre-KG", "test_material.py"),
        ("subsystem", "Subsystem", "KG-019", "Pre-KG", "test_material.py"),
        ("engineering_domain", "EngineeringDomain", "KG-026", "Pre-KG", "test_ontology.py"),
    ]:
        r[f"knowledge/models/{m}.py"] = e(
            "A", f"knowledge/models/{m}.py", f"knowledge.models.{m}.{sym}",
            f"Canonical {m}", kg, blk, tst, "Exact path match",
        )

    model_entries = {
        "chapter.py": ("E", "—", "—", "Chapter model", "KG-014"),
        "section.py": ("E", "—", "—", "Section model", "KG-014"),
        "paragraph.py": ("C", "knowledge/parsers/w3/models.py", "ParsedParagraph", "Paragraph", "KG-014"),
        "sentence.py": ("F", "—", "—", "Sentence model", "KG-014"),
        "figure.py": ("C", "knowledge/parsers/w3/models.py", "ParsedFigure", "Figure", "KG-016"),
        "table.py": ("C", "knowledge/parsers/w3/models.py", "ParsedTable", "Table", "KG-015"),
        "appendix.py": ("E", "—", "—", "Appendix model", "KG-014"),
        "glossary.py": ("E", "—", "—", "Glossary model", "KG-014"),
        "citation.py": ("C", "knowledge/parsers/w3/models.py", "ParsedCitation", "Citation", "KG-018"),
        "physical_law.py": ("E", "—", "—", "Physical law", "KG-019+"),
        "correlation.py": ("E", "—", "—", "Correlation", "KG-019+"),
        "empirical_relation.py": ("F", "—", "—", "Empirical relation", "—"),
        "assumption.py": ("E", "—", "—", "Assumption", "KG-022"),
        "boundary_condition.py": ("E", "—", "—", "Boundary condition", "KG-019+"),
        "property.py": ("E", "—", "—", "Property", "KG-019"),
        "component.py": ("C", "knowledge/graph/entity.py", "CanonicalEntityType", "Component typing", "KG-019"),
        "process.py": ("E", "—", "—", "Process", "KG-019"),
        "manufacturing_process.py": ("E", "—", "—", "Manufacturing process", "KG-019"),
        "experiment.py": ("E", "—", "—", "Experiment", "KG-019"),
        "simulation.py": ("E", "—", "—", "Simulation", "KG-019"),
        "design_rule.py": ("E", "—", "—", "Design rule", "KG-019"),
        "failure_mode.py": ("E", "—", "—", "Failure mode", "KG-019"),
        "ontology_node.py": ("C", "knowledge/ontology/models.py", "OntologyTerm", "Ontology node", "KG-024"),
        "ontology_edge.py": ("C", "knowledge/ontology/models.py", "TaxonomyEdge", "Ontology edge", "KG-026"),
        "metadata.py": ("C", "knowledge/ingestion/models.py", "IngestionResult", "Metadata", "KG-009"),
    }
    for fname, (code, cur, sym, cap, kg) in model_entries.items():
        blk = "BLOCK-006" if code in {"C", "B"} and "parsers" in cur else "—"
        tst = "test_w3_parsing.py" if "parsers" in cur else ("test_w5_ontology.py" if "ontology" in cur else "NO")
        r[f"knowledge/models/{fname}"] = e(code, cur, sym, cap, kg, blk, tst, f"Model disposition {code}")

    # Ingestion
    ing = {
        "ingestion_pipeline.py": ("C", "knowledge/ingestion_adapters/registry.py", "IngestionOrchestrator", "KG-009-013", "BLOCK-005", "test_adapters.py"),
        "batch_loader.py": ("E", "—", "—", "KG-013", "—", "NO"),
        "metadata_loader.py": ("C", "knowledge/ingestion/models.py", "IngestionResult", "KG-009", "BLOCK-002", "test_ingestion.py"),
        "pdf_loader.py": ("B", "knowledge/ingestion_adapters/pdf.py", "PdfIngestionAdapter.ingest", "KG-009", "BLOCK-005", "test_adapters.py"),
        "epub_loader.py": ("E", "—", "—", "KG-010", "—", "NO"),
        "docx_loader.py": ("B", "knowledge/ingestion_adapters/docx.py", "DocxIngestionAdapter.ingest", "KG-010", "BLOCK-005", "test_adapters.py"),
        "markdown_loader.py": ("B", "knowledge/ingestion_adapters/html.py", "MarkdownIngestionAdapter.ingest", "KG-012", "BLOCK-005", "test_adapters.py"),
        "html_loader.py": ("B", "knowledge/ingestion_adapters/html.py", "HtmlIngestionAdapter.ingest", "KG-012", "BLOCK-005", "test_adapters.py"),
        "latex_loader.py": ("E", "—", "—", "KG-012", "—", "NO"),
        "image_loader.py": ("E", "—", "—", "KG-016", "—", "NO"),
        "ocr_loader.py": ("E", "—", "—", "KG-016", "—", "NO"),
        "markitdown_loader.py": ("E", "—", "—", "KG-009", "—", "NO"),
    }
    for f, (code, cur, sym, kg, blk, tst) in ing.items():
        r[f"knowledge/ingestion/{f}"] = e(code, cur, sym, f.replace("_", " "), kg, blk, tst, "Ingestion layer")

    # Parsers
    par = {
        "document_parser.py": ("C", "knowledge/parsers/w3/pipeline.py", "parse_document", "KG-014", "BLOCK-006", "test_w3_parsing.py"),
        "chapter_parser.py": ("C", "knowledge/parsers/w3/structure.py", "parse_document_structure", "KG-014", "BLOCK-006", "test_w3_parsing.py"),
        "section_parser.py": ("C", "knowledge/parsers/w3/structure.py", "parse_document_structure", "KG-014", "BLOCK-006", "test_w3_parsing.py"),
        "heading_parser.py": ("C", "knowledge/parsers/w3/structure.py", "parse_document_structure", "KG-014", "BLOCK-006", "test_w3_parsing.py"),
        "paragraph_parser.py": ("C", "knowledge/parsers/w3/structure.py", "parse_document_structure", "KG-014", "BLOCK-006", "test_w3_parsing.py"),
        "sentence_parser.py": ("F", "—", "—", "KG-014", "—", "NO"),
        "figure_parser.py": ("B", "knowledge/parsers/w3/figures.py", "extract_figures", "KG-016", "BLOCK-006", "test_w3_parsing.py"),
        "table_parser.py": ("B", "knowledge/parsers/w3/tables.py", "extract_tables", "KG-015", "BLOCK-006", "test_w3_parsing.py"),
        "bibliography_parser.py": ("C", "knowledge/parsers/w3/references.py", "extract_references", "KG-018", "BLOCK-006", "test_w3_parsing.py"),
        "citation_parser.py": ("C", "knowledge/parsers/w3/references.py", "extract_citations", "KG-018", "BLOCK-006", "test_w3_parsing.py"),
        "appendix_parser.py": ("E", "—", "—", "KG-014", "—", "NO"),
        "glossary_parser.py": ("E", "—", "—", "KG-014", "—", "NO"),
        "metadata_parser.py": ("C", "knowledge/parsers/w3/content.py", "ParseContext", "KG-014", "BLOCK-006", "test_w3_parsing.py"),
    }
    for f, (code, cur, sym, kg, blk, tst) in par.items():
        r[f"knowledge/parsers/{f}"] = e(code, cur, sym, f, kg, blk, tst, "Parser layer")

    # Extraction - key files
    ext = {
        "extraction_pipeline.py": ("B", "knowledge/extraction/w4/pipeline.py", "extract_document; W4ExtractionPipeline", "KG-019-023", "BLOCK-007", "test_w4_extraction.py"),
        "equation_extractor.py": ("C", "knowledge/extraction/w4/equations.py", "extract_equation_candidates", "KG-021", "BLOCK-007", "test_w4_extraction.py"),
        "variable_extractor.py": ("C", "knowledge/extraction/w4/entities.py", "extract_entities", "KG-021", "BLOCK-007", "test_w4_extraction.py"),
        "quantity_extractor.py": ("B", "knowledge/extraction/w4/quantities.py", "extract_quantities", "KG-020", "BLOCK-007", "test_w4_extraction.py"),
        "material_extractor.py": ("C", "knowledge/extraction/w4/entities.py", "extract_entities", "KG-019", "BLOCK-007", "test_w4_extraction.py"),
    }
    for f, (code, cur, sym, kg, blk, tst) in ext.items():
        r[f"knowledge/extraction/{f}"] = e(code, cur, sym, f, kg, blk, tst, "Extraction")
    for name in [
        "constant_extractor", "unit_extractor", "dimension_extractor", "property_extractor",
        "component_extractor", "subsystem_extractor", "engineering_domain_extractor",
        "process_extractor", "manufacturing_extractor", "experiment_extractor",
        "simulation_extractor", "failure_mode_extractor", "design_rule_extractor",
        "physical_law_extractor", "correlation_extractor", "assumption_extractor",
        "boundary_condition_extractor", "glossary_extractor", "abbreviation_extractor",
    ]:
        if f"knowledge/extraction/{name}.py" not in r:
            mapped = ("C", "knowledge/extraction/w4/entities.py", "extract_entities", "KG-019", "BLOCK-007", "test_w4_extraction.py") if name.endswith("_extractor") and name.split("_")[0] in {"component","subsystem","engineering","constant","unit","dimension","material"} else ("E", "—", "—", "KG-019", "—", "NO")
            r[f"knowledge/extraction/{name}.py"] = e(*mapped, f"Extraction {name}", "W4")

    # Ontology
    r["knowledge/ontology/ontology_manager.py"] = e("B", "knowledge/ontology/registry.py", "OntologyRegistry", "Ontology management", "KG-024", "BLOCK-008", "test_w5_ontology.py", "Registry replaces manager")
    r["knowledge/ontology/engineering_domains.py"] = e("C", "knowledge/ontology/registry.py + ontology/models.py", "OntologyRegistry; EngineeringDomain taxonomy", "Engineering domain taxonomy", "KG-026", "BLOCK-008", "test_w5_ontology.py", "Static domain module consolidated into registry + models")
    for d in "propulsion thermodynamics thermochemistry combustion fluid_mechanics compressible_flow heat_transfer cryogenics materials structures manufacturing controls optimization aerospace".split():
        r[f"knowledge/ontology/{d}.py"] = e("D", "knowledge/ontology/registry.py", "OntologyRegistry.register_term", f"Domain {d}", "KG-026", "BLOCK-008", "test_w5_ontology.py", "Static module superseded by registry")

    # Graph
    gmap = {
        "graph_manager.py": ("C", "knowledge/graph/construction.py + query.py", "GraphConstructor.construct; GraphQueryService", "KG-028-031", "BLOCK-003", "test_construction.py; test_query.py"),
        "dependency_graph.py": ("C", "knowledge/graph/query.py", "GraphQueryService.traverse", "KG-030", "BLOCK-003", "test_query.py"),
        "equation_graph.py": ("C", "knowledge/graph/construction.py", "GraphConstructor", "KG-028", "BLOCK-003", "test_construction.py"),
        "variable_graph.py": ("C", "knowledge/graph/construction.py", "GraphConstructor", "KG-028", "BLOCK-003", "test_construction.py"),
        "engineering_graph.py": ("C", "knowledge/graph/construction.py", "GraphConstructor", "KG-028", "BLOCK-003", "test_construction.py"),
        "citation_graph.py": ("E", "—", "—", "KG-038", "—", "NO"),
        "concept_graph.py": ("F", "—", "—", "KG-035", "—", "NO"),
        "relationship_builder.py": ("B", "knowledge/graph/construction.py", "GraphConstructor + extraction/w4/relationships.py", "KG-023", "BLOCK-003/007", "test_construction.py"),
    }
    for f, (code, cur, sym, kg, blk, tst) in gmap.items():
        r[f"knowledge/graph/{f}"] = e(code, cur, sym, f, kg, blk, tst, "Graph layer")

    # Repositories
    r["knowledge/repositories/repository_manager.py"] = e("C", "knowledge/repository/source_registry.py", "SourceRegistry", "Repository management", "KG-005", "BLOCK-001", "test_source_registry.py", "Source registry")
    r["knowledge/repositories/document_repository.py"] = e("B", "knowledge/repository/repository.py", "DocumentRepository", "Document persistence", "Pre-KG", "—", "test_repository.py", "Singular repository path")
    for repo in "chapter section equation variable constant material property component subsystem figure table design_rule correlation simulation".split():
        r[f"knowledge/repositories/{repo}_repository.py"] = e("E", "—", "—", f"{repo} repository", "—", "—", "NO", "Entity repo deferred — graph store primary")

    # Indexing
    idx = {
        "index_manager.py": ("C", "knowledge/indexing/builder.py + w7/bundle.py", "KnowledgeIndexBuilder.build; W7IndexBuilder.build", "KG-033-035", "BLOCK-004/010", "test_indexing.py; test_w7_indexing.py"),
        "keyword_index.py": ("B", "knowledge/indexing/lexical.py", "InMemoryLexicalIndex", "KG-033", "BLOCK-004", "test_indexing.py"),
        "semantic_index.py": ("B", "knowledge/indexing/semantic.py + w7/vector.py", "InMemorySemanticIndex; InMemoryVectorIndex", "KG-034", "BLOCK-004/010", "test_indexing.py"),
        "graph_index.py": ("B", "knowledge/indexing/w7/graph_index.py", "InMemoryGraphIndex", "KG-035", "BLOCK-010", "test_w7_indexing.py"),
        "equation_index.py": ("E", "—", "—", "KG-033", "—", "NO"),
        "variable_index.py": ("E", "—", "—", "KG-033", "—", "NO"),
        "citation_index.py": ("E", "—", "—", "KG-033", "—", "NO"),
    }
    for f, (code, cur, sym, kg, blk, tst) in idx.items():
        r[f"knowledge/indexing/{f}"] = e(code, cur, sym, f, kg, blk, tst, "Indexing")

    # Search
    srch = {
        "search_engine.py": ("B", "knowledge/search/engine.py", "KnowledgeSearchEngine", "KG-036-039", "BLOCK-004", "test_search.py"),
        "keyword_search.py": ("B", "knowledge/search/w8/keyword.py", "KeywordSearchEngine", "KG-036", "BLOCK-010", "test_w8_search.py"),
        "semantic_search.py": ("B", "knowledge/search/w8/semantic.py", "SemanticVectorSearchEngine", "KG-037", "BLOCK-010", "test_w8_search.py"),
        "hybrid_search.py": ("B", "knowledge/search/w8/hybrid.py", "HybridSearchEngine", "KG-039", "BLOCK-010", "test_w8_search.py"),
        "graph_search.py": ("B", "knowledge/search/w8/graph_search.py", "GraphSearchEngine", "KG-038", "BLOCK-010", "test_w8_search.py"),
        "equation_search.py": ("E", "—", "—", "KG-036", "—", "NO"),
        "variable_search.py": ("E", "—", "—", "KG-036", "—", "NO"),
        "citation_search.py": ("E", "—", "—", "KG-038", "—", "NO"),
    }
    for f, (code, cur, sym, kg, blk, tst) in srch.items():
        r[f"knowledge/search/{f}"] = e(code, cur, sym, f, kg, blk, tst, "Search")

    # Reasoning
    rsn = {
        "engineering_reasoner.py": ("B", "knowledge/reasoning/reasoner.py + w10/reasoner.py", "ProvenanceAwareReasoner; W10ProvenanceAwareReasoner", "KG-045", "BLOCK-004/011", "test_reasoning.py; test_w10_reasoning.py"),
        "equation_reasoner.py": ("E", "—", "—", "KG-045", "—", "NO"),
        "dependency_reasoner.py": ("C", "knowledge/reasoning/w10/chains.py", "EvidenceChainBuilder", "KG-046", "BLOCK-011", "test_w10_reasoning.py"),
        "consistency_reasoner.py": ("C", "knowledge/validation/conflicts.py + w10/classification.py", "detect_conflicts; classify_evidence_item", "KG-044/045", "BLOCK-009/011", "test_w9_validation.py"),
        "recommendation_engine.py": ("D", "knowledge/interface/rag.py", "ControlledRAGOrchestrator (retrieval only)", "KG-048", "BLOCK-011", "test_w11_interface.py", "Superseded by controlled RAG"),
        "traceability_engine.py": ("C", "knowledge/reasoning/w10/chains.py", "EvidenceChainBuilder.build_chain", "KG-046", "BLOCK-011", "test_w10_reasoning.py"),
    }
    for f, row in rsn.items():
        code, cur, sym, kg, blk, tst = row[:6]
        just = row[6] if len(row) > 6 else "Reasoning"
        r[f"knowledge/reasoning/{f}"] = e(code, cur, sym, f, kg, blk, tst, just)

    # Validation
    val = {
        "source_validator.py": ("C", "knowledge/validation/provenance.py + source/integrity.py", "validate_provenance; verify_digest", "KG-041", "BLOCK-005/009", "test_w9_validation.py"),
        "citation_validator.py": ("E", "—", "—", "KG-041", "—", "NO"),
        "equation_validator.py": ("C", "knowledge/validation/schema.py", "validate_schema", "KG-040", "BLOCK-009", "test_w9_validation.py"),
        "dimension_validator.py": ("C", "knowledge/validation/units.py", "validate_units", "KG-042", "BLOCK-009", "test_w9_validation.py"),
        "unit_validator.py": ("C", "knowledge/validation/units.py", "validate_units", "KG-042", "BLOCK-009", "test_w9_validation.py"),
        "ontology_validator.py": ("B", "knowledge/ontology/validation.py", "validate_taxonomy_edge", "KG-024", "BLOCK-008", "test_w5_ontology.py"),
        "consistency_validator.py": ("B", "knowledge/validation/conflicts.py", "detect_conflicts", "KG-044", "BLOCK-009", "test_w9_validation.py"),
        "duplicate_detector.py": ("B", "knowledge/validation/duplicates.py", "detect_duplicates", "KG-043", "BLOCK-009", "test_w9_validation.py"),
        "ambiguity_detector.py": ("E", "—", "—", "KG-044", "—", "NO"),
    }
    for f, (code, cur, sym, kg, blk, tst) in val.items():
        r[f"knowledge/validation/{f}"] = e(code, cur, sym, f, kg, blk, tst, "Validation")

    # Exporters, pipelines, utils
    for name in ["markdown_exporter", "json_exporter", "yaml_exporter", "html_exporter", "latex_exporter", "graph_exporter", "database_exporter"]:
        r[f"knowledge/exporters/{name}.py"] = e("E", "—", "—", "Export", "—", "—", "NO", "Exporter package not implemented")
    pipes = {
        "document_pipeline.py": ("C", "tests/integration_tests/kg_block012/helpers/pipeline.py", "run_full_pipeline", "KG-012", "BLOCK-012", "kg_block012 E2E"),
        "extraction_pipeline.py": ("B", "knowledge/extraction/w4/pipeline.py", "extract_document", "KG-019-023", "BLOCK-007", "test_w4_extraction.py"),
        "indexing_pipeline.py": ("C", "knowledge/indexing/w7/bundle.py", "W7IndexBuilder.build", "KG-033-035", "BLOCK-010", "test_w7_indexing.py"),
        "validation_pipeline.py": ("B", "knowledge/validation/engine.py", "ValidationEngine.validate_context", "KG-040-044", "BLOCK-009", "test_w9_validation.py"),
        "knowledge_pipeline.py": ("C", "tests/integration_tests/kg_block012/helpers/pipeline.py", "run_full_pipeline", "KG-012", "BLOCK-012", "kg_block012 E2E"),
    }
    for f, (code, cur, sym, kg, blk, tst) in pipes.items():
        r[f"knowledge/pipelines/{f}.py"] = e(code, cur, sym, f, kg, blk, tst, "Pipeline")
    utils = {
        "hashing.py": ("B", "knowledge/source/integrity.py", "sha256_text_digest; sha256_bytes_digest", "KG-006", "BLOCK-005", "test_source.py"),
        "parsing_utils.py": ("C", "knowledge/parsers/w3/structure.py + ingestion_adapters/normalize.py", "parse_document_structure; normalize", "KG-014", "BLOCK-005/006", "test_w3_parsing.py"),
        "equation_utils.py": ("C", "knowledge/parsers/w3/equations.py + extraction/w4/equations.py", "extract_equations; extract_equation_candidates", "KG-017/021", "BLOCK-006/007", "test_w4_extraction.py"),
        "markdown_utils.py": ("B", "knowledge/ingestion_adapters/html.py", "Markdown normalization", "KG-012", "BLOCK-005", "test_adapters.py"),
        "graph_utils.py": ("C", "knowledge/graph/serialization.py + query.py", "canonical_graph_record_digest; GraphQueryService", "KG-032", "BLOCK-003", "test_serialization.py"),
        "text_utils.py": ("F", "—", "—", "—", "—", "NO"),
        "logging_utils.py": ("D", "core project logging (outside knowledge/)", "—", "—", "—", "test_logger.py", "Superseded by project-level logging"),
    }
    for f, row in utils.items():
        code, cur, sym, kg, blk, tst = row[:6]
        just = row[6] if len(row) > 6 else "Utils"
        r[f"knowledge/utils/{f}"] = e(code, cur, sym, f, kg, blk, tst, just)

    r["knowledge/__init__.py"] = e("A", "knowledge/__init__.py", "—", "Package root", "—", "—", "N/A", "Exact match")

    return r


if __name__ == "__main__":
    reg = build_registry()
    counts = Counter(v["disposition"] for v in reg.values())
    out = Path(__file__).parent / "kg_reconciliation_registry.json"
    out.write_text(json.dumps({"counts": dict(counts), "total": len(reg), "entries": reg}, indent=2))
    print(f"Wrote {len(reg)} entries to {out}")
    for k, v in sorted(counts.items()):
        print(f"  {k} ({DISPOSITION[k]}): {v}")
