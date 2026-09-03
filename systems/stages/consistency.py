"""Stage 15 — system consistency checks (no invented physics)."""

from __future__ import annotations

from systems.contracts.results import (
    ResultStatus,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import make_result

__all__ = ("run_consistency_stage",)

_REQUIRED_FOR_REVIEW = (
    "requirements",
    "propellants",
    "operating_point",
    "performance",
)


def run_consistency_stage(design: PropulsionDesign) -> object:
    """
    Check design-state consistency across the workflow graph.

    Does not invent missing Physics. Flags stale/missing/not-implemented
    and simple continuity mismatches already present in stored results.
    """

    stage_id = "consistency"
    checks: list[str] = []
    violations: list[str] = []
    warnings: list[str] = []

    for sid in _REQUIRED_FOR_REVIEW:
        current = design.workflow.current_result(sid)
        if current is None:
            violations.append(f"Required stage {sid!r} has no CURRENT result.")
            checks.append(f"required_current:{sid}=FAIL")
        else:
            checks.append(f"required_current:{sid}=PASS")

    # Graph dependency: if a stage is CURRENT, its dependencies should not be STALE.
    for sid, node in design.workflow.graph.nodes.items():
        current = design.workflow.current_result(sid)
        if current is None:
            continue
        for dep in node.dependencies:
            dep_stored = design.workflow.results.get(dep)
            if dep_stored is None:
                continue
            if dep_stored.status is ResultStatus.STALE:
                violations.append(
                    f"Stage {sid!r} is CURRENT while dependency {dep!r} is STALE."
                )
                checks.append(f"stale_dependency:{sid}->{dep}=FAIL")
            elif dep_stored.status is ResultStatus.CURRENT:
                checks.append(f"stale_dependency:{sid}->{dep}=PASS")

    # Mixture ratio continuity when both are present.
    req_mr = design.requirements.mixture_ratio
    prop_mr = design.propellant_configuration.mixture_ratio
    if req_mr is not None and prop_mr is not None:
        if abs(float(req_mr) - float(prop_mr)) > 1e-9:
            violations.append(
                f"mixture_ratio mismatch: requirements={req_mr} propellants={prop_mr}."
            )
            checks.append("mixture_ratio_match=FAIL")
        else:
            checks.append("mixture_ratio_match=PASS")

    # Structure hoop/yield advisory (if computed).
    struct = design.workflow.current_result("structure")
    if struct is not None and "hoop_over_yield" in struct.outputs:
        raw = struct.outputs["hoop_over_yield"]
        ratio = float(raw["value"] if isinstance(raw, dict) else raw)
        if ratio > 1.0:
            violations.append(
                f"hoop_over_yield {ratio} > 1.0 (thin-wall stress exceeds yield)."
            )
            checks.append("hoop_over_yield_le_1=FAIL")
        else:
            checks.append("hoop_over_yield_le_1=PASS")
            if ratio > 0.8:
                warnings.append(
                    f"hoop_over_yield {ratio} is high for a preliminary thin-wall check."
                )

    # Honest inventory of unavailable capabilities.
    for sid in ("cycle", "injector", "cooling"):
        stored = design.workflow.results.get(sid)
        if stored is not None and stored.status is ResultStatus.NOT_IMPLEMENTED:
            warnings.append(f"{sid} remains NOT_IMPLEMENTED.")
            checks.append(f"capability:{sid}=NOT_IMPLEMENTED")

    ok = len(violations) == 0
    status = ResultStatus.CURRENT if ok else ResultStatus.FAILED
    validity = ValidityInfo(
        status=ValidityState.VALID if ok else ValidityState.OUT_OF_RANGE,
        checks=tuple(checks),
        violations=tuple(violations),
    )

    result = make_result(
        calculation_type="workflow.consistency",
        stage_id=stage_id,
        status=status,
        model_id="systems.consistency",
        model_version="0.1",
        inputs={"required_stages": list(_REQUIRED_FOR_REVIEW)},
        outputs={
            "consistent": ok,
            "check_count": len(checks),
            "violation_count": len(violations),
            "checks": checks,
            "violations": violations,
        },
        warnings=tuple(warnings),
        validity=validity,
        verification=VerificationInfo(
            status="PASS" if ok else "FAIL",
            reference="Systems consistency rules (no experimental validation).",
        ),
        source="systems.stages.consistency",
        design_revision=design.revision,
    )
    design.store_stage_result(stage_id, result)
    return result
