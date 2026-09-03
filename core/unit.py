"""
COSMOS Core — engineering unit definitions.

Provides immutable unit metadata, SI conversion factors, and a registry of
canonical SI and commonly used engineering units. Scalar conversion helpers
remain in :mod:`core.units`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from core.constants import CELSIUS_ZERO_IN_KELVIN
from core.dimension import (
    ACCELERATION,
    AMOUNT,
    AREA,
    CURRENT,
    DENSITY,
    DIMENSIONLESS,
    ENERGY,
    FORCE,
    LENGTH,
    LUMINOUS_INTENSITY,
    MASS,
    MASS_FLOW_RATE,
    POWER,
    PRESSURE,
    TEMPERATURE,
    TIME,
    VELOCITY,
    VOLUME,
    Dimension,
)
from core.exceptions import UnitError

__all__ = (
    "Unit",
    "UnitRegistry",
    "SI",
    "get_unit_registry",
)


@dataclass(frozen=True, slots=True)
class Unit:
    """
    Immutable engineering unit definition.

    Conversion to SI follows ``value_si = magnitude * factor + offset``.
    For affine units such as Celsius, ``factor`` scales to the SI unit and
    ``offset`` completes the transform.
    """

    symbol: str
    name: str
    dimension: Dimension
    si_scale: float = 1.0
    si_offset: float = 0.0

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise UnitError("Unit symbol cannot be blank.")
        if not self.name.strip():
            raise UnitError("Unit name cannot be blank.")
        if self.si_scale == 0.0:
            raise UnitError("Unit si_scale cannot be zero.")

    def factor_to_si(self) -> float:
        """Multiplicative factor converting one unit to SI."""

        return self.si_scale

    def offset_to_si(self) -> float:
        """Additive offset applied after scaling to reach SI."""

        return self.si_offset

    def convert_to_si(self, magnitude: float) -> float:
        """Convert a magnitude in this unit to SI."""

        return magnitude * self.si_scale + self.si_offset

    def convert_from_si(self, magnitude_si: float) -> float:
        """Convert an SI magnitude to this unit."""

        return (magnitude_si - self.si_offset) / self.si_scale

    def is_compatible_with(self, other: Unit) -> bool:
        """Return ``True`` when units share the same dimension."""

        return self.dimension.is_compatible_with(other.dimension)

    @property
    def is_affine(self) -> bool:
        """Return ``True`` when the unit uses a non-zero SI offset."""

        return self.si_offset != 0.0

    def to_canonical_dict(self) -> dict[str, object]:
        """Return deterministic serialization payload."""

        return {
            "symbol": self.symbol,
            "name": self.name,
            "dimension": self.dimension.to_canonical_dict(),
            "factor_to_si": self.si_scale,
            "offset_to_si": self.si_offset,
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> Unit:
        """Reconstruct from canonical dictionary."""

        try:
            dimension_data = data["dimension"]
            if not isinstance(dimension_data, dict):
                raise TypeError
            return cls(
                symbol=str(data["symbol"]),
                name=str(data["name"]),
                dimension=Dimension.from_canonical_dict(dimension_data),
                si_scale=float(str(data["factor_to_si"])),
                si_offset=float(str(data["offset_to_si"])),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise UnitError("Invalid unit canonical dictionary.") from exc


class UnitRegistry:
    """Registry of canonical units addressable by symbol."""

    def __init__(self, units: tuple[Unit, ...]) -> None:
        self._units: dict[str, Unit] = {}
        for unit in units:
            key = unit.symbol.casefold()
            if key in self._units:
                raise UnitError(
                    f"Duplicate unit symbol registered: {unit.symbol!r}."
                )
            self._units[key] = unit

    def get(self, symbol: str) -> Unit:
        """Return the unit for ``symbol``."""

        key = symbol.casefold()
        try:
            return self._units[key]
        except KeyError as exc:
            raise UnitError(f"Unknown unit symbol: {symbol!r}.") from exc

    def symbols(self) -> tuple[str, ...]:
        """Return registered symbols in deterministic order."""

        return tuple(
            self._units[key].symbol
            for key in sorted(self._units)
        )

    def to_canonical_dict(self) -> dict[str, object]:
        """Serialize all registered units."""

        return {
            "units": [
                self._units[key].to_canonical_dict()
                for key in sorted(self._units)
            ]
        }


def _build_si_registry() -> UnitRegistry:
    """Construct the default SI and engineering unit registry."""

    units = (
        Unit("1", "dimensionless", DIMENSIONLESS),
        Unit("m", "metre", LENGTH),
        Unit("mm", "millimetre", LENGTH, si_scale=1.0e-3),
        Unit("cm", "centimetre", LENGTH, si_scale=1.0e-2),
        Unit("km", "kilometre", LENGTH, si_scale=1.0e3),
        Unit("in", "inch", LENGTH, si_scale=0.0254),
        Unit("ft", "foot", LENGTH, si_scale=0.3048),
        Unit("kg", "kilogram", MASS),
        Unit("lb", "pound mass", MASS, si_scale=0.453_592_37),
        Unit("s", "second", TIME),
        Unit("min", "minute", TIME, si_scale=60.0),
        Unit("h", "hour", TIME, si_scale=3600.0),
        Unit("K", "kelvin", TEMPERATURE),
        Unit(
            "degC",
            "degree Celsius",
            TEMPERATURE,
            si_scale=1.0,
            si_offset=CELSIUS_ZERO_IN_KELVIN,
        ),
        Unit("A", "ampere", CURRENT),
        Unit("mol", "mole", AMOUNT),
        Unit("cd", "candela", LUMINOUS_INTENSITY),
        Unit("m2", "square metre", AREA),
        Unit("m3", "cubic metre", VOLUME),
        Unit("m/s", "metre per second", VELOCITY),
        Unit("m/s2", "metre per second squared", ACCELERATION),
        Unit("N", "newton", FORCE),
        Unit("lbf", "pound-force", FORCE, si_scale=4.448_221_615_260_5),
        Unit("Pa", "pascal", PRESSURE),
        Unit("bar", "bar", PRESSURE, si_scale=1.0e5),
        Unit("psi", "pound per square inch", PRESSURE, si_scale=6894.757_293_168_361),
        Unit("atm", "standard atmosphere", PRESSURE, si_scale=101_325.0),
        Unit("J", "joule", ENERGY),
        Unit("W", "watt", POWER),
        Unit("kg/m3", "kilogram per cubic metre", DENSITY),
        Unit("kg/s", "kilogram per second", MASS_FLOW_RATE),
        Unit("rad", "radian", DIMENSIONLESS),
        Unit("deg", "degree", DIMENSIONLESS, si_scale=0.017_453_292_519_943_295),
    )
    return UnitRegistry(units)


SI: Final[UnitRegistry] = _build_si_registry()


def get_unit_registry() -> UnitRegistry:
    """Return the canonical SI unit registry."""

    return SI
