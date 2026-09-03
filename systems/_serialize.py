"""Shared serialization helpers for Systems domain objects."""

from __future__ import annotations

from core.quantity import Quantity

__all__ = ("optional_quantity_dict", "quantity_from_dict")


def optional_quantity_dict(value: Quantity | None) -> dict[str, object] | None:
    if value is None:
        return None
    return value.to_canonical_dict()


def quantity_from_dict(data: object | None) -> Quantity | None:
    if data is None:
        return None
    if not isinstance(data, dict):
        raise TypeError("Quantity canonical payload must be a mapping.")
    return Quantity.from_canonical_dict(data)
