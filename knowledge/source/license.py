"""
COSMOS Knowledge Foundation

Module:
    knowledge.source.license

Purpose:
    Structured license and IP metadata models (NEW KG-007).
"""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.source.exceptions import LicenseMetadataError

__all__ = (
    "LicenseMetadata",
)


def _optional_string(field_name: str, value: str | None) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise LicenseMetadataError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise LicenseMetadataError(f"{field_name} must not be blank.")

    return cleaned


@dataclass(frozen=True, slots=True, kw_only=True)
class LicenseMetadata:
    """
    Declared license and IP metadata for a knowledge source.

    Preserves declared metadata only. Does not infer legal permissions.
    """

    license_identifier: str | None = None
    license_text_reference: str | None = None
    rights_holder: str | None = None
    usage_restrictions: str | None = None
    attribution_requirements: str | None = None
    access_classification: str | None = None
    confidentiality_classification: str | None = None
    source_policy: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "license_identifier",
            _optional_string("license_identifier", self.license_identifier),
        )
        object.__setattr__(
            self,
            "license_text_reference",
            _optional_string(
                "license_text_reference",
                self.license_text_reference,
            ),
        )
        object.__setattr__(
            self,
            "rights_holder",
            _optional_string("rights_holder", self.rights_holder),
        )
        object.__setattr__(
            self,
            "usage_restrictions",
            _optional_string("usage_restrictions", self.usage_restrictions),
        )
        object.__setattr__(
            self,
            "attribution_requirements",
            _optional_string(
                "attribution_requirements",
                self.attribution_requirements,
            ),
        )
        object.__setattr__(
            self,
            "access_classification",
            _optional_string(
                "access_classification",
                self.access_classification,
            ),
        )
        object.__setattr__(
            self,
            "confidentiality_classification",
            _optional_string(
                "confidentiality_classification",
                self.confidentiality_classification,
            ),
        )
        object.__setattr__(
            self,
            "source_policy",
            _optional_string("source_policy", self.source_policy),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {}

        for key in (
            "license_identifier",
            "license_text_reference",
            "rights_holder",
            "usage_restrictions",
            "attribution_requirements",
            "access_classification",
            "confidentiality_classification",
            "source_policy",
        ):
            value = getattr(self, key)

            if value is not None:
                payload[key] = value

        return payload
