"""Representation, manifest lineage, QA and revision-bound selection contracts."""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from types import MappingProxyType

from ._wire import (
    WireContract,
    identifier,
    positive,
    relative_path,
    require,
    sha,
    unique,
    utc,
)
from .graph import GeometryFeatureGraph, Representation


class OutputFormat(str, Enum):
    STEP = "step"
    STL = "stl"
    GLB = "glb"
    VDB = "vdb"


APPROXIMATION = MappingProxyType({Representation.ANALYTIC_BREP: "none", Representation.IMPLICIT_FIELD: "sparse_volume",
                                 Representation.TESSELLATED_SURFACE: "surface_mesh", Representation.FACETED_BREP: "planar_facets"})


def representation_settings(representation: Representation, profile: str, voxel: float | None) -> None:
    require(profile == APPROXIMATION[representation], "REPRESENTATION_MISMATCH", "Approximation profile must label the actual representation")
    if representation is Representation.IMPLICIT_FIELD:
        require(voxel is not None and voxel > 0, "MISSING_RESOLUTION", "Implicit field requires explicit SI voxel resolution")
    else:
        require(voxel is None, "REPRESENTATION_MISMATCH", "Voxel resolution is only valid for implicit fields")


def format_compatible(representation: Representation, output_format: OutputFormat) -> None:
    if output_format is OutputFormat.STEP:
        require(representation in {Representation.ANALYTIC_BREP, Representation.FACETED_BREP}, "UNSUPPORTED_FORMAT", "Implicit/triangle geometry cannot claim analytic STEP")
    if output_format is OutputFormat.VDB:
        require(representation is Representation.IMPLICIT_FIELD, "UNSUPPORTED_FORMAT", "VDB requires an implicit field")


@dataclass(frozen=True, slots=True)
class GeometryBuildRequest(WireContract):
    request_id: str
    snapshot_id: str
    feature_graph_id: str
    feature_graph_sha256: str
    backend_id: str
    backend_version: str
    representation: Representation
    approximation_profile: str
    source_tolerance_m: float
    export_tolerance_m: float
    voxel_resolution_m: float | None
    output_formats: tuple[OutputFormat, ...]
    frame_id: str
    correlation_id: str

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        for name in ("request_id", "feature_graph_id", "backend_id", "backend_version", "frame_id", "correlation_id"):
            identifier(getattr(self, name), name)
        for name in ("snapshot_id", "feature_graph_sha256"):
            sha(getattr(self, name), name)
        positive(self.source_tolerance_m, "source_tolerance_m")
        positive(self.export_tolerance_m, "export_tolerance_m")
        unique(tuple(f.value for f in self.output_formats), "output_formats")
        representation_settings(self.representation, self.approximation_profile, self.voxel_resolution_m)
        for output_format in self.output_formats:
            format_compatible(self.representation, output_format)
        object.__setattr__(self, "output_formats", tuple(sorted(self.output_formats, key=lambda f: f.value)))


@dataclass(frozen=True, slots=True)
class GeometryArtifact(WireContract):
    """Source representation and export-byte format remain distinct identities."""
    artifact_id: str
    job_id: str
    geometry_revision_id: str
    snapshot_id: str
    feature_graph_sha256: str
    representation: Representation
    approximation_profile: str
    backend_id: str
    backend_version: str
    units: str
    frame_id: str
    source_tolerance_m: float
    export_tolerance_m: float
    voxel_resolution_m: float | None
    source_artifact_sha256: str
    sha256: str  # Export bytes, distinct from immutable manifest content_sha256.
    output_format: OutputFormat
    storage_uri: str
    size_bytes: int
    topology_report_id: str
    generated_at: str

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        for name in ("artifact_id", "job_id", "geometry_revision_id", "backend_id", "backend_version", "frame_id", "topology_report_id"):
            identifier(getattr(self, name), name)
        for name in ("snapshot_id", "feature_graph_sha256", "source_artifact_sha256", "sha256"):
            sha(getattr(self, name), name)
        require(self.units == "m", "INVALID_UNIT", "Artifact contract coordinates must declare SI metres")
        require(self.size_bytes > 0, "INVALID_SIZE", "Artifact size must be positive")
        relative_path(self.storage_uri, "storage_uri")
        require(self.storage_uri.endswith("." + self.output_format.value), "FORMAT_MISMATCH", "Storage extension and declared format disagree")
        positive(self.source_tolerance_m, "source_tolerance_m")
        positive(self.export_tolerance_m, "export_tolerance_m")
        representation_settings(self.representation, self.approximation_profile, self.voxel_resolution_m)
        format_compatible(self.representation, self.output_format)
        object.__setattr__(self, "generated_at", utc(self.generated_at, "generated_at"))

    @property
    def export_representation(self) -> Representation:
        """STL/GLB mesh exports never inherit an analytic source's CAD label."""
        if self.output_format in {OutputFormat.STL, OutputFormat.GLB}:
            return Representation.TESSELLATED_SURFACE
        if self.output_format is OutputFormat.VDB:
            return Representation.IMPLICIT_FIELD
        return self.representation  # STEP is already restricted to labelled B-reps.

    def freshness(self, active_snapshot_id: str, active_graph_sha256: str) -> str:
        sha(active_snapshot_id, "active_snapshot_id")
        sha(active_graph_sha256, "active_graph_sha256")
        return "CURRENT" if (self.snapshot_id, self.feature_graph_sha256) == (active_snapshot_id, active_graph_sha256) else "STALE"


