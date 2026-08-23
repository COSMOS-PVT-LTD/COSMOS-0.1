"""Deterministic graph topology and integrity diagnostics (Step 6)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from knowledge.graph.repository import GraphStore
from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.graph.validation import GraphRecordValidator

__all__ = (
    "GraphDiagnosticFinding",
    "GraphIntegrityDiagnostics",
    "analyze_graph_integrity",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphDiagnosticFinding:
    """Single graph diagnostic finding."""

    code: str
    message: str
    node_id: str | None = None
    relationship_id: str | None = None

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "code": self.code,
            "message": self.message,
        }
        if self.node_id is not None:
            payload["node_id"] = self.node_id
        if self.relationship_id is not None:
            payload["relationship_id"] = self.relationship_id
        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphIntegrityDiagnostics:
    """Aggregated graph integrity and topology diagnostics."""

    source_digest: str
    orphan_node_ids: tuple[str, ...]
    findings: tuple[GraphDiagnosticFinding, ...]
    report_digest: str

    @property
    def orphan_count(self) -> int:
        return len(self.orphan_node_ids)

    @property
    def has_issues(self) -> bool:
        return bool(self.findings) or bool(self.orphan_node_ids)

    def to_mapping(self) -> dict[str, object]:
        return {
            "findings": [finding.to_mapping() for finding in self.findings],
            "has_issues": self.has_issues,
            "orphan_count": self.orphan_count,
            "orphan_node_ids": list(self.orphan_node_ids),
            "report_digest": self.report_digest,
            "source_digest": self.source_digest,
        }


def _diagnostics_digest(
    source_digest: str,
    orphan_node_ids: tuple[str, ...],
    findings: tuple[GraphDiagnosticFinding, ...],
) -> str:
    payload = {
        "findings": [finding.to_mapping() for finding in findings],
        "orphan_node_ids": list(orphan_node_ids),
        "source_digest": source_digest,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def analyze_graph_integrity(store: GraphStore) -> GraphIntegrityDiagnostics:
    """Analyze graph topology and structural integrity deterministically."""

    record = store.snapshot()
    source_digest = canonical_graph_record_digest(record)
    validator = GraphRecordValidator()
    validation_report = validator.validate(record)

    findings: list[GraphDiagnosticFinding] = [
        GraphDiagnosticFinding(
            code=issue.code,
            message=issue.message,
            node_id=issue.node_id,
            relationship_id=issue.relationship_id,
        )
        for issue in validation_report.issues
    ]

    incident_nodes: dict[str, int] = {node.node_id: 0 for node in record.nodes}
    for relationship in record.relationships:
        incident_nodes[relationship.source_node_id] = (
            incident_nodes.get(relationship.source_node_id, 0) + 1
        )
        incident_nodes[relationship.target_node_id] = (
            incident_nodes.get(relationship.target_node_id, 0) + 1
        )

    orphan_node_ids = tuple(
        sorted(
            node_id
            for node_id, count in incident_nodes.items()
            if count == 0
        ),
    )

    for node_id in orphan_node_ids:
        findings.append(
            GraphDiagnosticFinding(
                code="orphan_node",
                message="Graph node has no incident relationships.",
                node_id=node_id,
            ),
        )

    ordered_findings = tuple(
        sorted(
            findings,
            key=lambda item: (
                item.code,
                item.node_id or "",
                item.relationship_id or "",
            ),
        ),
    )

    digest = _diagnostics_digest(source_digest, orphan_node_ids, ordered_findings)

    return GraphIntegrityDiagnostics(
        source_digest=source_digest,
        orphan_node_ids=orphan_node_ids,
        findings=ordered_findings,
        report_digest=digest,
    )
