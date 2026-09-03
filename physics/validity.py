"""
COSMOS Rocket Propulsion Platform

Module: physics.validity
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Explicit model-validity statuses for physics evaluations.

Description:
    Empirical and constitutive models must report validity rather than
    silently clamp, extrapolate, or substitute another correlation.
"""

from __future__ import annotations

from enum import Enum

__all__ = ("ValidityStatus",)


class ValidityStatus(str, Enum):
    """Application status of a physical model evaluation."""

    VALID = "VALID"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    EXTRAPOLATED = "EXTRAPOLATED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    INVALID_INPUT = "INVALID_INPUT"
    SINGULAR = "SINGULAR"
    DEFERRED = "DEFERRED"