class MappingStatus(str, Enum):
    EXACT = "exact"
    REMAPPED = "remapped"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class NamedSelection(WireContract):
    semantic_id: str
    geometry_revision_id: str
    feature_ref: str
    entity_refs: tuple[str, ...]
    remap_confidence: float | None
    mapping_status: MappingStatus

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        for name in ("semantic_id", "geometry_revision_id", "feature_ref"):
            identifier(getattr(self, name), name)
        unique(self.entity_refs, "entity_refs", nonempty=False)
        if self.remap_confidence is not None:
            require(0 <= self.remap_confidence <= 1, "INVALID_CONFIDENCE", "Confidence must be in [0,1]")
        if self.mapping_status is MappingStatus.UNRESOLVED:
            require(not self.entity_refs and self.remap_confidence is None, "INVALID_MAPPING", "Unresolved selection cannot claim mapped entities/confidence")
        elif self.mapping_status is MappingStatus.EXACT:
            require(bool(self.entity_refs) and self.remap_confidence == 1, "INVALID_MAPPING", "Exact selection needs explicit entities and confidence 1")
        elif self.mapping_status is MappingStatus.REMAPPED:
            require(bool(self.entity_refs) and self.remap_confidence is not None and self.remap_confidence > 0,
                    "INVALID_MAPPING", "Remap requires explicit entities and positive confidence; acceptance is separate")
        else:
            require(len(self.entity_refs) >= 2, "INVALID_MAPPING", "Ambiguous mapping requires multiple candidates")
        object.__setattr__(self, "entity_refs", tuple(sorted(self.entity_refs)))

    def for_revision(self, revision: str) -> NamedSelection:
        identifier(revision, "geometry_revision_id")
        if revision == self.geometry_revision_id:
            return self
        return replace(self, geometry_revision_id=revision, entity_refs=(), remap_confidence=None, mapping_status=MappingStatus.UNRESOLVED)

    def validate_binding(self, graph: GeometryFeatureGraph, artifact: GeometryArtifact) -> None:
        require(self.geometry_revision_id == artifact.geometry_revision_id, "STALE_SELECTION", "Named selection binds a different geometry revision")
        require(self.feature_ref in {f.feature_id for f in graph.features}, "UNKNOWN_FEATURE", "Selection feature is undefined")
        require(graph.content_sha256 == artifact.feature_graph_sha256 and graph.snapshot_id == artifact.snapshot_id,
                "STALE_GRAPH", "Artifact and selection graph lineage disagree")


class Disposition(str, Enum):
    UNVERIFIED = "unverified"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class GeometryCheck(WireContract):
    """Boolean check, or nonnegative error metric with an explicit at-most limit."""
    check_id: str
    passed: bool
    observed: float | None
    limit: float | None
    unit: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        identifier(self.check_id, "check_id")
        require(bool(self.unit.strip()), "INVALID_UNIT", "QA check must state its unit or dimensionless '1'")
        unique(self.evidence_refs, "evidence_refs")
        require((self.observed is None) == (self.limit is None), "INVALID_QA_METRIC", "Numeric QA requires both observed error and at-most limit")
        if self.observed is not None and self.limit is not None:
            require(self.observed >= 0 and self.limit >= 0 and self.passed == (self.observed <= self.limit),
                    "INVALID_QA_METRIC", "QA pass flag contradicts the nonnegative error ceiling")


@dataclass(frozen=True, slots=True)
class GeometryValidationReport(WireContract):
    report_id: str
    artifact_id: str
    checks: tuple[GeometryCheck, ...]
    acceptance_policy_id: str
    reviewer_id: str | None
    disposition: Disposition

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        for name in ("report_id", "artifact_id", "acceptance_policy_id"):
            identifier(getattr(self, name), name)
        unique(tuple(c.check_id for c in self.checks), "checks")
        if self.reviewer_id is not None:
            identifier(self.reviewer_id, "reviewer_id")
        if self.disposition is Disposition.ACCEPTED:
            require(all(c.passed for c in self.checks) and self.reviewer_id is not None,
                    "QA_NOT_ACCEPTED", "Accepted QA requires all recorded checks and independent reviewer identity")
        if self.disposition is Disposition.REJECTED:
            require(not all(c.passed for c in self.checks), "QA_NOT_REJECTED", "Rejected QA requires at least one recorded failed check")
