"""OCR confusion pairs. Ambiguity is REVIEW_REQUIRED, never guessed away."""

from __future__ import annotations

__all__ = ("OCR_CONFUSION_PAIRS", "ocr_ambiguity_warnings")

OCR_CONFUSION_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("u", "mu", "mu vs u"),
    ("p", "rho", "rho vs p"),
    ("v", "nu", "nu vs v"),
    ("l", "lambda", "lambda vs l"),
    ("O", "0", "0 vs O"),
    ("l", "1", "1 vs l"),
    ("x", "×", "x vs ×"),
    ("-", "−", "minus vs hyphen"),
)


def ocr_ambiguity_warnings(text: str) -> tuple[str, ...]:
    """Return visible OCR uncertainty notes. Does not rewrite the text."""

    if not text.strip():
        return ()
    warnings: list[str] = []
    compact = text.replace(" ", "")
    lowered = text.lower()
    if "re=" in compact.lower() or "reynolds" in lowered:
        if " u " in f" {text} " or "*u*" in compact.lower() or compact.lower().startswith("u*"):
            warnings.append("REVIEW_REQUIRED: mu vs u")
        if " p " in f" {text} " or "*p*" in compact.lower():
            warnings.append("REVIEW_REQUIRED: rho vs p")
    if "µ" not in text and "μ" not in text and "mu" not in lowered and "rho" in lowered:
        warnings.append("Greek mu not recovered from source image")
    return tuple(dict.fromkeys(warnings))
