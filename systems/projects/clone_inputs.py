"""Clone editable inputs only; immutable origin archive retains all evidence."""
from __future__ import annotations

import json

from systems.persistence.project_repository import RecordPayload
from systems.projects.models import DERIVED_SLOT_BY_STAGE, PropulsionDesign


def clone_input(domain: str, schema: str, namespace: str, raw: bytes, new_id: str) -> tuple[RecordPayload, int] | None:
    if domain == "propulsion" and schema == "cosmos.propulsion-design.v1":
        design = PropulsionDesign.from_canonical_dict(json.loads(raw))
        old_id = design.design_id
        design.design_id, design.revision, design.change_log = new_id, 0, []
        design.bump_revision("project_clone", old_id, new_id)
        design.created_at = design.updated_at
        for stage in design.workflow.graph.nodes:
            design.workflow.invalidate_from(stage, include_root=True)
        design.stamp_derived_slots_stale(tuple(DERIVED_SLOT_BY_STAGE))
        return RecordPayload.from_design(design), design.revision
    if domain == "geometry-fixture" and schema == "cosmos.geometry-fixture-input.v1":
        return RecordPayload(raw, schema, namespace), 0
    return None
