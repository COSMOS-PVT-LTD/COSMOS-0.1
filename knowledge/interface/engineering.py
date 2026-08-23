"""Knowledge-to-engineering interface for KG-051."""

from __future__ import annotations

from knowledge.interface.exceptions import InterfaceValidationError
from knowledge.interface.identity import deterministic_engineering_payload_id
from knowledge.interface.identity import deterministic_package_digest
from knowledge.interface.models import (
    CursorDevelopmentContext,
    EngineeringKnowledgePayload,
)

__all__ = (
    "EngineeringKnowledgeInterface",
)


class EngineeringKnowledgeInterface:
    """Controlled boundary between knowledge system and engineering software."""

    def build_payload(
        self,
        cursor_context: CursorDevelopmentContext,
    ) -> EngineeringKnowledgePayload:
        """Build a deterministic engineering knowledge payload."""

        if not isinstance(cursor_context, CursorDevelopmentContext):
            raise InterfaceValidationError(
                "cursor_context must be a CursorDevelopmentContext instance.",
            )

        outcome = cursor_context.package.result.context.outcome
        lifecycle_preserved = all(
            link.lifecycle_state is not None or link.document_id is not None
            for link in (
                link
                for chain in outcome.chains
                for link in chain.links
            )
        ) or not outcome.chains

        provenance_preserved = all(
            bool(link.provenance)
            for link in (
                link
                for chain in outcome.chains
                for link in chain.links
            )
        ) or not outcome.chains

        payload_digest = deterministic_package_digest(
            cursor_context.context_digest,
            outcome.classification.value,
            str(lifecycle_preserved),
            str(provenance_preserved),
        )
        payload_id = deterministic_engineering_payload_id(
            cursor_context.context_id,
            outcome.classification.value,
        )

        return EngineeringKnowledgePayload(
            payload_id=payload_id,
            cursor_context=cursor_context,
            outcome=outcome,
            lifecycle_preserved=lifecycle_preserved,
            provenance_preserved=provenance_preserved,
            payload_digest=payload_digest,
        )
