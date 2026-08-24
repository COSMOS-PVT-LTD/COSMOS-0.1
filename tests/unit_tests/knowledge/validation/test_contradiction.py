"""Contradiction detection tests."""

from __future__ import annotations

from knowledge.validation.contradiction import detect_numeric_conflicts


def test_conflicting_temperature_limits_are_reported() -> None:
    conflicts = detect_numeric_conflicts(
        (
            ("ENT-A", "CuCrZr", "max_temperature_K", 800.0, "NASA-A"),
            ("ENT-B", "CuCrZr", "max_temperature_K", 900.0, "PAPER-B"),
        ),
    )
    assert len(conflicts) == 1
    assert "review" in conflicts[0].reason.lower()
    assert conflicts[0].review_status == "REVIEW_REQUIRED"
