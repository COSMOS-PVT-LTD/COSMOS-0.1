"""R06 sensitivity and R07 intent adapters; reuse existing managed authority."""

from __future__ import annotations

import csv
import io
from hashlib import sha256
from pathlib import Path
from typing import Any

from api.engine_operating import methods as operating_methods
from api.engine_operating_projects import OperatingSource
from api.geometry_projects import BinarySource
from api.pressure_fed_projects import PressureFedAPI
from systems.cycle.operating_sensitivity import OUTPUTS, PARAMETERS, study
from systems.cycle.operating_sensitivity import SCHEMA as STUDY_SCHEMA
from systems.geometry.engine_intent import SCHEMA as GEOMETRY_SCHEMA
from systems.geometry.engine_intent import TEMPLATE, prepare
from systems.projects.models import PropulsionDesign
from systems.visualization.plots import _plot


class GeometryIntentSource(BinarySource):
    """Unbuilt, unaccepted geometry intent, not a synthetic kernel fixture."""


def methods() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    files = (
        "api/engineering_extensions.py", "systems/cycle/operating_sensitivity.py",
        "systems/projects/operating_sensitivity.py", "systems/projects/engine_geometry.py",
        "systems/geometry/engine_intent.py", "numerics/sensitivity/local.py",
        "numerics/utilities/numerical_checks.py", "systems/projects/sensitivity.py",
    )
    return {**operating_methods(), **{name: sha256((root / name).read_bytes()).hexdigest() for name in files}}


def evaluate_sensitivity(design: PropulsionDesign, spec: dict[str, Any]) -> dict[str, Any]:
    return {"result": study(design, spec).to_canonical_dict(), "method_sources": methods()}


def evaluate_geometry(design: PropulsionDesign, spec: dict[str, Any]) -> dict[str, Any]:
    return {"result": prepare(design, spec).to_canonical_dict(), "method_sources": methods()}


class OperatingSensitivityAPI(PressureFedAPI):
    filename_prefix = "operating-sensitivity"

    def handle(self, actor: Any, method: str, project: str, parts: list[str], query: dict[str, list[str]], body: dict[str, Any]) -> Any:
        if parts == ["capabilities"] and method == "GET" and not query:
            return {"ok": True, "schema": STUDY_SCHEMA, "parameters": PARAMETERS, "outputs": OUTPUTS, "scope": "Bounded OAT and centered h/h2 sensitivity over exact PF/GG recipes, including CEA HP and selected thermal feedback. No global sensitivity/UQ/physical validation."}
        if len(parts) == 2 and parts[1] == "plots" and method == "GET":
            value = super().handle(actor, method, project, parts[:1], query, body)
            if not isinstance(value, dict):
                raise TypeError("Expected exact study envelope, not binary source.")
            return sensitivity_plots(value)
        result = super().handle(actor, method, project, parts, query, body)
        return OperatingSource(result.name, result.data, result.content_hash) if isinstance(result, BinarySource) else result

    def csv(self, value: dict[str, Any]) -> bytes:
        record, a = value["record"], value["authority"]
        spec = record["command"]["specification"]
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(["parameter", "input_unit", "value", "status", "output", "output_unit", "error", "project_id", "commit_id", "content_sha256", "baseline_commit_id", "physical_validation"])
        for row in record["evaluation"]["result"]["outputs"]["evaluations"]:
            writer.writerow([spec["parameter"], spec["unit"], row["value"], row["status"], row["output"], OUTPUTS[spec["output"]][1], row["error"]["message"] if row["error"] else "", a["project_id"], a["commit_id"], a["head"]["content_hash"], record["baseline_commit_id"], "NOT_PERFORMED"])
        return output.getvalue().encode()


class EngineGeometryAPI(PressureFedAPI):
    filename_prefix = "engine-geometry-intent"

    def handle(self, actor: Any, method: str, project: str, parts: list[str], query: dict[str, list[str]], body: dict[str, Any]) -> Any:
        if parts == ["capabilities"] and method == "GET" and not query:
            return {"ok": True, "schema": GEOMETRY_SCHEMA, "template": TEMPLATE, "scope": "CURRENT saved divergent contour to P06 SI snapshot and feature-DAG intent. Explicit radial wall and separate tolerances. Not built/QA accepted/export eligible; no native allowlist bypass."}
        if len(parts) == 2 and parts[1] == "plots" and method == "GET":
            value = super().handle(actor, method, project, parts[:1], query, body)
            if not isinstance(value, dict):
                raise TypeError("Expected exact geometry intent envelope, not binary source.")
            source = plot_source(value, "engine-geometry-intent")
            if source is None:
                return {"plots": [], "unavailable": ["Historical source/methods or failed intent; inspect original."]}
            out = value["record"]["evaluation"]["result"]["outputs"]
            return {"plots": [_plot("engine-nozzle-intent", "Saved nozzle wall profile intent", out["profile"], ("x_m", "Axial position from throat", "m"), [("inner_radius_m", "Retained inner contour"), ("outer_radius_m", "Radial-offset outer intent")], "m", source, [out["profile_approximation"], out["wall_convention"], "Not a built or accepted CAD solid."])], "unavailable": []}
        if len(parts) == 2 and parts[1] == "residuals.csv":
            from systems.projects.authority import InvalidRecord
            raise InvalidRecord("Geometry intent has no calculated residuals. Download exact record/input JSON; no fabricated CAD or metrology export.")
        result = super().handle(actor, method, project, parts, query, body)
        return GeometryIntentSource(result.name, result.data, result.content_hash) if isinstance(result, BinarySource) else result


def plot_source(value: dict[str, Any], domain: str) -> dict[str, Any] | None:
    record, a = value["record"], value["authority"]
    if not value["upstream_current"] or record["status"] != "COMPLETED":
        return None
    result = record["evaluation"]["result"]
    return {"domain": domain, "project_id": a["project_id"], "commit_id": a["commit_id"], "baseline_commit_id": record["baseline_commit_id"], "content_sha256": a["head"]["content_hash"], "model_id": result["model_id"], "method_sources": record["method_sources"], "status": "COMPLETED", "freshness": "current", "verification": "NOT_INDEPENDENTLY_ACCEPTED", "validation": "NOT_PERFORMED", "assumptions": result["assumptions"], "warnings": result["warnings"], "source_canonical_json": value["source_canonical_json"]}


def sensitivity_plots(value: dict[str, Any]) -> dict[str, Any]:
    source = plot_source(value, "operating-sensitivity")
    if source is None:
        return {"plots": [], "unavailable": ["Historical source/methods or failed execution; inspect original."]}
    record = value["record"]
    spec = record["command"]["specification"]
    out = record["evaluation"]["result"]["outputs"]
    source["status"] = out["study_status"]
    chunks: list[list[dict[str, Any]]] = [[]]
    for row in out["samples"]:
        if row["status"] == "VALID":
            chunks[-1].append({"input": row["value"], "output": row["output"]})
        else:
            chunks.append([])
    data = [_plot("operating-sensitivity-" + str(i), OUTPUTS[spec["output"]][0], rows, ("input", PARAMETERS[spec["parameter"]][0], spec["unit"]), [("output", "Independently solved response")], out["output_unit"], source, ["Linear axes. Invalid domains are gaps; no interpolation, extrapolation or physical validation."]) for i, rows in enumerate(chunks) if len(rows) >= 2]
    return {"plots": data, "unavailable": ["Isolated valid samples remain in exact source/CSV, not joined across invalid gaps."] if any(len(rows) == 1 for rows in chunks) else []}
