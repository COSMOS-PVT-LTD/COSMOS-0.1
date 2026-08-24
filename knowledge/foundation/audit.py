"""Append-only audit log and content hashing for knowledge mutations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json

from knowledge.foundation.governance import KnowledgeAction, KnowledgeActor

__all__ = ("AuditEvent", "AuditLog", "canonical_hash")


def canonical_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True, kw_only=True)
class AuditEvent:
    actor_id: str
    action: str
    entity_id: str
    entity_hash: str
    timestamp: str


class AuditLog:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def record(
        self,
        actor: KnowledgeActor,
        action: KnowledgeAction,
        *,
        entity_id: str,
        payload: dict[str, object],
    ) -> AuditEvent:
        event = AuditEvent(
            actor_id=actor.actor_id,
            action=action.value,
            entity_id=entity_id,
            entity_hash=canonical_hash(payload),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._events.append(event)
        return event

    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)
