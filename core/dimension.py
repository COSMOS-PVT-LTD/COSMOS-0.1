"""
COSMOS Core — physical dimensions and dimensional analysis.

Represents SI base dimensions as integer exponent vectors and provides
deterministic dimensional arithmetic for engineering quantities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from core.exceptions import DimensionError

__all__ = (
    "DIMENSIONLESS",
    "LENGTH",
    "MASS",
    "TIME",
    "TEMPERATURE",
    "CURRENT",
    "AMOUNT",
    "LUMINOUS_INTENSITY",
    "AREA",
    "VOLUME",
    "VELOCITY",
    "ACCELERATION",
    "FORCE",
    "PRESSURE",
    "ENERGY",
    "POWER",
    "DENSITY",
    "MASS_FLOW_RATE",
    "Dimension",
)

# Exponent order: length, mass, time, current, temperature,
# amount_of_substance, luminous_intensity
_EXPONENT_FIELDS: Final[tuple[str, ...]] = (
    "length",
    "mass",
    "time",
    "current",
    "temperature",
    "amount",
    "luminous_intensity",
)


@dataclass(frozen=True, slots=True)
class Dimension:
    """
    Immutable SI base-dimension representation.

    Exponents follow the order ``(L, M, T, I, Θ, N, J)``.
    """

    length: int = 0
    mass: int = 0
    time: int = 0
    current: int = 0
    temperature: int = 0
    amount: int = 0
    luminous_intensity: int = 0

    def __post_init__(self) -> None:
        for field_name in _EXPONENT_FIELDS:
            value = getattr(self, field_name)
            if not isinstance(value, int):
                raise DimensionError(
                    f"{field_name} exponent must be an integer."
                )

    @property
    def exponents(self) -> tuple[int, int, int, int, int, int, int]:
        """Return the SI exponent vector ``(L, M, T, I, Θ, N, J)``."""

        return (
            self.length,
            self.mass,
            self.time,
            self.current,
            self.temperature,
            self.amount,
            self.luminous_intensity,
        )

    def is_dimensionless(self) -> bool:
        """Return ``True`` when every base exponent is zero."""

        return all(exponent == 0 for exponent in self.exponents)

    def is_compatible_with(self, other: Dimension) -> bool:
        """Return ``True`` when dimensions are identical."""

        return self.exponents == other.exponents

    def _require_compatible(self, other: Dimension, operation: str) -> None:
        if not self.is_compatible_with(other):
            raise DimensionError(
                f"Incompatible dimensions for {operation}: "
                f"{self!r} and {other!r}."
            )

    def multiply(self, other: Dimension) -> Dimension:
        """Return the dimension of a product ``self × other``."""

        return Dimension(
            length=self.length + other.length,
            mass=self.mass + other.mass,
            time=self.time + other.time,
            current=self.current + other.current,
            temperature=self.temperature + other.temperature,
            amount=self.amount + other.amount,
            luminous_intensity=(
                self.luminous_intensity + other.luminous_intensity
            ),
        )

    def divide(self, other: Dimension) -> Dimension:
        """Return the dimension of a quotient ``self / other``."""

        return Dimension(
            length=self.length - other.length,
            mass=self.mass - other.mass,
            time=self.time - other.time,
            current=self.current - other.current,
            temperature=self.temperature - other.temperature,
            amount=self.amount - other.amount,
            luminous_intensity=(
                self.luminous_intensity - other.luminous_intensity
            ),
        )

    def power(self, exponent: int) -> Dimension:
        """Return the dimension raised to an integer power."""

        if not isinstance(exponent, int):
            raise DimensionError("Dimension power must be an integer.")

        return Dimension(
            length=self.length * exponent,
            mass=self.mass * exponent,
            time=self.time * exponent,
            current=self.current * exponent,
            temperature=self.temperature * exponent,
            amount=self.amount * exponent,
            luminous_intensity=self.luminous_intensity * exponent,
        )

    def __mul__(self, other: Dimension) -> Dimension:
        return self.multiply(other)

    def __truediv__(self, other: Dimension) -> Dimension:
        return self.divide(other)

    def __pow__(self, exponent: int) -> Dimension:
        return self.power(exponent)

    def __repr__(self) -> str:
        if self.is_dimensionless():
            return "Dimension(dimensionless)"

        parts: list[str] = []
        labels = (
            ("m", self.length),
            ("kg", self.mass),
            ("s", self.time),
            ("A", self.current),
            ("K", self.temperature),
            ("mol", self.amount),
            ("cd", self.luminous_intensity),
        )
        for label, exp in labels:
            if exp == 0:
                continue
            if exp == 1:
                parts.append(label)
            else:
                parts.append(f"{label}^{exp}")

        return f"Dimension({'·'.join(parts)})"

    def to_canonical_dict(self) -> dict[str, object]:
        """Return deterministic serialization payload."""

        return {
            "length": self.length,
            "mass": self.mass,
            "time": self.time,
            "current": self.current,
            "temperature": self.temperature,
            "amount": self.amount,
            "luminous_intensity": self.luminous_intensity,
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> Dimension:
        """Reconstruct from canonical dictionary."""

        try:
            return cls(
                length=int(str(data["length"])),
                mass=int(str(data["mass"])),
                time=int(str(data["time"])),
                current=int(str(data["current"])),
                temperature=int(str(data["temperature"])),
                amount=int(str(data["amount"])),
                luminous_intensity=int(str(data["luminous_intensity"])),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise DimensionError(
                "Invalid dimension canonical dictionary."
            ) from exc


DIMENSIONLESS = Dimension()
LENGTH = Dimension(length=1)
MASS = Dimension(mass=1)
TIME = Dimension(time=1)
TEMPERATURE = Dimension(temperature=1)
CURRENT = Dimension(current=1)
AMOUNT = Dimension(amount=1)
LUMINOUS_INTENSITY = Dimension(luminous_intensity=1)

AREA = LENGTH**2
VOLUME = LENGTH**3
VELOCITY = LENGTH / TIME
ACCELERATION = VELOCITY / TIME
FORCE = MASS * ACCELERATION
PRESSURE = FORCE / AREA
ENERGY = FORCE * LENGTH
POWER = ENERGY / TIME
DENSITY = MASS / VOLUME
MASS_FLOW_RATE = MASS / TIME
