"""Classify engineering queries before retrieval."""

from __future__ import annotations

from enum import Enum
import re

__all__ = ("QueryKind", "classify_query")


class QueryKind(Enum):
    EQUATION = "EQUATION"
    VARIABLE = "VARIABLE"
    CITATION = "CITATION"
    MATERIAL = "MATERIAL"
    KEYWORD = "KEYWORD"
    MIXED = "MIXED"


_EQUATION_NAMES = re.compile(
    r"\b(bartz|dittus|boelter|gnielinski|sieder|colebrook|darcy|weishach|navier|fourier|bernoulli|reynolds)\b",
    re.IGNORECASE,
)
_VARIABLE_SYMBOLS = re.compile(r"\b(Re|Pr|Nu|Cp|Mach|Isp|mdot|mu|rho)\b")
_CITATION = re.compile(r"\b(NASA|SP-\d+|NIST|ISO|AMS|ASTM)\b", re.IGNORECASE)
_MATERIAL = re.compile(
    r"\b(LOX|CH4|GRCop|Inconel|CuCrZr|304L|316L|titanium|copper|methane)\b",
    re.IGNORECASE,
)


def classify_query(text: str) -> QueryKind:
    cleaned = text.strip()
    if not cleaned:
        return QueryKind.KEYWORD
    flags = {
        QueryKind.EQUATION: bool(_EQUATION_NAMES.search(cleaned)),
        QueryKind.VARIABLE: bool(_VARIABLE_SYMBOLS.search(cleaned)),
        QueryKind.CITATION: bool(_CITATION.search(cleaned)),
        QueryKind.MATERIAL: bool(_MATERIAL.search(cleaned)),
    }
    active = [kind for kind, matched in flags.items() if matched]
    if len(active) == 1:
        return active[0]
    if len(active) > 1:
        return QueryKind.MIXED
    return QueryKind.KEYWORD
