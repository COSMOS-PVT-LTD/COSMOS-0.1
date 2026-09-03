"""Export propulsion design packages (authoritative server-owned JSON)."""

from __future__ import annotations

from datetime import datetime, timezone

from core.serialization import canonical_json_dumps
from core.version import COSMOS_VERSION

from systems.contracts.results import is_current_displayable
from systems.projects.models import PropulsionDesign

__all__ = ("build_design_export_package", "export_design_json")


def build_design_export_package(design: PropulsionDesign) -> dict[str, object]:
    """
    Build an exportable engineering package.

    Includes full design serialization plus a CURRENT-only results view so
    consumers never treat STALE as the active answer.
    """

    current_results: dict[str, object] = {}
    all_results: dict[str, object] = {}
    for stage_id, result in sorted(design.workflow.results.items()):
        all_results[stage_id] = result.to_canonical_dict()
        if is_current_displayable(result.status):
            current_results[stage_id] = result.to_canonical_dict()

    return {
        "export_format": "cosmos.propulsion_design_package",
        "export_format_version": "0.1",
        "exported_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "software_version": COSMOS_VERSION,
        "design": design.to_canonical_dict(),
        "current_results": current_results,
        "all_results": all_results,
        "disclaimer": (
            "NOT flight-certified. Validation NOT_CLAIMED. "
            "Only current_results may be treated as the active engineering answer."
        ),
    }


def export_design_json(design: PropulsionDesign) -> str:
    """Canonical JSON string for download / archival."""

    return canonical_json_dumps(build_design_export_package(design))
