"""Read-only target comparison; never solves, resizes or accepts an engine."""
from __future__ import annotations

from typing import Any

from core.exceptions import CosmosError
from core.quantity import Quantity
from core.unit import get_unit_registry
from systems.projects.models import PropulsionDesign


def thrust_comparison(design: PropulsionDesign) -> dict[str, Any]:
    result = design.workflow.current_result("performance")
    identity = {"design_id": design.design_id, "design_revision": design.revision,
                "result_id": result.result_id if result else None}
    scope = "Signed difference = calculated minus requested target. Not a tolerance assessment, physical validation or sizing operation."
    unavailable = {**identity, "status": "UNAVAILABLE", "scope": scope, "quantities": {}}
    if result is None or result.design_revision != design.revision:
        return {**unavailable, "code": "NO_CURRENT_PERFORMANCE", "reason": "A performance result for this exact persisted revision is required."}
    target = design.requirements.target_thrust
    achieved = result.outputs.get("thrust")
    if target is None or achieved is None:
        return {**unavailable, "code": "MISSING_THRUST", "reason": "Both explicit requested thrust and source calculated thrust are required."}
    try:
        if isinstance(achieved, dict):
            achieved = Quantity.from_canonical_dict(achieved)
        if not isinstance(target, Quantity) or not isinstance(achieved, Quantity):
            raise TypeError("Thrust quantities must use the canonical Core contract")
        force = get_unit_registry().get("N")
        target_si, achieved_si = target.convert_to(force), achieved.convert_to(force)
        delta = achieved_si - target_si
    except (CosmosError, ValueError, TypeError, KeyError, OverflowError) as error:
        return {**unavailable, "code": "THRUST_QUANTITY", "reason": str(error)}
    return {**identity, "status": "AVAILABLE", "scope": scope,
            "quantities": {"requested_thrust": target_si.to_canonical_dict(),
                           "calculated_thrust": achieved_si.to_canonical_dict(),
                           "signed_difference": delta.to_canonical_dict()},
            "source_target": target.to_canonical_dict(), "source_calculated": achieved.to_canonical_dict(),
            "operating_conditions": result.to_canonical_dict()["inputs"],
            "tolerance_assessment": "NOT_DECLARED", "input_changes": False}
