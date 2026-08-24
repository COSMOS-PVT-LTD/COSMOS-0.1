"""Dimensional consistency check for simple product/quotient identities."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ("DimensionCheckResult", "DimensionExponents", "check_dimensional_consistency")

# SI base order: L, M, T, I, Θ, N, J
DimensionExponents = tuple[int, int, int, int, int, int, int]


@dataclass(frozen=True, slots=True, kw_only=True)
class DimensionCheckResult:
    expression: str
    passed: bool
    left_dimension: DimensionExponents | None
    right_dimension: DimensionExponents | None
    reason: str


def check_dimensional_consistency(
    expression: str,
    variable_exponents: dict[str, DimensionExponents],
) -> DimensionCheckResult:
    """Check identities such as Re = rho*V*D/mu using SI exponent 7-tuples."""

    if "=" not in expression:
        return DimensionCheckResult(
            expression=expression,
            passed=False,
            left_dimension=None,
            right_dimension=None,
            reason="expression must contain '='.",
        )

    left, right = (part.strip() for part in expression.split("=", 1))
    try:
        left_dim = _resolve(left, variable_exponents)
        right_dim = _evaluate(right, variable_exponents)
    except KeyError as exc:
        return DimensionCheckResult(
            expression=expression,
            passed=False,
            left_dimension=None,
            right_dimension=None,
            reason=f"unknown symbol {exc}.",
        )

    passed = left_dim == right_dim
    return DimensionCheckResult(
        expression=expression,
        passed=passed,
        left_dimension=left_dim,
        right_dimension=right_dim,
        reason="PASS" if passed else "dimension mismatch",
    )


def _resolve(symbol: str, mapping: dict[str, DimensionExponents]) -> DimensionExponents:
    cleaned = symbol.strip()
    if cleaned not in mapping:
        raise KeyError(cleaned)
    return mapping[cleaned]


def _add(left: DimensionExponents, right: DimensionExponents) -> DimensionExponents:
    return tuple(a + b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _sub(left: DimensionExponents, right: DimensionExponents) -> DimensionExponents:
    return tuple(a - b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _evaluate(expression: str, mapping: dict[str, DimensionExponents]) -> DimensionExponents:
    tokens = expression.replace(" ", "").replace("×", "*")
    factors = tokens.split("/")
    numerator = factors[0].split("*")
    result = _resolve(numerator[0], mapping)
    for factor in numerator[1:]:
        result = _add(result, _resolve(factor, mapping))
    for denominator in factors[1:]:
        for factor in denominator.split("*"):
            result = _sub(result, _resolve(factor, mapping))
    return result
