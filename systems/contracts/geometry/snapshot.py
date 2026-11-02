"""Immutable explicit SI input/frame/provenance contracts. No design store."""
from __future__ import annotations

import math
from dataclasses import dataclass

from core.dimension import TEMPERATURE
from core.exceptions import UnitError
from core.quantity import Quantity, QuantityKind
from core.unit import SI

from ._wire import WireContract, identifier, require, sha, source_uri, unique, utc

FRAME_ROUNDOFF_BOUND = 1e-10  # Dimensionless rotation validation, not CAD tolerance.


@dataclass(frozen=True, slots=True)
class SourceReference(WireContract):
    ref_id: str
    source_uri: str
    source_sha256: str

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        identifier(self.ref_id, "ref_id")
        source_uri(self.source_uri)
        sha(self.source_sha256, "source_sha256")


@dataclass(frozen=True, slots=True)
class SIParameter(WireContract):
    name: str
    value_si: float
    unit_symbol: str
    dimension: tuple[int, ...]
    source_ref_id: str
    kind: QuantityKind = QuantityKind.ABSOLUTE

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        identifier(self.name, "name")
        identifier(self.source_ref_id, "source_ref_id")
        try:
            unit = SI.get(self.unit_symbol)
        except UnitError as error:
            from ._wire import GeometryContractError
            raise GeometryContractError("INVALID_UNIT", str(error), "unit_symbol") from error
        require(unit.symbol == self.unit_symbol and unit.si_scale == 1 and unit.si_offset == 0,
                "NON_SI_UNIT", "Internal geometry parameters require canonical SI units; convert explicitly", "unit_symbol")
        require(self.dimension == unit.dimension.exponents, "DIMENSION_MISMATCH", "Dimension does not match the registered unit", "dimension")
        require(self.kind is not QuantityKind.INTERVAL or unit.dimension == TEMPERATURE,
                "INVALID_QUANTITY_KIND", "Interval kind is only valid for temperature", "kind")

    @classmethod
    def from_quantity(cls, name: str, value: Quantity, *, si_unit: str, source_ref_id: str) -> SIParameter:
        require(isinstance(value, Quantity), "INVALID_TYPE", "Explicit conversion requires a Core Quantity")
        try:
            target = SI.get(si_unit)
        except UnitError as error:
            from ._wire import GeometryContractError
            raise GeometryContractError("INVALID_UNIT", str(error), "si_unit") from error
        require(value.dimension().is_compatible_with(target.dimension), "DIMENSION_MISMATCH", "Source and target units differ in dimension")
        return cls(name, value.to_si(), si_unit, target.dimension.exponents, source_ref_id, value.kind)


@dataclass(frozen=True, slots=True)
class CoordinateFrame(WireContract):
    frame_id: str
    parent_frame_id: str | None
    origin_m: tuple[float, ...]
    rotation: tuple[float, ...]  # Row-major local-to-parent rotation.
    units: str = "m"
    handedness: str = "right"

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        identifier(self.frame_id, "frame_id")
        if self.parent_frame_id is not None:
            identifier(self.parent_frame_id, "parent_frame_id")
            require(self.parent_frame_id != self.frame_id, "FRAME_CYCLE", "Frame cannot parent itself")
        require(self.units == "m" and self.handedness == "right", "INVALID_FRAME", "Frame must be right-handed SI metres")
        require(len(self.origin_m) == 3 and len(self.rotation) == 9, "INVALID_FRAME", "Frame requires 3D origin and 3x3 rotation")
        r = self.rotation
        require(all(abs(v) <= 1 + FRAME_ROUNDOFF_BOUND for v in r), "INVALID_FRAME", "Rotation component exceeds unit-vector bound")
        for i in range(3):
            for j in range(3):
                dot = math.fsum(r[3 * i + k] * r[3 * j + k] for k in range(3))
                require(abs(dot - float(i == j)) <= FRAME_ROUNDOFF_BOUND, "INVALID_FRAME", "Rotation must be orthonormal")
        det = r[0] * (r[4] * r[8] - r[5] * r[7]) - r[1] * (r[3] * r[8] - r[5] * r[6]) + r[2] * (r[3] * r[7] - r[4] * r[6])
        require(abs(det - 1) <= FRAME_ROUNDOFF_BOUND, "INVALID_FRAME", "Reflections/left-handed rotations rejected")


@dataclass(frozen=True, slots=True)
class DesignSnapshot(WireContract):
    project_id: str  # Caller namespace only; does not create a Project record.
    revision_id: str
    parameters_si: tuple[SIParameter, ...]
    frames: tuple[CoordinateFrame, ...]
    frame_id: str
    source_refs: tuple[SourceReference, ...]
    created_at: str

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        identifier(self.project_id, "project_id")
        identifier(self.revision_id, "revision_id")
        unique(tuple(p.name for p in self.parameters_si), "parameters_si")
        unique(tuple(f.frame_id for f in self.frames), "frames")
        require(len(self.frames) <= 64, "CONTRACT_LIMIT", "At most 64 frames")
        unique(tuple(s.ref_id for s in self.source_refs), "source_refs")
        require(self.frame_id in {f.frame_id for f in self.frames}, "UNKNOWN_FRAME", "Snapshot frame is undefined")
        require(all(p.source_ref_id in {s.ref_id for s in self.source_refs} for p in self.parameters_si), "UNKNOWN_SOURCE", "Parameter source reference is undefined")
        parents = {f.frame_id: f.parent_frame_id for f in self.frames}
        require(sum(p is None for p in parents.values()) == 1, "INVALID_FRAME_TREE", "One explicit root frame is required")
        for name in parents:
            visited: set[str] = set()
            current: str | None = name
            while current is not None:
                require(current in parents, "UNKNOWN_FRAME", "Frame parent is undefined")
                require(current not in visited, "FRAME_CYCLE", "Coordinate frame tree contains a cycle")
                visited.add(current)
                current = parents[current]
        object.__setattr__(self, "created_at", utc(self.created_at, "created_at"))
        # Canonical ordering is semantic only; preserve every numerical value.
        object.__setattr__(self, "parameters_si", tuple(sorted(self.parameters_si, key=lambda p: p.name)))
        object.__setattr__(self, "frames", tuple(sorted(self.frames, key=lambda f: f.frame_id)))
        object.__setattr__(self, "source_refs", tuple(sorted(self.source_refs, key=lambda s: s.ref_id)))

    @property
    def snapshot_id(self) -> str:
        return self.content_sha256

    def parameter_hash(self, name: str) -> str:
        from ._wire import digest
        parameter = next((p for p in self.parameters_si if p.name == name), None)
        require(parameter is not None, "UNKNOWN_PARAMETER", "Feature references an undefined parameter", name)
        assert parameter is not None
        source = next(s for s in self.source_refs if s.ref_id == parameter.source_ref_id)
        return digest({"parameter": parameter.to_canonical_dict(), "source": source.to_canonical_dict()})

    def frame_hash(self, name: str) -> str:
        from ._wire import digest
        frames = {f.frame_id: f for f in self.frames}
        require(name in frames, "UNKNOWN_FRAME", "Feature frame is undefined", name)
        lineage = []
        current: str | None = name
        while current is not None:
            frame = frames[current]
            lineage.append(frame.to_canonical_dict())
            current = frame.parent_frame_id
        return digest({"lineage": lineage})
