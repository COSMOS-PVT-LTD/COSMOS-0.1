"""Recovery procedures for production local knowledge store (Step 7)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.graph.memory_store import InMemoryGraphStore
from knowledge.indexing.w7.bundle import W7IndexBundle
from knowledge.storage.exceptions import CorruptionError
from knowledge.storage.index_lifecycle import IndexLifecycleManager
from knowledge.storage.local_store import LocalKnowledgeStore

__all__ = (
    "RecoveryAction",
    "RecoveryPlan",
    "RecoveryProcedure",
)


class RecoveryAction(Enum):
    """Recovery actions for production store failures."""

    RELOAD_GRAPH = "RELOAD_GRAPH"
    REBUILD_INDEXES = "REBUILD_INDEXES"
    REINITIALIZE_STORE = "REINITIALIZE_STORE"
    NO_ACTION = "NO_ACTION"


@dataclass(frozen=True, slots=True, kw_only=True)
class RecoveryPlan:
    """Structured recovery plan."""

    actions: tuple[RecoveryAction, ...]
    message: str


class RecoveryProcedure:
    """Detect failures and execute deterministic recovery steps."""

    def __init__(
        self,
        *,
        store: LocalKnowledgeStore,
        index_manager: IndexLifecycleManager,
    ) -> None:
        self._store = store
        self._index_manager = index_manager

    def diagnose(self) -> RecoveryPlan:
        """Diagnose store/index health and recommend recovery actions."""

        if not self._store.verify_integrity():
            return RecoveryPlan(
                actions=(RecoveryAction.REINITIALIZE_STORE,),
                message="Store integrity verification failed.",
            )

        try:
            self._index_manager.validate(self._store.graph_store)
        except Exception as exc:
            return RecoveryPlan(
                actions=(RecoveryAction.REBUILD_INDEXES,),
                message=str(exc),
            )

        return RecoveryPlan(
            actions=(RecoveryAction.NO_ACTION,),
            message="Store and indexes are healthy.",
        )

    def recover(self) -> W7IndexBundle:
        """Execute recovery and return a valid index bundle."""

        plan = self.diagnose()

        if RecoveryAction.REINITIALIZE_STORE in plan.actions:
            self._store.initialize()
            empty_store = InMemoryGraphStore()
            return self._index_manager.rebuild(empty_store)

        if RecoveryAction.REBUILD_INDEXES in plan.actions:
            return self._index_manager.rebuild(self._store.graph_store)

        return self._index_manager.load(self._store.graph_store)

    def recover_from_corruption(self) -> RecoveryPlan:
        """Fail closed and produce explicit recovery guidance."""

        if self._store.verify_integrity():
            return RecoveryPlan(
                actions=(RecoveryAction.NO_ACTION,),
                message="No corruption detected.",
            )

        raise CorruptionError(
            "Persistent store corruption detected. "
            "Execute REBUILD_INDEXES or REINITIALIZE_STORE after human review.",
        )
