"""Architecture reconciliation closure tests."""

from __future__ import annotations

from knowledge.architecture import load_reconciliation_registry


def test_architecture_has_no_open_e_f_h_entries() -> None:
    registry = load_reconciliation_registry()
    assert registry.is_closed()
    assert registry.open_entries() == ()
    counts = registry.counts()
    assert counts["E"] == 0
    assert counts["F"] == 0
    assert counts["H"] == 0
    assert sum(counts.values()) == 175
