"""Variable search over the variable index."""

from __future__ import annotations

from knowledge.indexing.variable_index import VariableIndex, VariableIndexEntry

__all__ = ("search_variables",)


def search_variables(index: VariableIndex, symbol: str) -> tuple[VariableIndexEntry, ...]:
    return index.search(symbol)
