"""Correlation model tests."""

from __future__ import annotations

from knowledge.models.correlation import Correlation
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace, UncertaintyRecord


def test_correlation_carries_uncertainty_and_ranges() -> None:
    item = Correlation(
        correlation_id="CORR-DB",
        name="Dittus-Boelter",
        equation="Nu = 0.023 * Re**0.8 * Pr**n",
        variables=("Nu", "Re", "Pr"),
        dimensionless_groups=("Nu", "Re", "Pr"),
        reynolds_range=(1.0e4, 1.2e5),
        uncertainty=UncertaintyRecord(kind="correlation", magnitude=0.25, unit="fraction"),
        provenance=ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1"),
        lifecycle=KnowledgeLifecycle.APPROVED,
    )
    assert item.uncertainty is not None
    assert item.reynolds_range == (1.0e4, 1.2e5)
