"""
COSMOS Knowledge Foundation

Module:
    knowledge.graph.provenance

Purpose:
    Source provenance contracts extending KG-001 provenance anchors.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.graph.contracts import ProvenanceReference
from knowledge.graph.exceptions import GraphValidationError

__all__ = (
    "ExtractionProvenance",
    "ReviewStatus",
    "SourceLineage",
    "SourceProvenanceRecord",
)


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise GraphValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise GraphValidationError(f"{field_name} must not be blank.")

    return cleaned


def _validate_optional_non_empty_string(
    field_name: str,
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return _validate_non_empty_string(field_name, value)


class ReviewStatus(Enum):
    """Review state for extracted or asserted knowledge."""

    UNREVIEWED = "UNREVIEWED"
    CANDIDATE = "CANDIDATE"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractionProvenance:
    """
    Provenance metadata for an extraction tool and ontology context.

    Does not embed extracted content.
    """

    extractor_tool: str
    extractor_version: str
    ontology_version: str | None = None
    review_status: ReviewStatus = ReviewStatus.UNREVIEWED

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "extractor_tool",
            _validate_non_empty_string(
                "extractor_tool",
                self.extractor_tool,
            ),
        )
        object.__setattr__(
            self,
            "extractor_version",
            _validate_non_empty_string(
                "extractor_version",
                self.extractor_version,
            ),
        )
        object.__setattr__(
            self,
            "ontology_version",
            _validate_optional_non_empty_string(
                "ontology_version",
                self.ontology_version,
            ),
        )

        if not isinstance(self.review_status, ReviewStatus):
            raise GraphValidationError(
                "review_status must be a ReviewStatus value."
            )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {
            "extractor_tool": self.extractor_tool,
            "extractor_version": self.extractor_version,
            "review_status": self.review_status.value,
        }

        if self.ontology_version is not None:
            payload["ontology_version"] = self.ontology_version

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceLineage:
    """
    Lineage metadata linking a provenance record to upstream sources.

    At least one lineage field must be populated when a lineage object is
    constructed.
    """

    parent_source_id: str | None = None
    parent_artifact_id: str | None = None
    derivation_note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "parent_source_id",
            _validate_optional_non_empty_string(
                "parent_source_id",
                self.parent_source_id,
            ),
        )
        object.__setattr__(
            self,
            "parent_artifact_id",
            _validate_optional_non_empty_string(
                "parent_artifact_id",
                self.parent_artifact_id,
            ),
        )
        object.__setattr__(
            self,
            "derivation_note",
            _validate_optional_non_empty_string(
                "derivation_note",
                self.derivation_note,
            ),
        )

        if not any(
            value is not None
            for value in (
                self.parent_source_id,
                self.parent_artifact_id,
                self.derivation_note,
            )
        ):
            raise GraphValidationError(
                "SourceLineage requires at least one lineage field."
            )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {}

        if self.parent_source_id is not None:
            payload["parent_source_id"] = self.parent_source_id
        if self.parent_artifact_id is not None:
            payload["parent_artifact_id"] = self.parent_artifact_id
        if self.derivation_note is not None:
            payload["derivation_note"] = self.derivation_note

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceProvenanceRecord:
    """
    Composite provenance record for graph assertions.

    Wraps a KG-001 ``ProvenanceReference`` anchor with optional extraction and
    lineage metadata. Does not embed source text.
    """

    anchor: ProvenanceReference
    extraction: ExtractionProvenance | None = None
    lineage: SourceLineage | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.anchor, ProvenanceReference):
            raise GraphValidationError(
                "anchor must be a ProvenanceReference instance."
            )

        if self.extraction is not None and not isinstance(
            self.extraction,
            ExtractionProvenance,
        ):
            raise GraphValidationError(
                "extraction must be an ExtractionProvenance instance."
            )

        if self.lineage is not None and not isinstance(
            self.lineage,
            SourceLineage,
        ):
            raise GraphValidationError(
                "lineage must be a SourceLineage instance."
            )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {
            "anchor": self.anchor.to_mapping(),
        }

        if self.extraction is not None:
            payload["extraction"] = self.extraction.to_mapping()
        if self.lineage is not None:
            payload["lineage"] = self.lineage.to_mapping()

        return payload
