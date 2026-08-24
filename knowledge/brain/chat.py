"""Persistent knowledge conversations. Chat never auto-promotes to canonical knowledge."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import json
import re

from knowledge.brain.hybrid import hybrid_search
from knowledge.brain.planner import PlannedQueryKind, QueryPlan, QueryPlanner
from knowledge.foundation.reasoning_answer import EngineeringAnswer, assemble_engineering_answer
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.workspace.session import KnowledgeWorkspace

__all__ = (
    "ChatMessage",
    "ChatTurn",
    "ConversationRecord",
    "ConversationStore",
    "KnowledgeConversationService",
)

_CALC = re.compile(r"\b(calculate|run the calculation|compute|solve)\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatMessage:
    role: str
    content: str
    timestamp: str
    evidence_ids: tuple[str, ...] = ()
    validation_state: str = "CONVERSATION"


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatTurn:
    conversation_id: str
    message: ChatMessage
    answer: EngineeringAnswer
    plan: QueryPlan
    document_ids: tuple[str, ...]
    routed_to_solver: bool


@dataclass
class ConversationRecord:
    conversation_id: str
    user: str
    project_id: str
    created_at: str
    messages: list[ChatMessage] = field(default_factory=list)
    active_sources: list[str] = field(default_factory=list)

    def to_mapping(self) -> dict[str, object]:
        return {
            "conversation_id": self.conversation_id,
            "user": self.user,
            "project_id": self.project_id,
            "created_at": self.created_at,
            "messages": [
                {
                    "role": item.role,
                    "content": item.content,
                    "timestamp": item.timestamp,
                    "evidence_ids": list(item.evidence_ids),
                    "validation_state": item.validation_state,
                }
                for item in self.messages
            ],
            "active_sources": list(self.active_sources),
        }

    @classmethod
    def from_mapping(cls, payload: dict[str, object]) -> ConversationRecord:
        raw_messages = payload.get("messages")
        messages: list[ChatMessage] = []
        if isinstance(raw_messages, list):
            for item in raw_messages:
                if not isinstance(item, dict):
                    continue
                evidence = item.get("evidence_ids")
                messages.append(
                    ChatMessage(
                        role=str(item.get("role") or "user"),
                        content=str(item.get("content") or ""),
                        timestamp=str(item.get("timestamp") or ""),
                        evidence_ids=tuple(str(value) for value in evidence) if isinstance(evidence, list) else (),
                        validation_state=str(item.get("validation_state") or "CONVERSATION"),
                    ),
                )
        sources = payload.get("active_sources")
        return cls(
            conversation_id=str(payload["conversation_id"]),
            user=str(payload.get("user") or "engineer"),
            project_id=str(payload.get("project_id") or "GLOBAL"),
            created_at=str(payload.get("created_at") or ""),
            messages=messages,
            active_sources=[str(item) for item in sources] if isinstance(sources, list) else [],
        )


class ConversationStore:
    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root is not None else None
        self._items: dict[str, ConversationRecord] = {}
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)
            self._load()

    def save(self, record: ConversationRecord) -> ConversationRecord:
        self._items[record.conversation_id] = record
        if self.root is not None:
            path = self.root / f"{record.conversation_id}.json"
            path.write_text(json.dumps(record.to_mapping(), indent=2, sort_keys=True), encoding="utf-8")
        return record

    def get(self, conversation_id: str) -> ConversationRecord:
        return self._items[conversation_id]

    def list(self) -> tuple[ConversationRecord, ...]:
        return tuple(self._items.values())

    def _load(self) -> None:
        if self.root is None:
            return
        for path in sorted(self.root.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            record = ConversationRecord.from_mapping(payload)
            self._items[record.conversation_id] = record


class KnowledgeConversationService:
    def __init__(self, workspace: KnowledgeWorkspace) -> None:
        self.workspace = workspace
        self.planner = QueryPlanner()
        root = workspace.root / "conversations" if workspace.root is not None else None
        self.store = ConversationStore(root)

    def create(self, *, user: str = "engineer", project_id: str | None = None) -> ConversationRecord:
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        record = ConversationRecord(
            conversation_id=f"CONV-{uuid4().hex[:16]}",
            user=user,
            project_id=project_id or self.workspace.project_id,
            created_at=stamp,
        )
        return self.store.save(record)

    def ask(self, conversation_id: str, message: str) -> ChatTurn:
        record = self.store.get(conversation_id)
        plan = self.planner.plan(message)
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        user_message = ChatMessage(role="user", content=message, timestamp=stamp)
        record.messages.append(user_message)

        retrieved = hybrid_search(self.workspace, message, project_id=record.project_id)
        document_ids = [hit.source_id for hit in retrieved.documents]
        if plan.kind is PlannedQueryKind.COMPARISON_QUERY:
            document_ids = list(dict.fromkeys([*record.active_sources, *document_ids]))
        record.active_sources = list(dict.fromkeys([*record.active_sources, *document_ids]))

        routed = bool(plan.route_to_solver or _CALC.search(message))
        self.workspace._ensure_seed_corpus()
        foundation_answer = self.workspace.service.answer(message)
        conclusion = foundation_answer.conclusion
        evidence = list(foundation_answer.evidence)
        limitations = foundation_answer.limitations
        if retrieved.documents:
            snippets = "; ".join(f"{hit.source_id}: {hit.snippet}" for hit in retrieved.documents[:3])
            conclusion = f"{conclusion} Candidate document evidence: {snippets}"
            evidence.extend(hit.snippet for hit in retrieved.documents[:3])
        if routed:
            conclusion = (
                "Calculation requests are routed to the deterministic COSMOS physics/engineering "
                "gateway. Chat does not compute or invent numeric results."
            )
            limitations = (
                "No solver was executed. Approved knowledge may be retrieved through "
                "PhysicsKnowledgeGateway when a caller is authorized."
            )
        if not retrieved.foundation.hits and not retrieved.documents:
            conclusion = "No approved knowledge or ingested source evidence matched the query."
        answer = assemble_engineering_answer(
            conclusion=conclusion,
            equation_ids=foundation_answer.supporting_equation_ids,
            document_ids=tuple(document_ids) or foundation_answer.supporting_document_ids,
            supporting_entities=foundation_answer.supporting_entities,
            source_references=foundation_answer.source_references,
            assumptions=foundation_answer.assumptions,
            validity_range=foundation_answer.validity_range,
            domain=plan.kind.value,
            evidence=tuple(evidence),
            contradictions=foundation_answer.contradictions,
            approved=all(hit.lifecycle is KnowledgeLifecycle.APPROVED for hit in retrieved.foundation.hits)
            and bool(retrieved.foundation.hits)
            and not retrieved.documents,
            limitations=limitations,
        )
        assistant = ChatMessage(
            role="assistant",
            content=answer.conclusion,
            timestamp=stamp,
            evidence_ids=tuple(document_ids) + answer.supporting_entities,
            validation_state=answer.validation_state,
        )
        record.messages.append(assistant)
        self.store.save(record)
        self.workspace.metrics.chat_turns += 1
        return ChatTurn(
            conversation_id=conversation_id,
            message=assistant,
            answer=answer,
            plan=plan,
            document_ids=tuple(document_ids),
            routed_to_solver=routed,
        )
