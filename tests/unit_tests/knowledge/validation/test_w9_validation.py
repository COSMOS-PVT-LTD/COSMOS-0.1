"""Unit tests for KG-BLOCK-009 W9 validation (KG-040 → KG-044)."""

from __future__ import annotations

from knowledge.extraction.claim import ClaimConflictVisibility
from knowledge.graph import (
    GraphLifecycleState,
    GraphNode,
    GraphNodeIdentity,
    ImmutableGraphRecord,
)
from knowledge.ontology import (
    CanonicalizationStatus,
    OntologyAlias,
    OntologyRegistry,
    OntologyTerm,
    canonicalize_extraction_result,
)
from knowledge.graph.entity import CanonicalEntityType
from knowledge.validation import (
    ConflictClassification,
    DuplicateKind,
    ValidationCategory,
    ValidationContext,
    ValidationEngine,
    ValidationSeverity,
    ValidationStatus,
    detect_conflicts,
    detect_duplicates,
    validate_context,
    validate_provenance,
    validate_schema,
    validate_units,
)
from tests.unit_tests.knowledge.extraction.test_w4_extraction import (
    _parse_and_extract,
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


def test_schema_validation_accepts_valid_extraction() -> None:
    """KG-040 must accept structurally valid extraction output."""

    extraction = _parse_and_extract("Material: LOX\n")
    context = ValidationContext(
        document_id=extraction.document_id,
        source_id=extraction.source_id,
        extraction_result=extraction,
    )

    findings = validate_schema(context)

    assert not any(
        finding.status is ValidationStatus.INVALID
        and finding.severity in (ValidationSeverity.HIGH, ValidationSeverity.CRITICAL)
        for finding in findings
    )


def test_schema_validation_rejects_premature_approval() -> None:
    """KG-040 must reject extraction candidates in APPROVED lifecycle."""

    extraction = _parse_and_extract("Material: LOX\n")
    entity = extraction.entities[0]
    approved = entity.__class__(
        extraction_id=entity.extraction_id,
        document_id=entity.document_id,
        extracted_label=entity.extracted_label,
        entity_kind=entity.entity_kind,
        canonical_entity_type=entity.canonical_entity_type,
        provenance=entity.provenance,
        lifecycle_state=GraphLifecycleState.APPROVED,
    )
    mutated = extraction.__class__(
        document_id=extraction.document_id,
        source_id=extraction.source_id,
        artifact_id=extraction.artifact_id,
        extractor_name=extraction.extractor_name,
        extractor_version=extraction.extractor_version,
        entities=(approved,),
        quantities=extraction.quantities,
        equations=extraction.equations,
        claims=extraction.claims,
        relationships=extraction.relationships,
    )
    findings = validate_schema(
        ValidationContext(extraction_result=mutated),
    )

    assert any(finding.rule_id == "VAL-SCH-001" for finding in findings)


def test_schema_validation_flags_missing_relationship_endpoint() -> None:
    """KG-040 must detect relationship endpoints missing from batch."""

    extraction = _parse_and_extract("Material: LOX\n")
    relationship = extraction.relationships[0] if extraction.relationships else None

    if relationship is None:
        from knowledge.extraction.claim import CandidateRelationshipExtraction
        from knowledge.graph.provenance import SourceProvenanceRecord
        from knowledge.graph.contracts import ProvenanceReference

        relationship = CandidateRelationshipExtraction(
            relationship_id="rel-missing",
            document_id=extraction.document_id,
            relationship_type="quantity_DESCRIBES_entity",
            source_extraction_id="missing-source",
            target_extraction_id="missing-target",
            provenance=SourceProvenanceRecord(
                anchor=ProvenanceReference(
                    source_id="SRC-001",
                    document_id=extraction.document_id,
                ),
            ),
        )

    mutated = extraction.__class__(
        document_id=extraction.document_id,
        source_id=extraction.source_id,
        artifact_id=extraction.artifact_id,
        extractor_name=extraction.extractor_name,
        extractor_version=extraction.extractor_version,
        entities=extraction.entities,
        quantities=extraction.quantities,
        equations=extraction.equations,
        claims=extraction.claims,
        relationships=(relationship,),
    )
    findings = validate_schema(ValidationContext(extraction_result=mutated))

    assert any(finding.rule_id == "VAL-SCH-002" for finding in findings)


def test_provenance_validation_preserves_chain() -> None:
    """KG-041 must validate provenance for W4 extraction artifacts."""

    extraction = _parse_and_extract("Material: LOX\n")
    findings = validate_provenance(
        ValidationContext(
            document_id=extraction.document_id,
            source_id=extraction.source_id,
            extraction_result=extraction,
        ),
    )

    assert not any(
        finding.rule_id == "VAL-PRV-001" for finding in findings
    )


def test_provenance_validation_detects_broken_canonicalization_chain() -> None:
    """KG-041 must detect canonicalization mappings without extraction candidates."""

    extraction = _parse_and_extract("Material: LOX\n")
    canonical = canonicalize_extraction_result(extraction, _build_registry())
    broken_mapping = canonical.mappings[0].__class__(
        mapping_id=canonical.mappings[0].mapping_id,
        extraction_id="missing-extraction",
        observed_label=canonical.mappings[0].observed_label,
        normalized_term=canonical.mappings[0].normalized_term,
        canonical_term_id=canonical.mappings[0].canonical_term_id,
        status=canonical.mappings[0].status,
        provenance=canonical.mappings[0].provenance,
    )
    broken = canonical.__class__(
        document_id=canonical.document_id,
        mappings=(broken_mapping,),
    )
    findings = validate_provenance(
        ValidationContext(
            extraction_result=extraction,
            canonicalization_result=broken,
        ),
    )

    assert any(finding.rule_id == "VAL-PRV-003" for finding in findings)


def test_unit_validation_flags_unknown_unit_token() -> None:
    """KG-042 must flag unknown engineering unit tokens."""

    extraction = _parse_and_extract("Operating pressure 5 exoticU.\n")
    findings = validate_units(ValidationContext(extraction_result=extraction))

    assert any(finding.rule_id == "VAL-UNT-001" for finding in findings)


def test_unit_validation_flags_missing_required_unit() -> None:
    """KG-042 must flag numeric quantities missing required units."""

    from knowledge.extraction.w4.models import CandidateQuantityExtraction
    from knowledge.graph.contracts import ProvenanceReference
    from knowledge.graph.provenance import SourceProvenanceRecord

    extraction = _parse_and_extract("Material: LOX\n")
    quantity = CandidateQuantityExtraction(
        extraction_id="qty-missing-unit",
        document_id=extraction.document_id,
        raw_text="20",
        provenance=SourceProvenanceRecord(
            anchor=ProvenanceReference(
                source_id=extraction.source_id,
                document_id=extraction.document_id,
            ),
        ),
        numeric_value=20.0,
        unit_token=None,
        dimensionless=False,
    )
    mutated = extraction.__class__(
        document_id=extraction.document_id,
        source_id=extraction.source_id,
        artifact_id=extraction.artifact_id,
        extractor_name=extraction.extractor_name,
        extractor_version=extraction.extractor_version,
        entities=extraction.entities,
        quantities=(quantity,),
        equations=extraction.equations,
        claims=extraction.claims,
        relationships=extraction.relationships,
    )
    findings = validate_units(ValidationContext(extraction_result=mutated))

    assert any(finding.rule_id == "VAL-UNT-002" for finding in findings)


def test_duplicate_detection_same_label_different_entity() -> None:
    """KG-043 must distinguish same label with different extraction identities."""

    extraction = _parse_and_extract(
        "\n".join(
            [
                "# Section A",
                "Component: Main Injector",
                "# Section B",
                "Component: Main Injector",
            ],
        ),
    )
    findings = detect_duplicates(ValidationContext(extraction_result=extraction))

    assert any(
        finding.duplicate_kind is DuplicateKind.SAME_LABEL_DIFFERENT_ENTITY
        for finding in findings
    )


def test_duplicate_detection_same_value_different_provenance() -> None:
    """KG-043 must detect identical values with distinct provenance."""

    extraction = _parse_and_extract(
        "\n".join(
            [
                "# Chamber A",
                "Pressure is 5 MPa.",
                "# Chamber B",
                "Pressure is 5 MPa.",
            ],
        ),
    )
    findings = detect_duplicates(ValidationContext(extraction_result=extraction))

    assert any(
        finding.duplicate_kind is DuplicateKind.SAME_VALUE_DIFFERENT_PROVENANCE
        for finding in findings
    )


def test_conflict_detection_flags_claim_visibility() -> None:
    """KG-044 must surface claim conflict visibility states."""

    extraction = _parse_and_extract("The chamber pressure is 20 bar.\n")
    claim = extraction.claims[0]
    conflict_claim = claim.__class__(
        claim_id=claim.claim_id,
        document_id=claim.document_id,
        claim_text=claim.claim_text,
        provenance=claim.provenance,
        lifecycle_state=claim.lifecycle_state,
        conflict_visibility=ClaimConflictVisibility.CONFIRMED_CONFLICT,
        confidence_score=claim.confidence_score,
    )
    mutated = extraction.__class__(
        document_id=extraction.document_id,
        source_id=extraction.source_id,
        artifact_id=extraction.artifact_id,
        extractor_name=extraction.extractor_name,
        extractor_version=extraction.extractor_version,
        entities=extraction.entities,
        quantities=extraction.quantities,
        equations=extraction.equations,
        claims=(conflict_claim,),
        relationships=extraction.relationships,
    )
    findings = detect_conflicts(ValidationContext(extraction_result=mutated))

    assert any(
        finding.conflict_classification is ConflictClassification.CONFLICT
        for finding in findings
    )


def test_conflict_detection_flags_incompatible_quantities() -> None:
    """KG-044 must detect incompatible quantity values in the same section."""

    extraction = _parse_and_extract(
        "\n".join(
            [
                "# Chamber",
                "Pressure is 5 MPa.",
                "Pressure is 20 MPa.",
            ],
        ),
    )
    findings = detect_conflicts(ValidationContext(extraction_result=extraction))

    assert any(finding.rule_id == "VAL-CNF-002" for finding in findings)


def test_validation_engine_is_deterministic() -> None:
    """Validation output must be deterministic for identical inputs."""

    extraction = _parse_and_extract("Material: LOX\nThe chamber pressure is 20 bar.\n")
    context = ValidationContext(
        document_id=extraction.document_id,
        source_id=extraction.source_id,
        extraction_result=extraction,
        canonicalization_result=canonicalize_extraction_result(
            extraction,
            _build_registry(),
        ),
    )

    first = ValidationEngine().validate(context)
    second = ValidationEngine().validate(context)

    assert first.to_mapping() == second.to_mapping()


def test_w4_w5_validation_integration_preserves_provenance() -> None:
    """End-to-end validation must preserve provenance across W4 and W5."""

    extraction = _parse_and_extract("Material: LOX\n")
    canonical = canonicalize_extraction_result(extraction, _build_registry())
    report = validate_context(
        ValidationContext(
            document_id=extraction.document_id,
            source_id=extraction.source_id,
            extraction_result=extraction,
            canonicalization_result=canonical,
        ),
    )

    assert report.report_digest
    assert any(
        mapping.status is CanonicalizationStatus.RESOLVED
        for mapping in canonical.mappings
    )
    provenance_findings = [
        finding for finding in report.findings
        if finding.category is ValidationCategory.PROVENANCE
    ]

    assert not any(
        finding.rule_id == "VAL-PRV-001" for finding in provenance_findings
    )


def test_graph_schema_validation_integration() -> None:
    """Validation engine must integrate frozen graph schema validation."""

    record = ImmutableGraphRecord(
        nodes=(
            GraphNode(
                identity=GraphNodeIdentity(node_id="node-001", node_type="Quantity"),
                properties={},
            ),
        ),
        relationships=(),
    )
    findings = validate_schema(ValidationContext(graph_record=record))

    assert any(finding.rule_id == "VAL-SCH-003" for finding in findings)


def test_validation_report_digest_is_stable() -> None:
    """Validation report digest must be stable across repeated runs."""

    extraction = _parse_and_extract("# Title\n")
    context = ValidationContext(extraction_result=extraction)

    first = validate_context(context)
    second = validate_context(context)

    assert first.report_digest == second.report_digest
