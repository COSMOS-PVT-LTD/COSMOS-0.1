"""Geometry intent DAG; deterministic dependency-derived freshness, no kernels."""
from __future__ import annotations

import heapq
from dataclasses import dataclass
from enum import Enum

from ._wire import WireContract, digest, identifier, require, sha, unique
from .snapshot import DesignSnapshot


class Representation(str, Enum):
    ANALYTIC_BREP = "analytic_brep"
    IMPLICIT_FIELD = "implicit_field"
    TESSELLATED_SURFACE = "tessellated_surface"
    FACETED_BREP = "faceted_brep"


@dataclass(frozen=True, slots=True)
class GeometryFeature(WireContract):
    feature_id: str
    operation: str  # Intent identifier only; backend capability check belongs to P07.
    parameter_refs: tuple[str, ...]
    dependency_ids: tuple[str, ...]
    frame_id: str
    representation: Representation

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        for name in ("feature_id", "operation", "frame_id"):
            identifier(getattr(self, name), name)
        unique(self.parameter_refs, "parameter_refs", nonempty=False)
        unique(self.dependency_ids, "dependency_ids", nonempty=False)
        require(self.feature_id not in self.dependency_ids, "FEATURE_CYCLE", "Feature cannot depend on itself")
        object.__setattr__(self, "parameter_refs", tuple(sorted(self.parameter_refs)))
        object.__setattr__(self, "dependency_ids", tuple(sorted(self.dependency_ids)))


@dataclass(frozen=True, slots=True)
class DependencyImpact:
    source_snapshot_id: str
    target_snapshot_id: str
    changed_features: tuple[str, ...]
    stale_features: tuple[str, ...]

    @property
    def snapshot_is_stale(self) -> bool:
        return self.source_snapshot_id != self.target_snapshot_id


@dataclass(frozen=True, slots=True)
class GeometryFeatureGraph(WireContract):
    graph_id: str
    snapshot_id: str
    features: tuple[GeometryFeature, ...]
    output_feature_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        WireContract.__post_init__(self)
        identifier(self.graph_id, "graph_id")
        sha(self.snapshot_id, "snapshot_id")
        require(0 < len(self.features) <= 512, "CONTRACT_LIMIT", "Graph requires 1–512 features")
        unique(tuple(f.feature_id for f in self.features), "features")
        unique(self.output_feature_ids, "output_feature_ids")
        known = {f.feature_id for f in self.features}
        require(set(self.output_feature_ids) <= known, "UNKNOWN_FEATURE", "Graph output references missing feature")
        require(all(set(f.dependency_ids) <= known for f in self.features), "UNKNOWN_FEATURE", "Dependency references missing feature")
        self.topological_order()  # Prove acyclic before publishing graph intent.
        object.__setattr__(self, "features", tuple(sorted(self.features, key=lambda f: f.feature_id)))
        object.__setattr__(self, "output_feature_ids", tuple(sorted(self.output_feature_ids)))

    def topological_order(self) -> tuple[str, ...]:
        incoming = {f.feature_id: len(f.dependency_ids) for f in self.features}
        outgoing: dict[str, list[str]] = {key: [] for key in incoming}
        for feature in self.features:
            for dependency in feature.dependency_ids:
                outgoing[dependency].append(feature.feature_id)
        ready = [key for key, count in incoming.items() if count == 0]
        heapq.heapify(ready)
        result = []
        while ready:
            key = heapq.heappop(ready)
            result.append(key)
            for dependent in sorted(outgoing[key]):
                incoming[dependent] -= 1
                if incoming[dependent] == 0:
                    heapq.heappush(ready, dependent)
        require(len(result) == len(incoming), "FEATURE_CYCLE", "Feature graph contains a dependency cycle")
        return tuple(result)

    def validate_snapshot(self, snapshot: DesignSnapshot) -> None:
        require(self.snapshot_id == snapshot.snapshot_id, "STALE_SNAPSHOT", "Feature graph binds a different immutable snapshot")
        frames = {f.frame_id for f in snapshot.frames}
        parameters = {p.name for p in snapshot.parameters_si}
        for feature in self.features:
            require(feature.frame_id in frames, "UNKNOWN_FRAME", "Feature frame is undefined", feature.frame_id)
            for name in feature.parameter_refs:
                require(name in parameters, "UNKNOWN_PARAMETER", "Feature parameter is undefined", name)

    def _binding_hashes(self, snapshot: DesignSnapshot, *, allow_missing: bool = False) -> tuple[dict[str, str], dict[str, str]]:
        """Per-call reuse only; never mutate or cache an authoritative snapshot."""
        parameter_names = {p for f in self.features for p in f.parameter_refs}
        frame_names = {f.frame_id for f in self.features}
        if allow_missing:
            parameter_names &= {p.name for p in snapshot.parameters_si}
            frame_names &= {f.frame_id for f in snapshot.frames}
        return ({p: snapshot.parameter_hash(p) for p in sorted(parameter_names)},
                {f: snapshot.frame_hash(f) for f in sorted(frame_names)})

    def transitive_dependents(self, roots: tuple[str, ...]) -> tuple[str, ...]:
        known = {f.feature_id for f in self.features}
        require(set(roots) <= known, "UNKNOWN_FEATURE", "Unknown invalidation root")
        affected = set(roots)
        by_id = {f.feature_id: f for f in self.features}
        order = self.topological_order()
        for name in order:
            if set(by_id[name].dependency_ids) & affected:
                affected.add(name)
        return tuple(name for name in order if name in affected)

    def fingerprints(self, snapshot: DesignSnapshot) -> tuple[tuple[str, str], ...]:
        """Content keys for incremental reuse; never an artifact acceptance claim."""
        by_id = {f.feature_id: f for f in self.features}
        parameters, frames = self._binding_hashes(snapshot)
        result: dict[str, str] = {}
        for name in self.topological_order():
            feature = by_id[name]
            result[name] = digest({"feature": feature.to_canonical_dict(),
                                   "parameters": {p: parameters[p] for p in feature.parameter_refs},
                                   "frame": frames[feature.frame_id],
                                   "dependencies": {d: result[d] for d in feature.dependency_ids}})
        return tuple(result.items())

    def impact(self, source: DesignSnapshot, target: DesignSnapshot) -> DependencyImpact:
        self.validate_snapshot(source)
        require(source.project_id == target.project_id, "PROJECT_MISMATCH", "Cannot compare snapshots from different namespaces")
        source_parameters, source_frames = self._binding_hashes(source)
        target_parameters, target_frames = self._binding_hashes(target, allow_missing=True)
        changed = []
        by_id = {f.feature_id: f for f in self.features}
        for name in self.topological_order():
            feature = by_id[name]
            if (source_frames[feature.frame_id] != target_frames.get(feature.frame_id)
                or any(source_parameters[p] != target_parameters.get(p) for p in feature.parameter_refs)):
                changed.append(name)
        return DependencyImpact(source.snapshot_id, target.snapshot_id, tuple(changed), self.transitive_dependents(tuple(changed)))
