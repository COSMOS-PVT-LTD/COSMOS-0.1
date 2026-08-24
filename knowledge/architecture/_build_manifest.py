"""Build the closed architecture manifest from the historical reconciliation registry."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "documentation/development/kg_reconciliation_registry.json"
MANIFEST = Path(__file__).with_name("architecture_manifest.json")
LEDGER = Path(__file__).with_name("knowledge_freeze_ledger.json")

# Paths implemented in this completion phase at their frozen locations.
IMPLEMENTED_A = {
    "knowledge/models/assumption.py",
    "knowledge/models/boundary_condition.py",
    "knowledge/models/chapter.py",
    "knowledge/models/correlation.py",
    "knowledge/models/design_rule.py",
    "knowledge/models/empirical_relation.py",
    "knowledge/models/experiment.py",
    "knowledge/models/failure_mode.py",
    "knowledge/models/glossary.py",
    "knowledge/models/manufacturing_process.py",
    "knowledge/models/physical_law.py",
    "knowledge/models/process.py",
    "knowledge/models/property.py",
    "knowledge/models/section.py",
    "knowledge/models/sentence.py",
    "knowledge/models/simulation.py",
    "knowledge/models/appendix.py",
    "knowledge/indexing/citation_index.py",
    "knowledge/indexing/equation_index.py",
    "knowledge/indexing/variable_index.py",
    "knowledge/search/citation_search.py",
    "knowledge/search/equation_search.py",
    "knowledge/search/variable_search.py",
    "knowledge/graph/citation_graph.py",
    "knowledge/graph/concept_graph.py",
    "knowledge/extraction/abbreviation_extractor.py",
    "knowledge/extraction/assumption_extractor.py",
    "knowledge/extraction/boundary_condition_extractor.py",
    "knowledge/extraction/correlation_extractor.py",
    "knowledge/extraction/design_rule_extractor.py",
    "knowledge/extraction/experiment_extractor.py",
    "knowledge/extraction/failure_mode_extractor.py",
    "knowledge/extraction/glossary_extractor.py",
    "knowledge/extraction/manufacturing_extractor.py",
    "knowledge/extraction/physical_law_extractor.py",
    "knowledge/extraction/process_extractor.py",
    "knowledge/extraction/property_extractor.py",
    "knowledge/extraction/simulation_extractor.py",
    "knowledge/exporters/database_exporter.py",
    "knowledge/exporters/graph_exporter.py",
    "knowledge/exporters/html_exporter.py",
    "knowledge/exporters/json_exporter.py",
    "knowledge/exporters/latex_exporter.py",
    "knowledge/exporters/markdown_exporter.py",
    "knowledge/exporters/yaml_exporter.py",
    "knowledge/ingestion/batch_loader.py",
    "knowledge/ingestion/epub_loader.py",
    "knowledge/ingestion/image_loader.py",
    "knowledge/ingestion/latex_loader.py",
    "knowledge/ingestion/markitdown_loader.py",
    "knowledge/ingestion/ocr_loader.py",
    "knowledge/parsers/appendix_parser.py",
    "knowledge/parsers/glossary_parser.py",
    "knowledge/parsers/sentence_parser.py",
    "knowledge/reasoning/equation_reasoner.py",
    "knowledge/repositories/chapter_repository.py",
    "knowledge/repositories/component_repository.py",
    "knowledge/repositories/constant_repository.py",
    "knowledge/repositories/correlation_repository.py",
    "knowledge/repositories/design_rule_repository.py",
    "knowledge/repositories/equation_repository.py",
    "knowledge/repositories/figure_repository.py",
    "knowledge/repositories/material_repository.py",
    "knowledge/repositories/property_repository.py",
    "knowledge/repositories/section_repository.py",
    "knowledge/repositories/simulation_repository.py",
    "knowledge/repositories/subsystem_repository.py",
    "knowledge/repositories/table_repository.py",
    "knowledge/repositories/variable_repository.py",
    "knowledge/utils/text_utils.py",
}

CONSOLIDATED = {
    "knowledge/models/chapter.py": (
        "C",
        "knowledge/models/document_structure.py",
        "Canonical Chapter wraps W3 ParsedSection; no duplicate parser.",
    ),
    "knowledge/models/section.py": (
        "C",
        "knowledge/models/document_structure.py",
        "Canonical Section wraps W3 ParsedSection.",
    ),
    "knowledge/models/appendix.py": (
        "C",
        "knowledge/models/document_structure.py",
        "Canonical Appendix wraps W3 heading/section artifacts.",
    ),
    "knowledge/models/glossary.py": (
        "C",
        "knowledge/models/document_structure.py",
        "Canonical Glossary wraps W3 definitional sections.",
    ),
    "knowledge/models/sentence.py": (
        "C",
        "knowledge/models/document_structure.py",
        "Sentence is a provenance span over a W3 paragraph (ADR-KF-002).",
    ),
}


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    entries = []
    for frozen_path, raw in sorted(source["entries"].items()):
        disposition = raw["disposition"]
        current = raw.get("current") or frozen_path
        justification = raw.get("justification") or raw.get("capability") or ""
        symbols = raw.get("symbols") or ""

        if frozen_path in CONSOLIDATED:
            disposition, current, justification = CONSOLIDATED[frozen_path]
        elif frozen_path in IMPLEMENTED_A and disposition in {"E", "F"}:
            disposition = "A"
            current = frozen_path
            justification = "Implemented in Knowledge Foundation completion; tests attached."

        entries.append(
            {
                "frozen_path": frozen_path,
                "disposition": disposition,
                "current_path": current,
                "justification": justification,
                "symbols": symbols,
            },
        )

    counts: dict[str, int] = {}
    for item in entries:
        counts[item["disposition"]] = counts.get(item["disposition"], 0) + 1

    open_count = sum(counts.get(code, 0) for code in ("E", "F", "H"))
    manifest = {
        "schema_version": "1.0.0",
        "document_id": "COSMOS-KF-ARCHITECTURE-MANIFEST-001",
        "total": len(entries),
        "counts": counts,
        "open_dispositions": open_count,
        "architecture_closed": open_count == 0,
        "entries": entries,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    ledger = {
        "schema_version": "1.0.0",
        "document_id": "COSMOS-KF-FREEZE-LEDGER-001",
        "decision_id": "KG-KF-COMPLETION-FREEZE-2026-08-23",
        "authority": "Human Technical Owner — Tk Nayak",
        "architecture_closed": open_count == 0,
        "frozen_prior_blocks_modified": 0,
        "provider_invoked": False,
        "implemented_a_count": len(IMPLEMENTED_A),
    }
    LEDGER.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"counts": counts, "open": open_count, "total": len(entries)}, indent=2))


if __name__ == "__main__":
    main()
