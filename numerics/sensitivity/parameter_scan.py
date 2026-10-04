"""
COSMOS Rocket Propulsion Platform

Module: numerics.sensitivity.parameter_scan
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral sensitivity.parameter_scan foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.uncertainty.uncertainty_propagation import (
    PropagationResult,
    ScalarModel,
    propagate,
)


def scan(model: ScalarModel, parameter_rows: ArrayLike) -> PropagationResult:
    """Deterministic explicit row scan, preserving caller order."""
    return propagate(model, parameter_rows)
