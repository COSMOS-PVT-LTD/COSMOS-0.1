"""Design requirements for a propulsion analysis."""

from __future__ import annotations

from dataclasses import dataclass

from core.quantity import Quantity

from systems._serialize import optional_quantity_dict, quantity_from_dict

__all__ = ("DesignRequirements",)


@dataclass(slots=True)
class DesignRequirements:
    """
    Engineering requirements. Fields are optional — missing values are None.

    No silent engineering defaults that change meaning.
    """

    target_thrust: Quantity | None = None
    ambient_pressure: Quantity | None = None
    ambient_temperature: Quantity | None = None
    operating_altitude: Quantity | None = None
    burn_duration: Quantity | None = None
    target_chamber_pressure: Quantity | None = None
    mixture_ratio: float | None = None
    expansion_ratio: float | None = None
    cycle_type: str | None = None
    propellant_selection: str | None = None
    notes: str | None = None

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "ambient_pressure": optional_quantity_dict(self.ambient_pressure),
            "ambient_temperature": optional_quantity_dict(self.ambient_temperature),
            "burn_duration": optional_quantity_dict(self.burn_duration),
            "cycle_type": self.cycle_type,
            "expansion_ratio": self.expansion_ratio,
            "mixture_ratio": self.mixture_ratio,
            "notes": self.notes,
            "operating_altitude": optional_quantity_dict(self.operating_altitude),
            "propellant_selection": self.propellant_selection,
            "target_chamber_pressure": optional_quantity_dict(self.target_chamber_pressure),
            "target_thrust": optional_quantity_dict(self.target_thrust),
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> DesignRequirements:
        return cls(
            target_thrust=quantity_from_dict(data.get("target_thrust")),
            ambient_pressure=quantity_from_dict(data.get("ambient_pressure")),
            ambient_temperature=quantity_from_dict(data.get("ambient_temperature")),
            operating_altitude=quantity_from_dict(data.get("operating_altitude")),
            burn_duration=quantity_from_dict(data.get("burn_duration")),
            target_chamber_pressure=quantity_from_dict(data.get("target_chamber_pressure")),
            mixture_ratio=(
                None if data.get("mixture_ratio") is None else float(data["mixture_ratio"])
            ),
            expansion_ratio=(
                None if data.get("expansion_ratio") is None else float(data["expansion_ratio"])
            ),
            cycle_type=None if data.get("cycle_type") is None else str(data["cycle_type"]),
            propellant_selection=(
                None
                if data.get("propellant_selection") is None
                else str(data["propellant_selection"])
            ),
            notes=None if data.get("notes") is None else str(data["notes"]),
        )
