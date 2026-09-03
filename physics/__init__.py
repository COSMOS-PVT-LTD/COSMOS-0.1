"""
COSMOS Rocket Propulsion Platform

Module: physics
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Authoritative physical-model layer for COSMOS 0.1.

Description:
    Physics owns executable physical relationships. It consumes Core
    contracts (Quantity, Unit, Dimension, validation, exceptions,
    constants) and a Numerics port for scalar inverses. It does not
    contain GUI, API, persistence, or engineering design workflows.
"""

from __future__ import annotations

from physics.validity import ValidityStatus

__all__ = ("ValidityStatus",)
