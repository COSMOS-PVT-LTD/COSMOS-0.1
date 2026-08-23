"""Schema validation for KG-040."""

from __future__ import annotations

from knowledge.extraction.w4.models import ExtractionResult
from knowledge.graph.contracts import ImmutableGraphRecord
from knowledge.graph.lifecycle import GraphLifecycleState
from knowledge.graph.validation import GraphRecordValidator
from knowledge.ontology.models import CanonicalizationMapping, CanonicalizationResult
from knowledge.validation.models import (
    ValidationCategory,
    ValidationContext,
    ValidationFinding,
    ValidationSeverity,
    ValidationStatus,
)
from knowledge.validation.rules import make_finding

__all__ = (
    "validate_schema",
)

_RULE_PREMATURE_APPROVAL = "VAL-SCH-001"
_RULE_MISSING_RELATIONSHIP_ENDPOINT = "VAL-SCH-002"
_RULE_GRAPH_SCHEMA = "VAL-SCH-003"
_RULE_UNRESOLVED_CANONICAL_MAPPING = "VAL-SCH-004"


def validate_schema(context: ValidationContext) -> tuple[ValidationFinding, ...]:
    """Validate structural/schema integrity across supported knowledge objects."""

    findings: list[ValidationFinding] = []

    if context.extraction_result is not None:
        findings.extend(_validate_extraction_result(context.extraction_result))

    if context.canonicalization_result is not None:
        findings.extend(
            _validate_canonicalization_result(context.canonicalization_result),
        )

    if context.graph_record is not None:
        findings.extend(_validate_graph_record(context.graph_record))

    return tuple(sorted(findings, key=lambda item: item.finding_id))


def _validate_extraction_result(
    extraction_result: ExtractionResult,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []

    entity_ids = {entity.extraction_id for entity in extraction_result.entities}
    equation_ids = {equation.extraction_id for equation in extraction_result.equations}
    claim_ids = {claim.claim_id for claim in extraction_result.claims}
    quantity_ids = {
        quantity.extraction_id for quantity in extraction_result.quantities
    }
    known_ids = entity_ids | equation_ids | claim_ids | quantity_ids

    for entity in extraction_result.entities:
        if entity.lifecycle_state is GraphLifecycleState.APPROVED:
            findings.append(
                make_finding(
                    rule_id=_RULE_PREMATURE_APPROVAL,
                    object_id=entity.extraction_id,
                    severity=ValidationSeverity.CRITICAL,
                    category=ValidationCategory.SCHEMA,
                    status=ValidationStatus.INVALID,
                    message="Extraction candidate must not be in APPROVED state.",
                    provenance=entity.provenance,
                ),
            )

    for claim in extraction_result.claims:
        if claim.lifecycle_state is GraphLifecycleState.APPROVED:
            findings.append(
                make_finding(
                    rule_id=_RULE_PREMATURE_APPROVAL,
                    object_id=claim.claim_id,
                    severity=ValidationSeverity.CRITICAL,
                    category=ValidationCategory.SCHEMA,
                    status=ValidationStatus.INVALID,
                    message="Claim candidate must not be in APPROVED state.",
                    provenance=claim.provenance,
                ),
            )

    for relationship in extraction_result.relationships:
        if relationship.source_extraction_id not in known_ids:
            findings.append(
                make_finding(
                    rule_id=_RULE_MISSING_RELATIONSHIP_ENDPOINT,
                    object_id=relationship.relationship_id,
                    severity=ValidationSeverity.HIGH,
                    category=ValidationCategory.SCHEMA,
                    status=ValidationStatus.INVALID,
                    message="Relationship source endpoint is not present in batch.",
                    provenance=relationship.provenance,
                    related_object_ids=(relationship.source_extraction_id,),
                ),
            )

        if relationship.target_extraction_id not in known_ids:
            findings.append(
                make_finding(
                    rule_id=_RULE_MISSING_RELATIONSHIP_ENDPOINT,
                    object_id=relationship.relationship_id,
                    severity=ValidationSeverity.HIGH,
                    category=ValidationCategory.SCHEMA,
                    status=ValidationStatus.INVALID,
                    message="Relationship target endpoint is not present in batch.",
                    provenance=relationship.provenance,
                    related_object_ids=(relationship.target_extraction_id,),
                ),
            )

    return findings


def _validate_canonicalization_result(
    canonicalization_result: CanonicalizationResult,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []

    for mapping in canonicalization_result.mappings:
        if not isinstance(mapping, CanonicalizationMapping):
            continue

        if mapping.canonical_term_id is None:
            findings.append(
                make_finding(
                    rule_id=_RULE_UNRESOLVED_CANONICAL_MAPPING,
                    object_id=mapping.mapping_id,
                    severity=ValidationSeverity.LOW,
                    category=ValidationCategory.SCHEMA,
                    status=ValidationStatus.WARNING,
                    message="Canonicalization mapping remains unresolved.",
                    provenance=mapping.provenance,
                    related_object_ids=(mapping.extraction_id,),
                ),
            )

    return findings


def _validate_graph_record(graph_record: object) -> list[ValidationFinding]:
    if not isinstance(graph_record, ImmutableGraphRecord):
        return []

    findings: list[ValidationFinding] = []
    report = GraphRecordValidator().validate(graph_record)

    for issue in report.issues:
        object_id = issue.node_id or issue.relationship_id or "graph-record"
        findings.append(
            make_finding(
                rule_id=_RULE_GRAPH_SCHEMA,
                object_id=object_id,
                severity=ValidationSeverity.HIGH,
                category=ValidationCategory.SCHEMA,
                status=ValidationStatus.INVALID,
                message=issue.message,
                stable_parts=(issue.code,),
            ),
        )

    return findings
