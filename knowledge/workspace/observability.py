"""Local workspace metrics. Not a production monitoring stack."""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ("WorkspaceMetrics",)


@dataclass
class WorkspaceMetrics:
    ingest_accepted: int = 0
    ingest_blocked: int = 0
    ingest_failed: int = 0
    ingest_duplicates: int = 0
    chat_turns: int = 0
    reviews: int = 0
    backups: int = 0
    restores: int = 0
    reprocesses: int = 0
    index_rebuilds: int = 0
    notes: list[str] = field(default_factory=list)

    def snapshot(self) -> dict[str, object]:
        return {
            "ingest_accepted": self.ingest_accepted,
            "ingest_blocked": self.ingest_blocked,
            "ingest_failed": self.ingest_failed,
            "ingest_duplicates": self.ingest_duplicates,
            "chat_turns": self.chat_turns,
            "reviews": self.reviews,
            "backups": self.backups,
            "restores": self.restores,
            "reprocesses": self.reprocesses,
            "index_rebuilds": self.index_rebuilds,
            "notes": list(self.notes),
        }
