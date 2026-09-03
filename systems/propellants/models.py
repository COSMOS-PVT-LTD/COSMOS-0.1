"""Propellant configuration — references Physics registry IDs, no property DB."""

from __future__ import annotations

from dataclasses import dataclass

from core.quantity import Quantity

from systems._serialize import optional_quantity_dict, quantity_from_dict

__all__ = ("PropellantConfiguration",)


@dataclass(slots=True)
class PropellantConfiguration:
    oxidizer_id: str | None = None
    fuel_id: str | None = None
    mixture_ratio: float | None = None
    oxidizer_state: str | None = None
    fuel_state: str | None = None
    oxidizer_temperature: Quantity | None = None
    fuel_temperature: Quantity | None = None
    oxidizer_pressure: Quantity | None = None
    fuel_pressure: Quantity | None = None

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "fuel_id": self.fuel_id,
            "fuel_pressure": optional_quantity_dict(self.fuel_pressure),
            "fuel_state": self.fuel_state,
            "fuel_temperature": optional_quantity_dict(self.fuel_temperature),
            "mixture_ratio": self.mixture_ratio,
            "oxidizer_id": self.oxidizer_id,
            "oxidizer_pressure": optional_quantity_dict(self.oxidizer_pressure),
            "oxidizer_state": self.oxidizer_state,
            "oxidizer_temperature": optional_quantity_dict(self.oxidizer_temperature),
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> PropellantConfiguration:
        return cls(
            oxidizer_id=None if data.get("oxidizer_id") is None else str(data["oxidizer_id"]),
            fuel_id=None if data.get("fuel_id") is None else str(data["fuel_id"]),
            mixture_ratio=(
                None if data.get("mixture_ratio") is None else float(data["mixture_ratio"])
            ),
            oxidizer_state=(
                None if data.get("oxidizer_state") is None else str(data["oxidizer_state"])
            ),
            fuel_state=None if data.get("fuel_state") is None else str(data["fuel_state"]),
            oxidizer_temperature=quantity_from_dict(data.get("oxidizer_temperature")),
            fuel_temperature=quantity_from_dict(data.get("fuel_temperature")),
            oxidizer_pressure=quantity_from_dict(data.get("oxidizer_pressure")),
            fuel_pressure=quantity_from_dict(data.get("fuel_pressure")),
        )
