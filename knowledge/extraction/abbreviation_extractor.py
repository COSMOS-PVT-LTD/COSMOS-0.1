"""Abbreviation candidate extractor."""

from __future__ import annotations

import re

__all__ = ("extract_abbreviations",)

_ABBREV = re.compile(r"\b([A-Z]{2,6})\b")


def extract_abbreviations(text: str) -> tuple[str, ...]:
    return tuple(sorted(set(_ABBREV.findall(text))))
