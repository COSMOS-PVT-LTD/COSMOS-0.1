"""Equation search over the equation index."""

from __future__ import annotations

from knowledge.indexing.equation_index import EquationIndex, EquationIndexEntry

__all__ = ("search_equations",)


def search_equations(index: EquationIndex, query: str) -> tuple[EquationIndexEntry, ...]:
    return index.search(query)
