"""Run an isolated, source-pinned material comparison; never install live inputs.

Prescribed boundary conditions below are software research fixtures, NOT
calculated engine gas/coolant states. Unknown source process details remain
unknown. No NIST aged LPBF IN718 conductivity curve is invented to fill a gap.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from typing import TypedDict

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.exceptions import OutOfRangeError
from physics.si import UNIT_HTC
from systems.materials.research import (
    SCOPE,
    ConductivityEvidence,
    MaterialCondition,
    WallResearchInputs,
    research_wall,
    stage_conductivity,
)

SOURCE_SHA = "f542b2a0b829a0d6e10c9b1d47bef78d464df92659181d84530990e5e255c229"
TRANSCRIPTION_SHA = "7df4b72366ed8241a8f889ba539a2b9a27c4f953c0bcfb631ae12ca89c809d62"
EVIDENCE_IDS = {"LINDE-CU42-2024-REPORTED-MEAN-K", "LINDE-CU42-2024-REPORTED-MEAN-MINUS-3SIGMA-K"}
IMPLEMENTATION_FILES = (
    "scripts/prepare_material_research.py", "systems/materials/research.py",
    "physics/heat_transfer/temperature_wall.py", "physics/quantities.py", "physics/si.py",
    "core/quantity.py", "core/unit.py", "core/dimension.py", "core/validation.py",
    "numerics/integration/trapezoidal.py", "numerics/interpolation/linear.py",
    "numerics/root_finding/bisection.py", "numerics/utilities/tolerances.py",
)


class StudyCase(TypedDict):
    case_id: str
    gas_k: float
    coolant_k: float
    hg: float
    hc: float
    expected: str


def independent_conduction(evidence: ConductivityEvidence, cold: float, hot: float) -> float:
    """Independent piecewise-linear Fourier integral; no curve evaluation calls."""
    ts, ks = evidence.curve.temperatures_k, evidence.curve.conductivities_w_m_k
    total = 0.0
    for ta, tb, ka, kb in zip(ts[:-1], ts[1:], ks[:-1], ks[1:], strict=True):
        a, b = max(ta, cold), min(tb, hot)
        if b > a:
            slope = (kb - ka) / (tb - ta)
            total += (b - a) * (ka + slope * ((a + b) / 2 - ta))
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-pdf", type=Path, required=True)
    parser.add_argument("--transcriptions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.source_pdf.read_bytes()
    if sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError("Exact visually inspected source PDF required; no silently updated datasheet")
    transcription_bytes = args.transcriptions.read_bytes()
    if sha256(transcription_bytes).hexdigest() != TRANSCRIPTION_SHA:
        raise ValueError("Exact inspected original-unit transcription required; changes need a new review")
    payloads = json.loads(transcription_bytes)
    if (type(payloads) is not list or len(payloads) != 2
            or {p.get("evidence_id") for p in payloads if type(p) is dict} != EVIDENCE_IDS):
        raise ValueError("Both separate manually inspected supplier statistics required")
    records = [stage_conductivity(p, raw) for p in payloads]
    # No engine/machine selection is implied by the user's process-family research approval.
    requested = MaterialCondition("GRCop-42", "LPBF", None, None, "HIP; exact candidate schedule not selected", None)
    cases: list[StudyCase] = [
        {"case_id": "warm-wall-A", "gas_k": 900., "coolant_k": 300., "hg": 2000., "hc": 10000., "expected": "RESEARCH_RESULT"},
        {"case_id": "warm-wall-B", "gas_k": 1200., "coolant_k": 350., "hg": 5000., "hc": 8000., "expected": "RESEARCH_RESULT"},
        {"case_id": "cryogenic-wall-outside-table", "gas_k": 900., "coolant_k": 111.15, "hg": 2000., "hc": 20000., "expected": "OUT_OF_DOMAIN"},
        {"case_id": "hot-wall-outside-table", "gas_k": 3000., "coolant_k": 350., "hg": 20000., "hc": 4000., "expected": "OUT_OF_DOMAIN"},
    ]
    out = args.output.resolve()
    out.mkdir(mode=0o700, parents=True, exist_ok=False)

    def save(name: str, value: object) -> None:
        with (out / name).open("x") as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write("\n")

    declaration = {"scope": SCOPE, "requested_condition": asdict(requested), "cases": cases,
        "area_m2_each": .01, "thickness_m": .0015, "residual_tolerance_w": 1e-6,
        "boundary_basis": "PRESCRIBED_SOFTWARE_FIXTURES_NOT_ENGINE_STATES",
        "comparison_interpretation": "Separate reported statistics; NOT probability/uncertainty propagation or design bounds",
        "installation_authorized": False, "manufacturing_authorized": False, "r08": "HOLD"}
    repository = Path(__file__).resolve().parents[1]
    implementation = {name: sha256((repository / name).read_bytes()).hexdigest() for name in IMPLEMENTATION_FILES}
    save("implementation-manifest.json", {"sha256": implementation, "python_version": sys.version,
        "scope": "Selected implementation identities; not full environment qualification or release authority"})
    save("predeclared-study.json", declaration)
    with (out / "source.pdf").open("xb") as stream:
        stream.write(raw)
    with (out / "original-transcriptions.json").open("xb") as stream:
        stream.write(transcription_bytes)
    save("staged-records.json", [asdict(r) for r in records])
    save("source-manifest.json", {"source_pdf_sha256": SOURCE_SHA,
        "original_transcriptions_sha256": sha256(transcription_bytes).hexdigest(),
        "records": [{"id": r.evidence_id, "transcription_sha256": r.transcription_sha256} for r in records]})
    rows = []
    for record in records:
        for case in cases:
            inputs = WallResearchInputs(Quantity(case["gas_k"], SI.get("K")), Quantity(case["coolant_k"], SI.get("K")),
                Quantity(case["hg"], UNIT_HTC), Quantity(case["hc"], UNIT_HTC),
                Quantity(.01, SI.get("m2")), Quantity(.01, SI.get("m2")), Quantity(.01, SI.get("m2")),
                Quantity(.0015, SI.get("m")), Quantity(1e-6, SI.get("W")), 120)
            # Incomplete identity MUST reject exact-condition admission, regardless of numerical feasibility.
            try:
                research_wall(evidence=record, requested=requested, mode="EXACT_CONDITION_RESEARCH", inputs=inputs)
            except InvalidInputError:
                exact_rejected = True
            else:
                exact_rejected = False
            try:
                result = research_wall(evidence=record, requested=requested,
                    mode="UNMATCHED_SAME_ALLOY_COMPARISON", inputs=inputs)
            except OutOfRangeError as error:
                rows.append({"evidence_id": record.evidence_id, "case_id": case["case_id"],
                    "status": "OUT_OF_DOMAIN", "reason": str(error), "exact_condition_rejected": exact_rejected,
                    "check_pass": case["expected"] == "OUT_OF_DOMAIN" and exact_rejected})
                continue
            wall = result.balance
            residual = .01 / .0015 * independent_conduction(record, wall.cold_wall_temperature_k, wall.hot_wall_temperature_k) - wall.heat_w
            finite_residuals = [residual, wall.conduction_residual_w, wall.gas_residual_w, wall.coolant_residual_w]
            passed = (case["expected"] == "RESEARCH_RESULT" and exact_rejected
                and all(math.isfinite(v) and abs(v) <= 1e-6 for v in finite_residuals))
            rows.append({"evidence_id": record.evidence_id, "case_id": case["case_id"], "status": "RESEARCH_RESULT",
                "result": asdict(result), "independent_conduction_residual_w": residual,
                "exact_condition_rejected": exact_rejected, "check_pass": passed})
    report = {"scope": SCOPE, "software_checks_pass": all(r["check_pass"] for r in rows), "checks": rows,
        "installed": False, "material_allowable_assessed": False, "engine_complete": False,
        "physical_validation": "NOT_PERFORMED", "r08": "HOLD",
        "in718_status": "No matching k(T) curve for approved conventional LPBF postprocessing staged; no generic/wrought substitution"}
    save("research-checks.json", report)
    print(json.dumps({"software_checks_pass": report["software_checks_pass"], "cases": len(rows),
        "research_results": sum(r["status"] == "RESEARCH_RESULT" for r in rows),
        "expected_domain_rejections": sum(r["status"] == "OUT_OF_DOMAIN" for r in rows),
        "installed": False, "engine_complete": False}))
    if not report["software_checks_pass"]:
        raise ValueError("Predeclared research check failed; retained output must not be called accepted")


if __name__ == "__main__":
    main()
