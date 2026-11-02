"""Immutable SI study and fixture-only geometry/mesh handoff contracts."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from systems.contracts.geometry import (
    GeometryArtifact,
    MappingStatus,
    NamedSelection,
    Representation,
)
from systems.contracts.geometry._wire import WireContract, require, sha


@dataclass(frozen=True, slots=True)
class StudySettings(WireContract):
    conductivity_w_m_k: float = 10.
    generation_w_m3: float = 1e6
    surface_k: float = 300.
    cells: int = 16
    relative_residual: float = 1e-8
    max_iterations: int = 10_000

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        require(.1 <= self.conductivity_w_m_k <= 1000 and 1 <= self.generation_w_m3 <= 1e7 and 1 <= self.surface_k <= 2000,
                "INVALID_MATERIAL", "Explicit positive finite SI material/source/boundary ranges required")
        require(self.cells in {8, 16, 32, 64} and 1 <= self.max_iterations <= 50_000 and 1e-10 <= self.relative_residual <= 1e-4,
                "INVALID_SOLVER", "Bounded declared mesh/iteration/residual settings required")


@dataclass(frozen=True, slots=True)
class FixtureHandoff(WireContract):
    artifact: GeometryArtifact
    selection: NamedSelection
    integrity_sha256: str
    radius_m: float
    frame_id: str
    geometry_snapshot_id: str
    scope: str = "software-sphere-radial-benchmark-only"

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        sha(self.integrity_sha256, "integrity_sha256")
        require(self.scope == "software-sphere-radial-benchmark-only" and self.radius_m == .01 and self.frame_id == "world",
                "UNQUALIFIED_HANDOFF", "Only centered 10mm sphere in the qualified SI world frame is supported")
        require(self.artifact.units == "m" and self.artifact.backend_id == "occt" and self.artifact.output_format.value == "step"
                and self.artifact.representation is Representation.ANALYTIC_BREP and self.artifact.frame_id == self.frame_id
                and self.artifact.snapshot_id == self.geometry_snapshot_id, "INVALID_HANDOFF", "Exact independently accepted analytic sphere STEP required")
        require(self.selection.mapping_status is MappingStatus.EXACT and self.selection.semantic_id == "outer-surface"
                and self.selection.geometry_revision_id == self.artifact.geometry_revision_id
                and self.selection.feature_ref == "body" and self.selection.entity_refs == ("radial-outer-shell",),
                "UNRESOLVED_SELECTION", "Explicit exact semantic selection and geometry revision required")


@dataclass(frozen=True, slots=True)
class StudySnapshot(WireContract):
    handoff: FixtureHandoff
    settings: StudySettings
    model: str = "steady-spherical-conduction-v1"
    solver_sha256: str = field(default_factory=lambda: hashlib.sha256((Path(__file__).resolve().parents[1] / "numerics/finite_volume/radial_diffusion.py").read_bytes()).hexdigest())
    model_sha256: str = field(default_factory=lambda: hashlib.sha256((Path(__file__).resolve().parents[1] / "physics/heat_transfer/spherical_conduction.py").read_bytes()).hexdigest())

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        sha(self.solver_sha256, "solver_sha256")
        sha(self.model_sha256, "model_sha256")
        require(self.model == "steady-spherical-conduction-v1", "UNSUPPORTED_MODEL", "No CFD/FEA or engine thermal model is qualified")
