"""Unit tests for KG-BLOCK-013 Phase C validation capabilities."""

from __future__ import annotations

from pathlib import Path

from knowledge.ontology import (
    OntologyAlias,
    OntologyRegistry,
    OntologyTerm,
    canonicalize_extraction_result,
)
from knowledge.graph.entity import CanonicalEntityType
from knowledge.parsers.w3 import ParseContext, parse_document
from knowledge.validation import (
    ValidationContext,
    detect_ambiguities,
    validate_citations,
    validate_context,
    validate_context_extended,
)
from knowledge.ingestion import (
    IngestionArtifactRef,
    IngestionRequest,
    IngestionStage,
    SourceFormat,
)
from knowledge.ingestion_adapters import MarkdownIngestionAdapter
from knowledge.source import InMemorySourceVault, VaultArtifact, VaultArtifactMetadata
from knowledge.source.integrity import sha256_text_digest
from knowledge.extraction.w4 import ExtractionContext, extract_document

_GOLDEN_DOCUMENT = (
    Path(__file__).resolve().parents[3]
    / "integration_tests"
    / "kg_block012"
    / "fixtures"
    / "documents"
    / "golden_propulsion_spec.md"
)


def _build_registry() -> OntologyRegistry:
    registry = OntologyRegistry()
    registry.register_term(
        OntologyTerm(
            term_id="term-material-lox",
            canonical_name="Liquid Oxygen",
            entity_type=CanonicalEntityType.MATERIAL,
            aliases=(
                OntologyAlias(
                    alias="LOX",
                    canonical_term_id="term-material-lox",
                ),
            ),
        ),
    )
    return registry


def _parse_pipeline(content: str):
    normalized = "\n".join(
        line.rstrip()
        for line in content.replace("\r\n", "\n").split("\n")
    )
    digest = sha256_text_digest(normalized)
    vault = InMemorySourceVault()
    vault.store(
        VaultArtifact(
            source_id="SRC-PHASE-C",
            artifact_id="ART-PHASE-C",
            content=normalized.encode("utf-8"),
            content_hash=digest,
            metadata=VaultArtifactMetadata(
                source_format=SourceFormat.MARKDOWN.value,
            ),
        ),
    )
    artifact = IngestionArtifactRef(
        source_id="SRC-PHASE-C",
        artifact_id="ART-PHASE-C",
        source_format=SourceFormat.MARKDOWN,
        content_hash=digest,
    )
    adapter = MarkdownIngestionAdapter(vault)
    ingestion = adapter.ingest(
        IngestionRequest(
            artifact=artifact,
            adapter_name=adapter.adapter_name,
            adapter_version=adapter.adapter_version,
        ),
    )
    parse_result = parse_document(
        ParseContext(
            ingestion_result=ingestion,
            normalized_content=normalized,
        ),
    )
    assert parse_result.ingestion_result.stage is IngestionStage.PARSED
    extraction = extract_document(
        ExtractionContext(
            parsed_document=parse_result.parsed_document,
            normalized_content=normalized,
        ),
    )
    return parse_result.parsed_document, extraction


def test_citation_validator_flags_unresolved_citation_key() -> None:
    """Citation validator must warn on unresolved citation keys."""

    content = "\n".join(
        [
            "# Spec",
            "",
            "Design guidance [unknown-ref].",
            "",
            "# References",
            "",
            "1. NASA SP-125 (2020)",
        ],
    )
    parsed_document, extraction = _parse_pipeline(content)
    findings = validate_citations(
        ValidationContext(
            document_id=extraction.document_id,
            extraction_result=extraction,
            parsed_document=parsed_document,
        ),
    )

    assert any(finding.rule_id == "VAL-CIT-001" for finding in findings)


def test_citation_validator_flags_orphan_reference() -> None:
    """Citation validator must warn when bibliography entries are never cited."""

    content = "\n".join(
        [
            "# Spec",
            "",
            "No citations here.",
            "",
            "# References",
            "",
            "1. NASA SP-125 (2020)",
        ],
    )
    parsed_document, extraction = _parse_pipeline(content)
    findings = validate_citations(
        ValidationContext(
            parsed_document=parsed_document,
            extraction_result=extraction,
        ),
    )

    assert any(finding.rule_id == "VAL-CIT-003" for finding in findings)


def test_ambiguity_detector_flags_conflicting_section() -> None:
    """Ambiguity detector must flag explicitly conflicting sections."""

    content = _GOLDEN_DOCUMENT.read_text(encoding="utf-8")
    parsed_document, extraction = _parse_pipeline(content)
    findings = detect_ambiguities(
        ValidationContext(
            parsed_document=parsed_document,
            extraction_result=extraction,
        ),
    )

    assert any(finding.rule_id == "VAL-AMB-002" for finding in findings)


def test_validate_context_extended_includes_phase_c_findings() -> None:
    """Extended validation must include Phase-C findings beyond base W9."""

    content = _GOLDEN_DOCUMENT.read_text(encoding="utf-8")
    parsed_document, extraction = _parse_pipeline(content)
    registry = _build_registry()
    canonical = canonicalize_extraction_result(extraction, registry)
    context = ValidationContext(
        document_id=extraction.document_id,
        source_id=extraction.source_id,
        extraction_result=extraction,
        canonicalization_result=canonical,
        parsed_document=parsed_document,
    )

    base_report = validate_context(context)
    extended_report = validate_context_extended(context)

    assert len(extended_report.findings) >= len(base_report.findings)
    assert any(
        finding.rule_id.startswith("VAL-CIT")
        or finding.rule_id.startswith("VAL-AMB")
        for finding in extended_report.findings
    )


def test_validate_context_extended_is_deterministic() -> None:
    """Extended validation output must be deterministic."""

    content = _GOLDEN_DOCUMENT.read_text(encoding="utf-8")
    parsed_document, extraction = _parse_pipeline(content)
    context = ValidationContext(
        document_id=extraction.document_id,
        extraction_result=extraction,
        parsed_document=parsed_document,
    )

    first = validate_context_extended(context)
    second = validate_context_extended(context)

    assert first.report_digest == second.report_digest
    assert first.to_mapping() == second.to_mapping()
