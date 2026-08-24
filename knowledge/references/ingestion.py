"""Reference ingest gate. Restricted/unknown rights never proceed as cleared."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.references.document_class import DocumentClass
from knowledge.references.rights import RightsRecord, RightsStatus, rights_allow_ingestion

__all__ = ("ReferenceIngestRequest", "validate_reference_ingest")


@dataclass(frozen=True, slots=True, kw_only=True)
class ReferenceIngestRequest:
    source_id: str
    document_id: str
    title: str
    filename: str
    rights: RightsRecord
    document_class: DocumentClass
    author: str | None = None
    organization: str | None = None
    edition: str | None = None
    publication_year: int | None = None
    publisher: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ReferenceIngestDecision:
    accepted: bool
    reason: str
    rights_status: RightsStatus


def validate_reference_ingest(request: ReferenceIngestRequest) -> ReferenceIngestDecision:
    if request.rights.status is RightsStatus.UNKNOWN:
        return ReferenceIngestDecision(
            accepted=False,
            reason="UNKNOWN rights must not be treated as cleared.",
            rights_status=request.rights.status,
        )
    if request.rights.status is RightsStatus.RESTRICTED:
        return ReferenceIngestDecision(
            accepted=False,
            reason="RESTRICTED sources are not ingestible.",
            rights_status=request.rights.status,
        )
    if not rights_allow_ingestion(request.rights.status):
        return ReferenceIngestDecision(
            accepted=False,
            reason=f"Rights status {request.rights.status.value} is not ingestible.",
            rights_status=request.rights.status,
        )
    if not request.source_id.strip() or not request.document_id.strip():
        return ReferenceIngestDecision(
            accepted=False,
            reason="source_id and document_id are required.",
            rights_status=request.rights.status,
        )
    return ReferenceIngestDecision(
        accepted=True,
        reason="ok",
        rights_status=request.rights.status,
    )
