"""Machine-readable architecture reconciliation registry."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from knowledge.architecture.dispositions import ArchitectureDisposition, OPEN_DISPOSITIONS

__all__ = (
    "ReconciliationEntry",
    "ReconciliationRegistry",
    "load_reconciliation_registry",
)

_DEFAULT_PATH = Path(__file__).with_name("architecture_manifest.json")


@dataclass(frozen=True, slots=True, kw_only=True)
class ReconciliationEntry:
    frozen_path: str
    disposition: ArchitectureDisposition
    current_path: str
    justification: str
    symbols: str = ""

    @property
    def is_open(self) -> bool:
        return self.disposition in OPEN_DISPOSITIONS


@dataclass(frozen=True, slots=True, kw_only=True)
class ReconciliationRegistry:
    entries: tuple[ReconciliationEntry, ...]

    def counts(self) -> dict[str, int]:
        tallies: dict[str, int] = {item.value: 0 for item in ArchitectureDisposition}
        for entry in self.entries:
            tallies[entry.disposition.value] += 1
        return tallies

    def open_entries(self) -> tuple[ReconciliationEntry, ...]:
        return tuple(entry for entry in self.entries if entry.is_open)

    def is_closed(self) -> bool:
        return not self.open_entries()


def load_reconciliation_registry(path: Path | None = None) -> ReconciliationRegistry:
    payload = json.loads((path or _DEFAULT_PATH).read_text(encoding="utf-8"))
    entries = tuple(
        ReconciliationEntry(
            frozen_path=str(item["frozen_path"]),
            disposition=ArchitectureDisposition(str(item["disposition"])),
            current_path=str(item["current_path"]),
            justification=str(item["justification"]),
            symbols=str(item.get("symbols", "")),
        )
        for item in payload["entries"]
    )
    return ReconciliationRegistry(entries=entries)
