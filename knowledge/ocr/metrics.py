"""Separate OCR quality metrics. One score is never used as a substitute."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ("EquationQuality", "TextQuality", "character_error_rate", "word_error_rate")


@dataclass(frozen=True, slots=True, kw_only=True)
class TextQuality:
    expected: str
    actual: str
    character_error_rate: float
    word_error_rate: float


@dataclass(frozen=True, slots=True, kw_only=True)
class EquationQuality:
    expected: str
    actual: str
    equation_detected: bool
    symbol_preserved: bool
    operator_preserved: bool
    label_preserved: bool


def character_error_rate(expected: str, actual: str) -> float:
    if not expected:
        return 0.0 if not actual else 1.0
    distance = _levenshtein(expected, actual)
    return distance / max(len(expected), 1)


def word_error_rate(expected: str, actual: str) -> float:
    expected_words = expected.split()
    actual_words = actual.split()
    if not expected_words:
        return 0.0 if not actual_words else 1.0
    distance = _levenshtein(expected_words, actual_words)
    return distance / max(len(expected_words), 1)


def _levenshtein(left: list[str] | str, right: list[str] | str) -> int:
    previous = list(range(len(right) + 1))
    for i, left_item in enumerate(left, start=1):
        current = [i]
        for j, right_item in enumerate(right, start=1):
            insert = current[j - 1] + 1
            delete = previous[j] + 1
            replace = previous[j - 1] + (0 if left_item == right_item else 1)
            current.append(min(insert, delete, replace))
        previous = current
    return previous[-1]
