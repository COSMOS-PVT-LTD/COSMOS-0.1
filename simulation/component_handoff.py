"""Reviewed component study setup, explicitly NOT the sphere solver or engine CFD."""

from __future__ import annotations

from dataclasses import dataclass

from systems.contracts.geometry import (
    CoordinateFrame,
    GeometryArtifact,
    MappingStatus,
    NamedSelection,
)
from systems.contracts.geometry._wire import (
    WireContract,
    identifier,
    require,
    sha,
    unique,
)


@dataclass(frozen=True,slots=True)
class ComponentMaterialRegion(WireContract):
    part_id: str
    kind: str
    material_name: str
    source: str

    def __post_init__(self):
        WireContract.__post_init__(self); identifier(self.part_id,"part_id")
        require(self.kind in {"metal","coolant-fluid-domain"} and 0<len(self.material_name.strip())<=240 and 0<len(self.source.strip())<=2048,"HANDOFF_MATERIAL","Explicit region/material/source required; geometry material label does not supply solver properties")


@dataclass(frozen=True,slots=True)
class ComponentMeshConstraints(WireContract):
    maximum_edge_m: float
    minimum_feature_m: float
    cells_across_feature: int
    curvature_tolerance_m: float
    maximum_cells: int
    source: str

    def __post_init__(self):
        WireContract.__post_init__(self)
        require(2<=self.cells_across_feature<=100 and 0<self.maximum_edge_m<=self.minimum_feature_m/self.cells_across_feature and 0<self.minimum_feature_m<1
                and 0<self.curvature_tolerance_m<self.minimum_feature_m/2 and 1<=self.maximum_cells<=5000000 and 0<len(self.source.strip())<=2048,"HANDOFF_MESH","Explicit consistent declared minimum feature/edge/curvature/cell constraints required; this does not generate or certify a volume mesh")


@dataclass(frozen=True,slots=True)
class ComponentInterface(WireContract):
    interface_id: str
    left_selection: str
    right_selection: str
    entity_pairs: tuple[str,...]
    mapping_status: str = "EXACT_REVISION_GEOMETRIC_MATCH"

    def __post_init__(self):
        WireContract.__post_init__(self)
        for key in ("interface_id","left_selection","right_selection"): identifier(getattr(self,key),key)
        unique(self.entity_pairs,"entity_pairs")
        require(self.left_selection!=self.right_selection and self.mapping_status=="EXACT_REVISION_GEOMETRIC_MATCH","HANDOFF_INTERFACE","Exact distinct revision-bound interface pairing required; no assumed thermal/contact law")


@dataclass(frozen=True,slots=True)
class ComponentHandoff(WireContract):
    artifact: GeometryArtifact
    build_job_id: str
    build_source_commit_id: str
    review_commit_id: str
    review_sha256: str
    named_selections: tuple[NamedSelection,...]
    material_regions: tuple[ComponentMaterialRegion,...]
    coordinate_frames: tuple[CoordinateFrame,...]
    interfaces: tuple[ComponentInterface,...]
    mesh_constraints: ComponentMeshConstraints
    geometry_integrity_sha256: str
    intended_use: str = "GEOMETRY_ANALYSIS_PREPARATION"

    def __post_init__(self):
        WireContract.__post_init__(self)
        for key in ("build_job_id","build_source_commit_id","review_commit_id"): identifier(getattr(self,key),key)
        for key in ("review_sha256","geometry_integrity_sha256"): sha(getattr(self,key),key)
        require(self.artifact.output_format.value=="step" and self.artifact.units=="m" and self.artifact.backend_id=="occt" and self.intended_use=="GEOMETRY_ANALYSIS_PREPARATION","UNQUALIFIED_HANDOFF","Reviewed exact analytic metre component STEP required; no implicit CFD/FEA capability")
        require(self.geometry_integrity_sha256==self.artifact.sha256,"HANDOFF_INTEGRITY","Handoff checksum must bind the exact actual STEP artifact")
        unique(tuple(s.semantic_id for s in self.named_selections),"named_selections")
        require(all(s.geometry_revision_id==self.artifact.geometry_revision_id and s.mapping_status is MappingStatus.EXACT and s.remap_confidence==1 for s in self.named_selections),"UNRESOLVED_SELECTION","Every handed-off selection must bind exact exported revision/entities; proposals cannot pass")
        unique(tuple(r.part_id for r in self.material_regions),"material_regions")
        unique(tuple(f.frame_id for f in self.coordinate_frames),"coordinate_frames")
        known={s.semantic_id for s in self.named_selections}
        require(all(i.left_selection in known and i.right_selection in known for i in self.interfaces),"UNRESOLVED_INTERFACE","Interfaces must name exact handed-off selections")


@dataclass(frozen=True,slots=True)
class ComponentStudySetup(WireContract):
    handoff: ComponentHandoff
    model: str = "geometry-preparation-only-v1"
    mesh_status: str = "NOT_GENERATED"
    execution_status: str = "NOT_STARTED"
    solver_supported: bool = False
    physical_validation: str = "NOT_PERFORMED"
    material_properties_status: str = "NOT_SPECIFIED_FOR_A_SOLVER"

    def __post_init__(self):
        WireContract.__post_init__(self)
        require((self.model,self.mesh_status,self.execution_status,self.solver_supported,self.physical_validation,self.material_properties_status)==("geometry-preparation-only-v1","NOT_GENERATED","NOT_STARTED",False,"NOT_PERFORMED","NOT_SPECIFIED_FOR_A_SOLVER"),"UNSUPPORTED_COMPONENT_STUDY","Component handoff is geometry setup only; no engine solver/mesh/result/validation may be fabricated")
