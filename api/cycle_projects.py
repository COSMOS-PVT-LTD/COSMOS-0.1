"""Authenticated selected-cycle history and exact source/residual exports."""

from __future__ import annotations

import csv
import io
from typing import Any

from api.pressure_fed_projects import PressureFedAPI
from systems.cycle.coupled import GG_UNITS, INPUT_SCHEMA, STREAM_UNITS


class CycleAssessmentAPI(PressureFedAPI):
    filename_prefix = "coupled-cycle"

    def handle(
        self,
        actor: Any,
        method: str,
        project: str,
        parts: list[str],
        query: dict[str, list[str]],
        body: dict[str, Any],
    ) -> Any:
        if len(parts) == 2 and parts[1] == "plots" and method == "GET":
            value = super().handle(actor, method, project, parts[:1], query, body)
            if not isinstance(value, dict):
                raise TypeError(
                    "Expected exact assessment envelope, not a binary source."
                )
            return plots(value)
        if parts == ["capabilities"] and method == "GET" and not query:
            # Membership is checked at the enclosing ProjectAPI boundary.
            return {
                "ok": True,
                "schema": INPUT_SCHEMA,
                "cycles": ["PRESSURE_FED", "GAS_GENERATOR"],
                "stream_units": STREAM_UNITS,
                "gg_units": GG_UNITS,
                "scope": "Steady prescribed-component design point; actual injector and optional full-core-fuel series cooling; imposed externally conditioned fuel film. No map/speed/combustion-feedback or hardware validation.",
                "execution": "Bounded direct affine solve outside SQL; original input capture precedes evaluation; no background-job claim.",
            }
        return super().handle(actor, method, project, parts, query, body)

    def csv(self, value: dict[str, Any]) -> bytes:
        out = io.StringIO(newline="")
        fields = [
            "name",
            "value",
            "unit",
            "tolerance",
            "passed",
            "project_id",
            "commit_id",
            "content_sha256",
            "baseline_commit_id",
            "capture_commit_id",
            "upstream_current",
            "physical_validation",
        ]
        writer = csv.DictWriter(out, fields)
        writer.writeheader()
        record = value["record"]
        for row in record["evaluation"]["result"]["outputs"]["residuals"]:
            writer.writerow(
                {
                    **row,
                    "project_id": value["authority"]["project_id"],
                    "commit_id": value["authority"]["commit_id"],
                    "content_sha256": value["authority"]["head"]["content_hash"],
                    "baseline_commit_id": record["baseline_commit_id"],
                    "capture_commit_id": record["capture_commit_id"],
                    "upstream_current": value["upstream_current"],
                    "physical_validation": "NOT_PERFORMED",
                }
            )
        return out.getvalue().encode()


def plots(value: dict[str, Any]) -> dict[str, Any]:
    from systems.visualization.plots import _plot

    record = value["record"]
    if not value["upstream_current"] or record["status"] != "COMPLETED":
        return {
            "plots": [],
            "unavailable": [
                "Historical/method-stale or failed assessment; inspect exact original records instead."
            ],
        }
    result = record["evaluation"]["result"]
    source = {
        "domain": "coupled-cycle-assessment",
        "project_id": value["authority"]["project_id"],
        "commit_id": value["authority"]["commit_id"],
        "baseline_commit_id": record["baseline_commit_id"],
        "content_sha256": value["authority"]["head"]["content_hash"],
        "model_id": result["model_id"],
        "method_sources": record["method_sources"],
        "status": record["status"],
        "freshness": "current",
        "verification": result["verification"]["status"],
        "validation": "NOT_PERFORMED",
        "assumptions": result["assumptions"],
        "warnings": result["warnings"],
        "source_canonical_json": value["source_canonical_json"],
    }
    rows = [
        {
            "index": i,
            "name": row["name"],
            "raw_value": row["value"],
            "raw_unit": row["unit"],
            "raw_tolerance": row["tolerance"],
            "normalized": row["value"] / row["tolerance"],
            "upper": 1.0,
            "lower": -1.0,
        }
        for i, row in enumerate(result["outputs"]["residuals"])
    ]
    plot = _plot(
        "cycle-residuals",
        "Signed balance residual / declared tolerance",
        rows,
        ("index", "Discrete ledger row index", "1"),
        [
            ("normalized", "Signed normalized residual"),
            ("upper", "Upper acceptance bound"),
            ("lower", "Lower acceptance bound"),
        ],
        "1",
        source,
        [
            "Linear axes. Independent discrete balance rows, not iteration history or a physical trajectory. Connecting lines are display guides only.",
            "Index/name/raw SI residual/tolerance are retained in the source table and original residual CSV.",
            "Declared algebraic tolerances are not measurement uncertainty or hardware acceptance.",
        ],
    )
    return {"plots": [plot], "unavailable": []}
