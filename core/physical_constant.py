"""
COSMOS Core — physical constants with units and provenance.

Wraps authoritative constant values as dimensionally typed quantities.
Values must come from :mod:`core.constants` or other verified sources.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.constants import (
    BOLTZMANN_CONSTANT,
    G0,
    GRAVITATIONAL_CONSTANT,
    PLANCK_CONSTANT,
    SPEED_OF_LIGHT,
    STANDARD_ATMOSPHERE,
    UNIVERSAL_GAS_CONSTANT,
)
from core.dimension import AMOUNT, ENERGY, LENGTH, MASS, TEMPERATURE, TIME
from core.metadata import ObjectMetadata
from core.quantity import Quantity
from core.unit import SI, Unit

__all__ = (
    "PhysicalConstant",
    "CODATA_PHYSICAL_CONSTANTS",
)


@dataclass(frozen=True, slots=True)
class PhysicalConstant:
    """
    Authoritative physical constant with typed quantity and metadata.

    Attributes
    ----------
    name:
        Human-readable constant name.
    symbol:
        Standard engineering symbol.
    quantity:
        Constant value with unit.
    metadata:
        Traceability and schema metadata.
    source:
        Short provenance string (standard, publication, etc.).
    """

    name: str
    symbol: str
    quantity: Quantity
    metadata: ObjectMetadata
    source: str

    def to_canonical_dict(self) -> dict[str, object]:
        """Return deterministic serialization payload."""

        return {
            "name": self.name,
            "symbol": self.symbol,
            "quantity": self.quantity.to_canonical_dict(),
            "metadata": self.metadata.to_canonical_dict(),
            "source": self.source,
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> PhysicalConstant:
        """Reconstruct from canonical dictionary."""

        quantity_data = data["quantity"]
        metadata_data = data["metadata"]
        if not isinstance(quantity_data, dict) or not isinstance(metadata_data, dict):
            raise ValueError("Invalid physical constant canonical dictionary.")

        return cls(
            name=str(data["name"]),
            symbol=str(data["symbol"]),
            quantity=Quantity.from_canonical_dict(quantity_data),
            metadata=ObjectMetadata.from_canonical_dict(metadata_data),
            source=str(data["source"]),
        )


def _constant(
    name: str,
    symbol: str,
    magnitude: float,
    unit: Unit,
    *,
    source: str,
    object_id: str,
) -> PhysicalConstant:
    from core.metadata import ObjectMetadata

    return PhysicalConstant(
        name=name,
        symbol=symbol,
        quantity=Quantity(magnitude=magnitude, unit=unit),
        metadata=ObjectMetadata(
            object_id=object_id,
            object_type="PhysicalConstant",
            schema_version="1.0.0",
            source=source,
        ),
        source=source,
    )


CODATA_PHYSICAL_CONSTANTS: tuple[PhysicalConstant, ...] = (
    _constant(
        "Speed of light in vacuum",
        "c",
        SPEED_OF_LIGHT,
        SI.get("m/s"),
        source="SI exact (2019 redefinition)",
        object_id="constant.speed_of_light",
    ),
    _constant(
        "Planck constant",
        "h",
        PLANCK_CONSTANT,
        Unit("J·s", "joule second", ENERGY * TIME),
        source="SI exact (2019 redefinition)",
        object_id="constant.planck",
    ),
    _constant(
        "Boltzmann constant",
        "k",
        BOLTZMANN_CONSTANT,
        Unit("J/K", "joule per kelvin", ENERGY / TEMPERATURE),
        source="SI exact (2019 redefinition)",
        object_id="constant.boltzmann",
    ),
    _constant(
        "Universal molar gas constant",
        "R",
        UNIVERSAL_GAS_CONSTANT,
        Unit("J/(mol·K)", "joule per mole kelvin", ENERGY / (AMOUNT * TEMPERATURE)),
        source="Derived from SI exact k and N_A",
        object_id="constant.gas_constant",
    ),
    _constant(
        "Standard acceleration of gravity",
        "g_0",
        G0,
        SI.get("m/s2"),
        source="ISO 80000-3 conventional value",
        object_id="constant.standard_gravity",
    ),
    _constant(
        "Standard atmosphere",
        "atm",
        STANDARD_ATMOSPHERE,
        SI.get("Pa"),
        source="ISO 80000-3 conventional value",
        object_id="constant.standard_atmosphere",
    ),
    _constant(
        "Newtonian constant of gravitation",
        "G",
        GRAVITATIONAL_CONSTANT,
        Unit(
            "m3/(kg·s2)",
            "metre cubed per kilogram second squared",
            (LENGTH**3) / (MASS * TIME**2),
        ),
        source="CODATA 2022 recommended value",
        object_id="constant.gravitational",
    ),
)
