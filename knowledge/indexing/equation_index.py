"""Equation index — search by expression, variable, domain, and source."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.equation import Equation

__all__ = ("EquationIndex", "EquationIndexEntry")


@dataclass(frozen=True, slots=True, kw_only=True)
class EquationIndexEntry:
    equation_id: str
    name: str
    expression: str
    variables: tuple[str, ...]
    domain: str
    source_document_id: str
    status: str


class EquationIndex:
    def __init__(self) -> None:
        self._entries: dict[str, EquationIndexEntry] = {}

    def add(self, equation: Equation, *, variables: tuple[str, ...] = ()) -> None:
        self._entries[equation.equation_id] = EquationIndexEntry(
            equation_id=equation.equation_id,
            name=equation.equation_name,
            expression=equation.expression,
            variables=variables,
            domain=equation.equation_category.value,
            source_document_id=equation.source_document.document_id,
            status=equation.status.value,
        )

    def search(self, query: str) -> tuple[EquationIndexEntry, ...]:
        needle = query.strip().lower()
        if not needle:
            return ()
        hits = [
            entry
            for entry in self._entries.values()
            if needle in entry.name.lower()
            or needle in entry.expression.lower()
            or needle in entry.domain.lower()
            or any(needle == variable.lower() for variable in entry.variables)
        ]
        return tuple(sorted(hits, key=lambda item: item.equation_id))
