"""
COSMOS Rocket Propulsion Platform

Module: physics.model
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Traceable identity contracts for executable physical models.

Description:
    Every authoritative physics model records identity, domain, equations,
    assumptions, validity, source, and verification status. This metadata
    is the computational counterpart of knowledge-layer evidence; it does
    not duplicate knowledge models and does not constitute a second solver.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from core.metadata import ObjectMetadata, ProvenanceRecord
from core.version import COSMOS_VERSION

from physics.validity import ValidityStatus

__all__ = (
    "PHYSICS_SCHEMA_VERSION",
    "ModelIdentity",
    "ModelEvaluation",
)

PHYSICS_SCHEMA_VERSION: Final[str] = "0.1.0"


@dataclass(frozen=True, slots=True)
class ModelIdentity:
    """
    Immutable identity and scientific contract of a physics model.

    Attributes
    ----------
    model_id:
        Stable identifier, for example ``PHYS-001.ideal_gas.eos``.
    model_name:
        Human-readable model name.
    physical_domain:
        Physics subdomain (thermodynamics, fluids, ...).
    equations:
        Governing relations in compact mathematical form.
    inputs:
        Named inputs with SI units.
    outputs:
        Named outputs with SI units.
    assumptions:
        Explicit modelling assumptions.
    validity_range:
        Documented range of applicability.
    required_properties:
        Property names the model consumes.
    numerical_method_dependency:
        Numerics contract required, or ``none`` for closed form.
    source:
        Primary scientific source.
    verification_status:
        Declared verification level actually demonstrated.
    limitations:
        Known limitations and non-claims.
    """

    model_id: str
    model_name: str
    physical_domain: str
    equations: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    assumptions: tuple[str, ...]
    validity_range: str
    required_properties: tuple[str, ...] = ()
    numerical_method_dependency: str = "none"
    source: str = ""
    verification_status: str = "software_verification"
    limitations: tuple[str, ...] = ()
    version: str = PHYSICS_SCHEMA_VERSION

    def metadata(self) -> ObjectMetadata:
        """Return Core metadata for this model identity."""

        provenance = (
            ProvenanceRecord(source=self.source)
            if self.source
            else None
        )
        return ObjectMetadata(
            object_id=self.model_id,
            object_type="physics_model",
            schema_version=PHYSICS_SCHEMA_VERSION,
            software_version=COSMOS_VERSION,
            source=self.source or None,
            assumptions=self.assumptions,
            verification_status=self.verification_status,
            provenance=provenance,
        )

    def to_canonical_dict(self) -> dict[str, object]:
        """Return a deterministic dictionary representation."""

        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "physical_domain": self.physical_domain,
            "equations": list(self.equations),
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "assumptions": list(self.assumptions),
            "validity_range": self.validity_range,
            "required_properties": list(self.required_properties),
            "numerical_method_dependency": self.numerical_method_dependency,
            "source": self.source,
            "verification_status": self.verification_status,
            "limitations": list(self.limitations),
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class ModelEvaluation:
    """
    Outcome envelope for a physics evaluation.

    ``payload`` holds model-specific results. Validity is always explicit.
    """

    identity: ModelIdentity
    validity: ValidityStatus
    payload: dict[str, object] = field(default_factory=dict)
    notes: tuple[str, ...] = ()

    def require_valid(self) -> None:
        """Raise if this evaluation is not scientifically applicable."""

        from physics.exceptions import (
            InsufficientDataError,
            ModelValidityError,
            OutOfRangeError,
            PhysicsValidationError,
        )

        if self.validity is ValidityStatus.VALID:
            return
        if self.validity is ValidityStatus.OUT_OF_RANGE:
            raise OutOfRangeError(
                f"{self.identity.model_id} is outside its validity range."
            )
        if self.validity is ValidityStatus.INSUFFICIENT_DATA:
            raise InsufficientDataError(
                f"{self.identity.model_id} lacks required source data."
            )
        if self.validity is ValidityStatus.INVALID_INPUT:
            raise PhysicsValidationError(
                f"{self.identity.model_id} received invalid input."
            )
        raise ModelValidityError(
            f"{self.identity.model_id} status is {self.validity.value}."
        )
