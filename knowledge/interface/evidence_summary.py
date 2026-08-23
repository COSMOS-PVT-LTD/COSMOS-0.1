"""Deterministic evidence summaries for Cursor-ready engineering packages (Step 6)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from knowledge.interface.models import ContextPackage

__all__ = (
    "EvidenceSummary",
    "summarize_evidence",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceSummary:
    """Deterministic summary of a packaged controlled-RAG evidence bundle."""

    package_id: str
    request_id: str
    classification: str
    evidence_count: int
    retrieval_methods: tuple[str, ...]
    provider_invoked: bool
    constraint_labels: tuple[str, ...]
    summary_digest: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "classification": self.classification,
            "constraint_labels": list(self.constraint_labels),
            "evidence_count": self.evidence_count,
            "package_id": self.package_id,
            "provider_invoked": self.provider_invoked,
            "request_id": self.request_id,
            "retrieval_methods": list(self.retrieval_methods),
            "summary_digest": self.summary_digest,
        }


def _summary_digest(
    package_id: str,
    request_id: str,
    classification: str,
    evidence_count: int,
    retrieval_methods: tuple[str, ...],
    provider_invoked: bool,
    constraint_labels: tuple[str, ...],
) -> str:
    payload = {
        "classification": classification,
        "constraint_labels": list(constraint_labels),
        "evidence_count": evidence_count,
        "package_id": package_id,
        "provider_invoked": provider_invoked,
        "request_id": request_id,
        "retrieval_methods": list(retrieval_methods),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def summarize_evidence(
    package: ContextPackage,
    *,
    constraint_labels: tuple[str, ...] = (),
) -> EvidenceSummary:
    """Summarize a context package without invoking any external provider."""

    result = package.result
    context = result.context
    evidence_count = len(context.evidence.items)

    digest = _summary_digest(
        package.package_id,
        result.request_id,
        package.classification.value,
        evidence_count,
        result.retrieval_methods,
        result.provider_invoked,
        constraint_labels,
    )

    return EvidenceSummary(
        package_id=package.package_id,
        request_id=result.request_id,
        classification=package.classification.value,
        evidence_count=evidence_count,
        retrieval_methods=result.retrieval_methods,
        provider_invoked=result.provider_invoked,
        constraint_labels=constraint_labels,
        summary_digest=digest,
    )
