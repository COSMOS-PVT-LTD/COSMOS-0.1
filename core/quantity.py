"""
COSMOS Core — dimensionally safe engineering quantities.

Quantities bind a finite numeric magnitude to a unit and enforce dimensional
compatibility for arithmetic. Unit conversion is explicit and never silent.

Affine temperature semantics
----------------------------
Absolute temperatures (for example ``degC``, ``K``) cannot be added to one
another. Subtraction of two absolute temperatures yields a **temperature
interval** in kelvin. A temperature interval may be added to an absolute
temperature. Multiplication of an affine absolute quantity by another quantity
uses the thermodynamic SI magnitude (``to_si()``) so offsets are not dropped.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Final, Union

from core.dimension import DIMENSIONLESS, TEMPERATURE, Dimension
from core.exceptions import DimensionError, InvalidInputError, UnitError
from core.unit import Unit
from core.validation import validate_finite

__all__ = (
    "Quantity",
    "QuantityKind",
    "ScalarLike",
    "dimensionless",
    "temperature_interval",
)

ScalarLike = Union[int, float]
_RELATIVE_TOLERANCE: Final[float] = 1.0e-12


class QuantityKind(str, Enum):
    """Distinguish absolute values from interval/difference quantities."""

    ABSOLUTE = "absolute"
    INTERVAL = "interval"


def _as_float(value: ScalarLike, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidInputError(f"{name} must be a real number.")
    numeric = float(value)
    return validate_finite(numeric, name)


def _kelvin_interval_unit() -> Unit:
    from core.unit import SI

    return SI.get("K")


@dataclass(frozen=True, slots=True)
class Quantity:
    """
    Immutable engineering quantity with unit and dimensional safety.

    Parameters
    ----------
    magnitude:
        Numeric value expressed in ``unit``.
    unit:
        Measurement unit attached to ``magnitude``.
    kind:
        ``ABSOLUTE`` for point values; ``INTERVAL`` for differences such as
        temperature deltas (always expressed in kelvin).
    """

    magnitude: float
    unit: Unit
    kind: QuantityKind = QuantityKind.ABSOLUTE

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "magnitude",
            validate_finite(self.magnitude, "magnitude"),
        )
        if self.kind is QuantityKind.INTERVAL:
            if not self.unit.dimension.is_compatible_with(TEMPERATURE):
                raise UnitError("Interval quantities are supported for temperature only.")
            if self.unit.is_affine:
                raise UnitError("Temperature intervals must be expressed in kelvin.")

    def dimension(self) -> Dimension:
        """Return the physical dimension."""

        return self.unit.dimension

    def is_temperature(self) -> bool:
        """Return ``True`` when the quantity has temperature dimension."""

        return self.dimension().is_compatible_with(TEMPERATURE)

    def to_si(self) -> float:
        """
        Return magnitude in SI units for this dimension.

        Temperature intervals return the kelvin delta directly.
        """

        if self.kind is QuantityKind.INTERVAL:
            return self.magnitude * self.unit.si_scale
        return self.unit.convert_to_si(self.magnitude)

    def _algebraic_si_value(self) -> float:
        """Return the SI value used in product/quotient algebra."""

        if self.kind is QuantityKind.INTERVAL:
            return self.magnitude * self.unit.si_scale
        if self.unit.is_affine:
            return self.to_si()
        return self.magnitude * self.unit.si_scale

    def to_canonical_dict(self) -> dict[str, object]:
        """Return deterministic serialization payload."""

        payload: dict[str, object] = {
            "magnitude": self.magnitude,
            "unit": self.unit.to_canonical_dict(),
        }
        if self.kind is not QuantityKind.ABSOLUTE:
            payload["kind"] = self.kind.value
        return payload

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> Quantity:
        """Reconstruct from canonical dictionary."""

        try:
            unit_data = data["unit"]
            if not isinstance(unit_data, dict):
                raise TypeError
            kind_raw = data.get("kind", QuantityKind.ABSOLUTE.value)
            kind = QuantityKind(str(kind_raw))
            return cls(
                magnitude=float(str(data["magnitude"])),
                unit=Unit.from_canonical_dict(unit_data),
                kind=kind,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise UnitError("Invalid quantity canonical dictionary.") from exc

    def convert_to(self, target: Unit) -> Quantity:
        """
        Convert explicitly to ``target``.

        Temperature intervals remain intervals and convert only among
        offset-free temperature units (kelvin).
        """

        if self.kind is QuantityKind.INTERVAL:
            if target.is_affine:
                raise UnitError("Temperature intervals cannot be converted to affine units.")
            if not target.dimension.is_compatible_with(TEMPERATURE):
                raise DimensionError("Temperature interval conversion requires temperature units.")
            si_delta = self.to_si()
            return Quantity(
                magnitude=target.convert_from_si(si_delta),
                unit=target,
                kind=QuantityKind.INTERVAL,
            )

        if not self.unit.is_compatible_with(target):
            raise DimensionError(
                f"Cannot convert {self.unit.symbol!r} to "
                f"{target.symbol!r}: incompatible dimensions."
            )

        si_value = self.to_si()
        return Quantity(
            magnitude=target.convert_from_si(si_value),
            unit=target,
            kind=QuantityKind.ABSOLUTE,
        )

    def _require_same_dimension(self, other: Quantity, operation: str) -> None:
        if not self.dimension().is_compatible_with(other.dimension()):
            raise DimensionError(
                f"Incompatible dimensions for {operation}: "
                f"{self.dimension()!r} and {other.dimension()!r}."
            )

    def _temperature_add(self, other: Quantity) -> Quantity:
        if self.kind is QuantityKind.ABSOLUTE and other.kind is QuantityKind.ABSOLUTE:
            raise UnitError("Cannot add absolute temperatures.")

        if self.kind is QuantityKind.INTERVAL and other.kind is QuantityKind.INTERVAL:
            si_sum = self.to_si() + other.to_si()
            return temperature_interval(si_sum)

        if self.kind is QuantityKind.ABSOLUTE and other.kind is QuantityKind.INTERVAL:
            absolute, interval = self, other
        elif self.kind is QuantityKind.INTERVAL and other.kind is QuantityKind.ABSOLUTE:
            absolute, interval = other, self
        else:
            raise UnitError("Invalid temperature addition combination.")

        si_result = absolute.to_si() + interval.to_si()
        return Quantity(
            magnitude=absolute.unit.convert_from_si(si_result),
            unit=absolute.unit,
            kind=QuantityKind.ABSOLUTE,
        )

    def __add__(self, other: Quantity) -> Quantity:
        self._require_same_dimension(other, "addition")

        if self.is_temperature() and other.is_temperature():
            return self._temperature_add(other)

        if self.kind is QuantityKind.INTERVAL or other.kind is QuantityKind.INTERVAL:
            raise UnitError("Interval arithmetic is defined for temperature only.")

        if self.unit.is_affine or other.unit.is_affine:
            raise UnitError(
                "Cannot add absolute quantities with affine units. "
                "Convert explicitly or use interval semantics."
            )

        si_sum = self.to_si() + other.to_si()
        return Quantity(
            magnitude=self.unit.convert_from_si(si_sum),
            unit=self.unit,
            kind=QuantityKind.ABSOLUTE,
        )

    def __sub__(self, other: Quantity) -> Quantity:
        self._require_same_dimension(other, "subtraction")

        if self.is_temperature() and other.is_temperature():
            if self.kind is QuantityKind.ABSOLUTE and other.kind is QuantityKind.ABSOLUTE:
                return temperature_interval(self.to_si() - other.to_si())
            if self.kind is QuantityKind.ABSOLUTE and other.kind is QuantityKind.INTERVAL:
                si_result = self.to_si() - other.to_si()
                return Quantity(
                    magnitude=self.unit.convert_from_si(si_result),
                    unit=self.unit,
                    kind=QuantityKind.ABSOLUTE,
                )
            if self.kind is QuantityKind.INTERVAL and other.kind is QuantityKind.INTERVAL:
                return temperature_interval(self.to_si() - other.to_si())
            raise UnitError("Invalid temperature subtraction combination.")

        if self.kind is QuantityKind.INTERVAL or other.kind is QuantityKind.INTERVAL:
            raise UnitError("Interval arithmetic is defined for temperature only.")

        if self.unit.is_affine or other.unit.is_affine:
            si_difference = self.to_si() - other.to_si()
            if self.unit.is_affine:
                return temperature_interval(si_difference)
            return Quantity(
                magnitude=self.unit.convert_from_si(si_difference),
                unit=self.unit,
                kind=QuantityKind.ABSOLUTE,
            )

        si_difference = self.to_si() - other.to_si()
        return Quantity(
            magnitude=self.unit.convert_from_si(si_difference),
            unit=self.unit,
            kind=QuantityKind.ABSOLUTE,
        )

    def __mul__(self, other: ScalarLike | Quantity) -> Quantity:
        if isinstance(other, Quantity):
            si_product = self._algebraic_si_value() * other._algebraic_si_value()
            return Quantity(
                magnitude=si_product,
                unit=Unit(
                    symbol=f"{self.unit.symbol}·{other.unit.symbol}",
                    name=f"{self.unit.name}·{other.unit.name}",
                    dimension=self.dimension() * other.dimension(),
                    si_scale=1.0,
                    si_offset=0.0,
                ),
                kind=QuantityKind.ABSOLUTE,
            )

        scalar = _as_float(other, "scalar")
        if self.unit.is_affine and self.kind is QuantityKind.ABSOLUTE:
            return Quantity(
                magnitude=self.magnitude * scalar,
                unit=self.unit,
                kind=QuantityKind.ABSOLUTE,
            )
        return Quantity(
            magnitude=self.magnitude * scalar,
            unit=self.unit,
            kind=self.kind,
        )

    def __rmul__(self, other: ScalarLike) -> Quantity:
        return self.__mul__(other)

    def __truediv__(self, other: ScalarLike | Quantity) -> Quantity:
        if isinstance(other, Quantity):
            if other._algebraic_si_value() == 0.0:
                raise InvalidInputError("Division by zero quantity.")
            si_quotient = self._algebraic_si_value() / other._algebraic_si_value()
            if (
                self.is_temperature()
                and other.is_temperature()
                and self.kind is QuantityKind.INTERVAL
                and other.kind is QuantityKind.INTERVAL
            ):
                return dimensionless(si_quotient)
            return Quantity(
                magnitude=si_quotient,
                unit=Unit(
                    symbol=f"{self.unit.symbol}/{other.unit.symbol}",
                    name=f"{self.unit.name}/{other.unit.name}",
                    dimension=self.dimension() / other.dimension(),
                    si_scale=1.0,
                    si_offset=0.0,
                ),
                kind=QuantityKind.ABSOLUTE,
            )

        scalar = _as_float(other, "scalar")
        if scalar == 0.0:
            raise InvalidInputError("Division by zero scalar.")
        return Quantity(
            magnitude=self.magnitude / scalar,
            unit=self.unit,
            kind=self.kind,
        )

    def __neg__(self) -> Quantity:
        return Quantity(magnitude=-self.magnitude, unit=self.unit, kind=self.kind)

    def __abs__(self) -> Quantity:
        return Quantity(magnitude=abs(self.magnitude), unit=self.unit, kind=self.kind)

    def is_dimensionless(self) -> bool:
        """Return ``True`` when the quantity is dimensionless."""

        return self.dimension().is_dimensionless()

    def approx_equal(
        self,
        other: Quantity,
        *,
        rel_tol: float = _RELATIVE_TOLERANCE,
        abs_tol: float = 0.0,
    ) -> bool:
        """Compare two quantities after converting to SI."""

        self._require_same_dimension(other, "comparison")
        return math.isclose(
            self.to_si(),
            other.to_si(),
            rel_tol=rel_tol,
            abs_tol=abs_tol,
        )

    def __repr__(self) -> str:
        kind_suffix = "" if self.kind is QuantityKind.ABSOLUTE else f", {self.kind.value}"
        return f"Quantity({self.magnitude} {self.unit.symbol}{kind_suffix})"


def dimensionless(value: ScalarLike) -> Quantity:
    """Construct a dimensionless quantity."""

    return Quantity(
        magnitude=_as_float(value, "magnitude"),
        unit=Unit("1", "dimensionless", DIMENSIONLESS),
    )


def temperature_interval(delta_kelvin: ScalarLike) -> Quantity:
    """Construct a temperature interval expressed in kelvin."""

    return Quantity(
        magnitude=_as_float(delta_kelvin, "delta_kelvin"),
        unit=_kelvin_interval_unit(),
        kind=QuantityKind.INTERVAL,
    )
