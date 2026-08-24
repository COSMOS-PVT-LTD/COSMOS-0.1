"""Reference model tests."""

from __future__ import annotations

from knowledge.models.reference import Reference, ReferenceStatus, ReferenceType


def test_reference_is_traceable() -> None:
    reference = Reference(
        reference_id="REF-NASA-SP-8087",
        title="Liquid Rocket Engine Regenerative Cooling",
        authors=("NASA",),
        reference_type=ReferenceType.NASA_REPORT,
        publication_year=1972,
        status=ReferenceStatus.APPROVED,
    )
    assert reference.reference_id == "REF-NASA-SP-8087"
    assert reference.status is ReferenceStatus.APPROVED
