"""
COSMOS Rocket Propulsion Platform

Module: physics.exceptions
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain exception types for the physics layer.

Description:
    Physics-specific failures inherit from Core ``CosmosError`` so callers
    may catch either a precise physics failure or any COSMOS failure.
    Physical invalidity is never converted into a plausible numerical result.
"""

from __future__ import annotations

from core.exceptions import CosmosError, ValidationError

__all__ = (
    "PhysicsError",
    "PhysicsValidationError",
    "ModelValidityError",
    "OutOfRangeError",
    "InsufficientDataError",
    "InvalidCompositionError",
    "ThermodynamicsError",
    "FluidPropertyError",
    "ThermochemistryError",
    "CompressibleFlowError",
    "HeatTransferError",
    "MaterialPropertyError",
    "SolidMechanicsError",
)


class PhysicsError(CosmosError):
    """Base class for physics-layer failures."""


class PhysicsValidationError(ValidationError, PhysicsError):
    """Indicate that a physics input or composition failed validation."""


class ModelValidityError(PhysicsError):
    """Indicate that a model cannot be applied to the supplied state."""


class OutOfRangeError(ModelValidityError):
    """Indicate that an input lies outside the model's validity range."""


class InsufficientDataError(ModelValidityError):
    """Indicate that required property or coefficient data is missing."""


class InvalidCompositionError(PhysicsValidationError):
    """Indicate that a chemical composition is physically invalid."""


class ThermodynamicsError(PhysicsError):
    """Thermodynamics-domain failure."""


class FluidPropertyError(PhysicsError):
    """Fluid-property evaluation failure."""


class ThermochemistryError(PhysicsError):
    """Thermochemistry-domain failure."""


class CompressibleFlowError(PhysicsError):
    """Compressible-flow relation failure."""


class HeatTransferError(PhysicsError):
    """Heat-transfer model failure."""


class MaterialPropertyError(PhysicsError):
    """Material-property evaluation failure."""


class SolidMechanicsError(PhysicsError):
    """Solid-mechanics constitutive-model failure."""
