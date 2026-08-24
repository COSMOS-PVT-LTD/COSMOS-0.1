"""Property-value candidate extractor."""

from __future__ import annotations

import re

from knowledge.extraction.candidate import candidate_provenance
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.models.property import PropertyValue

__all__ = ("extract_property_values",)

_PROPERTY = re.compile(
    r"\b(?P<name>density|viscosity|thermal conductivity|specific heat)\b",
    re.IGNORECASE,
)


def extract_property_values(
    text: str,
    *,
    document_id: str,
    reference_id: str,
) -> tuple[PropertyValue, ...]:
    items: list[PropertyValue] = []
    for index, match in enumerate(re.finditer(_PROPERTY, text)):
        items.append(
            PropertyValue(
                value_id=f"PROPVAL-CAND-{index:03d}",
                property_id=match.group("name").lower().replace(" ", "_"),
                material_id=None,
                numeric_value=0.0,
                unit="UNSPECIFIED",
                provenance=candidate_provenance(document_id, reference_id),
                lifecycle=KnowledgeLifecycle.CANDIDATE,
            ),
        )
    return tuple(items)
