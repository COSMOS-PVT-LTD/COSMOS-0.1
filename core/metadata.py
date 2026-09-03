"""
COSMOS Core — traceability metadata for engineering objects.

Provides deterministic, serializable metadata separate from runtime
infrastructure audit records in :mod:`core.settings`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.version import CORE_SCHEMA_VERSION, COSMOS_VERSION

__all__ = (
    "ObjectMetadata",
    "ProvenanceRecord",
)


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    """
    Source reference for a Core object.

    Attributes
    ----------
    source:
        Authoritative source identifier or citation.
    reference:
        Optional document, dataset, or specification reference.
    notes:
        Optional engineering notes.
    """

    source: str
    reference: str | None = None
    notes: str | None = None

    def to_canonical_dict(self) -> dict[str, object]:
        """Return deterministic serialization payload."""

        payload: dict[str, object] = {"source": self.source}
        if self.reference is not None:
            payload["reference"] = self.reference
        if self.notes is not None:
            payload["notes"] = self.notes
        return payload

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> ProvenanceRecord:
        """Reconstruct from canonical dictionary."""

        return cls(
            source=str(data["source"]),
            reference=(
                None
                if data.get("reference") is None
                else str(data["reference"])
            ),
            notes=(
                None if data.get("notes") is None else str(data["notes"])
            ),
        )


@dataclass(frozen=True, slots=True)
class ObjectMetadata:
    """
    Generic metadata attached to Core engineering objects.

    Deterministic identity fields exclude runtime timestamps and random IDs
    from canonical hashes unless explicitly included in ``object_id``.
    """

    object_id: str
    object_type: str
    schema_version: str = CORE_SCHEMA_VERSION
    software_version: str = COSMOS_VERSION
    source: str | None = None
    assumptions: tuple[str, ...] = field(default_factory=tuple)
    validation_status: str | None = None
    verification_status: str | None = None
    provenance: ProvenanceRecord | None = None

    def metadata_dict(self) -> dict[str, object]:
        """Return metadata as a mapping."""

        return self.to_canonical_dict()

    def to_canonical_dict(self) -> dict[str, object]:
        """Return deterministic serialization payload."""

        payload: dict[str, object] = {
            "object_id": self.object_id,
            "object_type": self.object_type,
            "schema_version": self.schema_version,
            "software_version": self.software_version,
            "assumptions": list(self.assumptions),
        }
        if self.source is not None:
            payload["source"] = self.source
        if self.validation_status is not None:
            payload["validation_status"] = self.validation_status
        if self.verification_status is not None:
            payload["verification_status"] = self.verification_status
        if self.provenance is not None:
            payload["provenance"] = self.provenance.to_canonical_dict()
        return payload

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> ObjectMetadata:
        """Reconstruct from canonical dictionary."""

        assumptions_raw = data.get("assumptions", [])
        if assumptions_raw is None:
            assumptions: tuple[str, ...] = ()
        elif isinstance(assumptions_raw, (list, tuple)):
            assumptions = tuple(str(item) for item in assumptions_raw)
        else:
            raise TypeError("assumptions must be a list or tuple.")

        provenance_raw = data.get("provenance")
        provenance = (
            None
            if provenance_raw is None
            else ProvenanceRecord.from_canonical_dict(
                provenance_raw  # type: ignore[arg-type]
            )
        )

        return cls(
            object_id=str(data["object_id"]),
            object_type=str(data["object_type"]),
            schema_version=str(data.get("schema_version", CORE_SCHEMA_VERSION)),
            software_version=str(data.get("software_version", COSMOS_VERSION)),
            source=(
                None if data.get("source") is None else str(data["source"])
            ),
            assumptions=assumptions,
            validation_status=(
                None
                if data.get("validation_status") is None
                else str(data["validation_status"])
            ),
            verification_status=(
                None
                if data.get("verification_status") is None
                else str(data["verification_status"])
            ),
            provenance=provenance,
        )
