"""Symbol hypotheses. Never performs uncontrolled global substitution."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.ocr.ambiguity import OCR_CONFUSION_PAIRS, ocr_ambiguity_warnings

__all__ = (
    "ENGINEERING_GREEK",
    "GREEK_ALPHABET",
    "SymbolHypothesis",
    "propose_symbol_resolutions",
)

GREEK_ALPHABET: tuple[str, ...] = (
    "α",
    "β",
    "γ",
    "δ",
    "ε",
    "θ",
    "λ",
    "μ",
    "ν",
    "ρ",
    "σ",
    "τ",
    "φ",
    "ψ",
    "ω",
    "Δ",
    "Σ",
    "Ω",
)

ENGINEERING_GREEK: tuple[str, ...] = ("ρ", "μ", "ν", "σ", "τ", "γ", "θ", "ω")

_ASCII_TO_GREEK = {
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "epsilon": "ε",
    "theta": "θ",
    "lambda": "λ",
    "mu": "μ",
    "nu": "ν",
    "rho": "ρ",
    "sigma": "σ",
    "tau": "τ",
    "phi": "φ",
    "psi": "ψ",
    "omega": "ω",
}


@dataclass(frozen=True, slots=True, kw_only=True)
class SymbolHypothesis:
    source_span: str
    hypothesized: str
    note: str
    requires_review: bool = True


def propose_symbol_resolutions(text: str) -> tuple[SymbolHypothesis, ...]:
    """Return review-only hypotheses. Does not rewrite `text`."""

    warnings = ocr_ambiguity_warnings(text)
    found: list[SymbolHypothesis] = []
    lowered = f" {text.lower()} "
    for ascii_name, greek in _ASCII_TO_GREEK.items():
        if ascii_name in lowered and greek not in text:
            found.append(
                SymbolHypothesis(
                    source_span=ascii_name,
                    hypothesized=greek,
                    note=f"ASCII '{ascii_name}' may correspond to '{greek}'",
                ),
            )
    for left, right, note in OCR_CONFUSION_PAIRS:
        compact = text.replace(" ", "")
        if left in compact and right not in compact:
            found.append(
                SymbolHypothesis(
                    source_span=left,
                    hypothesized=right,
                    note=note,
                ),
            )
    for warning in warnings:
        found.append(
            SymbolHypothesis(
                source_span=text[:80],
                hypothesized="",
                note=warning,
            ),
        )
    unique: list[SymbolHypothesis] = []
    seen: set[tuple[str, str, str]] = set()
    for item in found:
        key = (item.source_span, item.hypothesized, item.note)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return tuple(unique)
