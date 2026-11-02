"""Dormant P06 data contracts. Importing this package does not enable NGG."""
from ._wire import SCHEMA_VERSION, GeometryContractError
from .artifacts import (
    Disposition,
    GeometryArtifact,
    GeometryBuildRequest,
    GeometryCheck,
    GeometryValidationReport,
    MappingStatus,
    NamedSelection,
    OutputFormat,
)
from .build import BuildState, GeometryBuildEvent, GeometryBuildRecord
from .graph import (
    DependencyImpact,
    GeometryFeature,
    GeometryFeatureGraph,
    Representation,
)
from .snapshot import CoordinateFrame, DesignSnapshot, SIParameter, SourceReference

__all__ = (
    "SCHEMA_VERSION", "BuildState", "CoordinateFrame", "DependencyImpact", "DesignSnapshot",
    "Disposition", "GeometryArtifact", "GeometryBuildEvent", "GeometryBuildRecord",
    "GeometryBuildRequest", "GeometryCheck", "GeometryContractError", "GeometryFeature",
    "GeometryFeatureGraph", "GeometryValidationReport", "MappingStatus", "NamedSelection",
    "OutputFormat", "Representation", "SIParameter", "SourceReference",
)
