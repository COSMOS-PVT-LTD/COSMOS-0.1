"""Knowledge repository lifecycle tests."""

from __future__ import annotations

import pytest

from knowledge.models.correlation import Correlation
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace
from knowledge.repositories.correlation_repository import CorrelationRepository
from knowledge.repository.knowledge_repository import DestructiveDeleteError


def _corr(lifecycle: KnowledgeLifecycle) -> Correlation:
    return Correlation(
        correlation_id="CORR-BARTZ",
        name="Bartz",
        equation="h = f(Re, Pr)",
        variables=("h", "Re", "Pr"),
        dimensionless_groups=("Re", "Pr"),
        provenance=ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1"),
        lifecycle=lifecycle,
    )


def test_repository_rejects_destructive_delete_of_approved() -> None:
    repo = CorrelationRepository()
    repo.create(_corr(KnowledgeLifecycle.APPROVED))
    with pytest.raises(DestructiveDeleteError):
        repo.delete("CORR-BARTZ")


def test_candidate_may_be_removed() -> None:
    repo = CorrelationRepository()
    repo.create(_corr(KnowledgeLifecycle.CANDIDATE))
    repo.delete("CORR-BARTZ")
    assert repo.query() == ()
