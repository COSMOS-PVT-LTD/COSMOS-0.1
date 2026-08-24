"""Variable index — find entities involving Re, Pr, Nu, μ, etc."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ("VariableIndex", "VariableIndexEntry")


@dataclass(frozen=True, slots=True, kw_only=True)
class VariableIndexEntry:
    variable_id: str
    symbol: str
    name: str
    equation_ids: tuple[str, ...]


class VariableIndex:
    def __init__(self) -> None:
        self._entries: dict[str, VariableIndexEntry] = {}

    def add(self, entry: VariableIndexEntry) -> None:
        self._entries[entry.variable_id] = entry

    def search(self, symbol: str) -> tuple[VariableIndexEntry, ...]:
        needle = symbol.strip().lower()
        return tuple(
            entry
            for entry_id, entry in sorted(self._entries.items())
            if needle == entry.symbol.lower() or needle in entry.name.lower()
        )
