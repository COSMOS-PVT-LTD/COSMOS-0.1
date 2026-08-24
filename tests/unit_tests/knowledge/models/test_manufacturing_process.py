"""ManufacturingProcess required fields."""

from __future__ import annotations

import pytest

from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace
from knowledge.models.manufacturing_process import ManufacturingProcess


def test_approved_manufacturing_process_requires_applicability() -> None:
    provenance = ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1")
    with pytest.raises(ValueError, match="applicability"):
        ManufacturingProcess(
            process_id="MFG-LPBF",
            name="Laser powder bed fusion",
            description="Additive copper chamber liners",
            material_ids=("MAT-GRCOP-42",),
            provenance=provenance,
            equipment="LPBF machine",
            parameters=("laser power", "scan speed"),
            tolerances="as-designed wall thickness",
            surface_condition="as-built + HIP",
            post_processing="HIP",
            inspection="CT",
            defects=("lack of fusion",),
            lifecycle=KnowledgeLifecycle.APPROVED,
        )


def test_manufacturing_process_records_inspection_and_defects() -> None:
    process = ManufacturingProcess(
        process_id="MFG-LPBF",
        name="Laser powder bed fusion",
        description="Additive copper chamber liners",
        material_ids=("MAT-GRCOP-42",),
        provenance=ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1"),
        equipment="LPBF machine",
        parameters=("laser power",),
        inspection="CT",
        defects=("porosity",),
        applicability="copper liners",
        lifecycle=KnowledgeLifecycle.APPROVED,
    )
    assert process.equipment == "LPBF machine"
    assert process.inspection == "CT"
