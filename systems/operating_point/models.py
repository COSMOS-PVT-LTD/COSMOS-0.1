"""Engine operating point — Core Quantity for physical fields."""

from __future__ import annotations

from dataclasses import dataclass

from core.quantity import Quantity

from systems._serialize import optional_quantity_dict, quantity_from_dict

__all__ = ("OperatingPoint",)


@dataclass(slots=True)
class OperatingPoint:
    chamber_pressure: Quantity | None = None
    ambient_pressure: Quantity | None = None
    ambient_temperature: Quantity | None = None
    chamber_temperature: Quantity | None = None
    mass_flow: Quantity | None = None
    oxidizer_mass_flow: Quantity | None = None
    fuel_mass_flow: Quantity | None = None
    mixture_ratio: float | None = None
    gamma: float | None = None
    molecular_weight: float | None = None
    characteristic_velocity: Quantity | None = None
    # Explicit assumption flags — never silent.
    gamma_is_assumption: bool = False
    chamber_temperature_is_assumption: bool = False

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "ambient_pressure": optional_quantity_dict(self.ambient_pressure),
            "ambient_temperature": optional_quantity_dict(self.ambient_temperature),
            "chamber_pressure": optional_quantity_dict(self.chamber_pressure),
            "chamber_temperature": optional_quantity_dict(self.chamber_temperature),
            "chamber_temperature_is_assumption": self.chamber_temperature_is_assumption,
            "characteristic_velocity": optional_quantity_dict(self.characteristic_velocity),
            "fuel_mass_flow": optional_quantity_dict(self.fuel_mass_flow),
            "gamma": self.gamma,
            "gamma_is_assumption": self.gamma_is_assumption,
            "mass_flow": optional_quantity_dict(self.mass_flow),
            "mixture_ratio": self.mixture_ratio,
            "molecular_weight": self.molecular_weight,
            "oxidizer_mass_flow": optional_quantity_dict(self.oxidizer_mass_flow),
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> OperatingPoint:
        return cls(
            chamber_pressure=quantity_from_dict(data.get("chamber_pressure")),
            ambient_pressure=quantity_from_dict(data.get("ambient_pressure")),
            ambient_temperature=quantity_from_dict(data.get("ambient_temperature")),
            chamber_temperature=quantity_from_dict(data.get("chamber_temperature")),
            mass_flow=quantity_from_dict(data.get("mass_flow")),
            oxidizer_mass_flow=quantity_from_dict(data.get("oxidizer_mass_flow")),
            fuel_mass_flow=quantity_from_dict(data.get("fuel_mass_flow")),
            mixture_ratio=(
                None if data.get("mixture_ratio") is None else float(data["mixture_ratio"])
            ),
            gamma=None if data.get("gamma") is None else float(data["gamma"]),
            molecular_weight=(
                None
                if data.get("molecular_weight") is None
                else float(data["molecular_weight"])
            ),
            characteristic_velocity=quantity_from_dict(data.get("characteristic_velocity")),
            gamma_is_assumption=bool(data.get("gamma_is_assumption", False)),
            chamber_temperature_is_assumption=bool(
                data.get("chamber_temperature_is_assumption", False)
            ),
        )
