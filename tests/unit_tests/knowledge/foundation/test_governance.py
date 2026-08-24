"""Governance is machine-enforced."""

from __future__ import annotations

import pytest

from knowledge.foundation.governance import (
    KnowledgeAction,
    KnowledgeActor,
    KnowledgeGovernance,
    KnowledgeGovernanceError,
    KnowledgeRole,
)
from knowledge.models.lifecycle import KnowledgeLifecycle


def test_ingestor_cannot_approve() -> None:
    actor = KnowledgeActor(actor_id="ingest-1", roles=frozenset({KnowledgeRole.INGESTOR}))
    gov = KnowledgeGovernance()
    with pytest.raises(KnowledgeGovernanceError):
        gov.authorize(actor, KnowledgeAction.APPROVE)


def test_approver_can_mutate_to_approved() -> None:
    actor = KnowledgeActor(actor_id="appr-1", roles=frozenset({KnowledgeRole.APPROVER}))
    KnowledgeGovernance().can_mutate_lifecycle(
        actor,
        KnowledgeLifecycle.REVIEWED,
        KnowledgeLifecycle.APPROVED,
    )
