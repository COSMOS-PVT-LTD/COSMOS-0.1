"""Standard SI exponent catalog for variable/unit/dimension integration."""

from __future__ import annotations

from knowledge.models.dimension_check import DimensionExponents, check_dimensional_consistency

__all__ = ("SI_EXPONENTS", "check_known_identity")

# L, M, T, I, Θ, N, J
SI_EXPONENTS: dict[str, DimensionExponents] = {
    "Re": (0, 0, 0, 0, 0, 0, 0),
    "Pr": (0, 0, 0, 0, 0, 0, 0),
    "Nu": (0, 0, 0, 0, 0, 0, 0),
    "rho": (-3, 1, 0, 0, 0, 0, 0),
    "V": (1, 0, -1, 0, 0, 0, 0),
    "D": (1, 0, 0, 0, 0, 0, 0),
    "mu": (-1, 1, -1, 0, 0, 0, 0),
    "F": (1, 1, -2, 0, 0, 0, 0),
    "m": (0, 1, 0, 0, 0, 0, 0),
    "a": (1, 0, -2, 0, 0, 0, 0),
    "p": (-1, 1, -2, 0, 0, 0, 0),
    "r": (1, 0, 0, 0, 0, 0, 0),
    "t": (1, 0, 0, 0, 0, 0, 0),
    "sigma": (-1, 1, -2, 0, 0, 0, 0),
    "q": (0, 1, -3, 0, 0, 0, 0),
    "k": (1, 1, -3, 0, -1, 0, 0),
    "dT": (0, 0, 0, 0, 1, 0, 0),
    "dx": (1, 0, 0, 0, 0, 0, 0),
}


def check_known_identity(expression: str) -> bool:
    """Return True when a catalogued identity is dimensionally consistent."""

    symbols = {
        token
        for token in (
            expression.replace("=", " ")
            .replace("*", " ")
            .replace("/", " ")
            .replace("-", " ")
            .split()
        )
        if token in SI_EXPONENTS
    }
    mapping = {symbol: SI_EXPONENTS[symbol] for symbol in symbols}
    return check_dimensional_consistency(expression, mapping).passed
