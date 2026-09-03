"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.fluid_properties
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Traceable fluid-property records and range-checked evaluation.

Description:
    Property data carry units, phase, temperature/pressure validity, source,
    and optional uncertainty. Evaluation never silently extrapolates.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.dimension import PRESSURE, TEMPERATURE, Dimension
from core.quantity import Quantity
from core.unit import Unit
from core.validation import validate_positive

from physics.exceptions import OutOfRangeError
from physics.model import ModelEvaluation, ModelIdentity
from physics.quantities import as_si, quantity
from physics.validity import ValidityStatus

__all__ = (
    "FLUID_PROPERTY_MODEL",
    "FluidKind",
    "PropertyEvaluation",
    "PropertyRecord",
    "evaluate_record",
)

FLUID_PROPERTY_MODEL = ModelIdentity(
    model_id="PHYS-002.fluid_properties.record",
    model_name="Sourced fluid property record",
    physical_domain="fluids",
    equations=("property = tabulated or correlation value at (T, p, phase)",),
    inputs=("fluid identity", "T [K]", "p [Pa]"),
    outputs=("property with unit and validity",),
    assumptions=("Record applies only inside its documented validity window.",),
    validity_range="Per-record temperature and pressure bounds; no silent extrapolation.",
    source="Per-record provenance (NIST, NASA, Sutherland, Incropera, MIL-SPEC).",
    verification_status="software_verification: range gates; reference-point checks",
    limitations=(
        "A single reference-state value is not a complete equation of state.",
        "Uncertainty is recorded only when the source provides it.",
    ),
)


class FluidKind(str, Enum):
    """High-level fluid category."""

    OXIDIZER = "oxidizer"
    FUEL = "fuel"
    PRESSURANT = "pressurant"
    INERT = "inert"
    COOLANT = "coolant"


@dataclass(frozen=True, slots=True)
class PropertyRecord:
    """One sourced physical property with an applicability window."""

    fluid_id: str
    property_name: str
    value: float
    unit: Unit
    dimension: Dimension
    phase: str
    temperature_min_k: float
    temperature_max_k: float
    pressure_min_pa: float | None
    pressure_max_pa: float | None
    source: str
    reference_temperature_k: float
    reference_pressure_pa: float | None = None
    uncertainty: float | None = None
    uncertainty_kind: str | None = None
    notes: str = ""


@dataclass(frozen=True, slots=True)
class PropertyEvaluation:
    """Evaluated property with explicit validity."""

    record: PropertyRecord
    stored_quantity: Quantity
    temperature: Quantity
    pressure: Quantity | None
    validity: ValidityStatus
    identity: ModelIdentity = FLUID_PROPERTY_MODEL

    @property
    def quantity(self) -> Quantity:
        """
        Return the property quantity when validity is ``VALID``.

        Raises
        ------
        OutOfRangeError
            If the evaluation is not valid. Use ``stored_quantity`` for
            diagnostic inspection of invalid states.
        """

        if self.validity is not ValidityStatus.VALID:
            raise OutOfRangeError(
                f"{self.record.fluid_id} {self.record.property_name} is not valid "
                f"(status={self.validity.value}). Use stored_quantity for diagnostics."
            )
        return self.stored_quantity

    def require_valid(self) -> Quantity:
        """Return the quantity or raise if the state is out of range."""

        if self.validity is ValidityStatus.VALID:
            return self.stored_quantity
        if self.validity is ValidityStatus.OUT_OF_RANGE:
            raise OutOfRangeError(
                f"{self.record.fluid_id} {self.record.property_name} is outside "
                f"[{self.record.temperature_min_k}, {self.record.temperature_max_k}] K."
            )
        raise OutOfRangeError(
            f"{self.record.fluid_id} {self.record.property_name} status "
            f"{self.validity.value}."
        )

    def to_model_evaluation(self) -> ModelEvaluation:
        """Return a traceability envelope for this evaluation."""

        return ModelEvaluation(
            identity=self.identity,
            validity=self.validity,
            payload={
                "fluid_id": self.record.fluid_id,
                "property_name": self.record.property_name,
                "temperature_k": self.temperature.to_si(),
                "pressure_pa": None if self.pressure is None else self.pressure.to_si(),
                "value_si": self.stored_quantity.to_si(),
            },
            notes=(f"source={self.record.source}",),
        )


def evaluate_record(
    record: PropertyRecord,
    temperature: Quantity,
    pressure: Quantity | None = None,
    *,
    allow_extrapolation: bool = False,
) -> PropertyEvaluation:
    """
    Evaluate a property record at ``temperature`` (and optional ``pressure``).

    If ``allow_extrapolation`` is true and the state is outside the window,
    the recorded reference value is returned with status ``EXTRAPOLATED``.
    The numerical value is still the sourced reference value — this is not
    a predictive extrapolation model.
    """

    t = validate_positive(as_si(temperature, TEMPERATURE, "temperature"), "temperature")
    p: float | None = None
    if pressure is not None:
        p = validate_positive(as_si(pressure, PRESSURE, "pressure"), "pressure")

    in_temperature = record.temperature_min_k <= t <= record.temperature_max_k
    in_pressure = True
    if p is not None and record.pressure_min_pa is not None:
        in_pressure = record.pressure_min_pa <= p
        if record.pressure_max_pa is not None:
            in_pressure = in_pressure and p <= record.pressure_max_pa

    validity = ValidityStatus.VALID if (in_temperature and in_pressure) else (
        ValidityStatus.EXTRAPOLATED if allow_extrapolation else ValidityStatus.OUT_OF_RANGE
    )
    return PropertyEvaluation(
        record=record,
        stored_quantity=quantity(record.value, record.unit),
        temperature=temperature,
        pressure=pressure,
        validity=validity,
    )
