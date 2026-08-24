"""Deterministic text utilities for extraction and parsing."""

from __future__ import annotations

import re

__all__ = ("normalize_whitespace", "split_sentences")

_WHITESPACE = re.compile(r"\s+")


def normalize_whitespace(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


def split_sentences(text: str) -> tuple[str, ...]:
    parts = re.split(r"(?<=[.!?])\s+", normalize_whitespace(text))
    return tuple(part for part in parts if part)
