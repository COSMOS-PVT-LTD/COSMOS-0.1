"""Greek/symbol hypotheses never rewrite source text."""

from __future__ import annotations

from knowledge.ocr.symbols import ENGINEERING_GREEK, GREEK_ALPHABET, propose_symbol_resolutions


def test_symbol_hypotheses_do_not_mutate_source() -> None:
    source = "Re = rho * V * D / mu"
    hypotheses = propose_symbol_resolutions(source)
    assert source == "Re = rho * V * D / mu"
    assert hypotheses
    assert all(item.requires_review for item in hypotheses)
    notes = " ".join(item.note for item in hypotheses)
    assert "rho" in notes or "mu" in notes


def test_greek_catalog_is_explicit() -> None:
    for symbol in ("α", "β", "γ", "δ", "ε", "θ", "λ", "μ", "ν", "ρ", "σ", "τ", "φ", "ψ", "ω", "Δ", "Σ", "Ω"):
        assert symbol in GREEK_ALPHABET
    for symbol in ("ρ", "μ", "ν", "σ", "τ", "γ", "θ", "ω"):
        assert symbol in ENGINEERING_GREEK
