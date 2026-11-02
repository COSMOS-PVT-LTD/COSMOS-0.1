"""JSON Schema shape contract generated from the authoritative Python DTOs.

Cross-object lineage/hash/frame/state/acceptance checks remain Python semantics.
No external validator dependency is imported by the application.
"""
from __future__ import annotations

import types
from dataclasses import fields
from enum import Enum
from typing import Any, Union, get_args, get_origin

from ._wire import SCHEMA_VERSION, WireContract, hints
from .artifacts import (
    GeometryArtifact,
    GeometryBuildRequest,
    GeometryCheck,
    GeometryValidationReport,
    NamedSelection,
)
from .build import GeometryBuildEvent, GeometryBuildRecord
from .graph import GeometryFeature, GeometryFeatureGraph
from .snapshot import CoordinateFrame, DesignSnapshot, SIParameter, SourceReference

CONTRACT_TYPES = (SourceReference, SIParameter, CoordinateFrame, DesignSnapshot, GeometryFeature,
                  GeometryFeatureGraph, GeometryBuildRequest, GeometryArtifact, NamedSelection,
                  GeometryCheck, GeometryValidationReport, GeometryBuildEvent, GeometryBuildRecord)
IDENTIFIER_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$"
HASH_PATTERN = r"^[0-9a-f]{64}$"


def annotation_schema(annotation: Any) -> dict[str, Any]:
    origin, args = get_origin(annotation), get_args(annotation)
    if origin in (Union, types.UnionType):
        return {"anyOf": [annotation_schema(arg) for arg in args]}
    if origin is tuple:
        return {"type": "array", "items": annotation_schema(args[0]), "maxItems": 4096, "uniqueItems": True}
    if annotation is type(None):
        return {"type": "null"}
    if annotation in (str, int, float, bool):
        return {"type": {str: "string", int: "integer", float: "number", bool: "boolean"}[annotation],
                **({"maxLength": 2048} if annotation is str else {})}
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return {"type": "string", "enum": [value.value for value in annotation]}
    if isinstance(annotation, type) and issubclass(annotation, WireContract):
        return {"$ref": "#/$defs/" + annotation.__name__}
    raise TypeError(f"Unsupported geometry schema annotation: {annotation}")


def schema_document() -> dict[str, Any]:
    definitions: dict[str, Any] = {}
    for cls in CONTRACT_TYPES:
        properties: dict[str, Any] = {
            "schema_version": {"const": SCHEMA_VERSION}, "contract_type": {"const": cls.__name__},
            "content_sha256": {"type": "string", "pattern": HASH_PATTERN},
        }
        for field in fields(cls):
            properties[field.name] = annotation_schema(hints(cls)[field.name])
            p = properties[field.name]
            if field.name.endswith("sha256") or field.name == "snapshot_id":
                p["pattern"] = HASH_PATTERN
            elif p.get("type") == "string" and (field.name.endswith("_id") or field.name in {"name", "feature_ref", "operation", "backend_version", "stage"}):
                p["pattern"] = IDENTIFIER_PATTERN
            if field.name in {"created_at", "timestamp", "generated_at"}:
                p.update(format="date-time", pattern=r"(?:Z|\+00:00)$")
            if field.name in {"source_tolerance_m", "export_tolerance_m"}:
                p["exclusiveMinimum"] = 0
            if field.name == "voxel_resolution_m":
                p["anyOf"][0]["exclusiveMinimum"] = 0
            if field.name in {"progress_fraction", "remap_confidence"}:
                p["anyOf"][0].update(minimum=0, maximum=1)
            if field.name == "seq":
                p["minimum"] = 0
            if field.name == "size_bytes":
                p["minimum"] = 1
        definitions[cls.__name__] = {"type": "object", "additionalProperties": False,
                                   "required": sorted(properties), "properties": properties}
    frame = definitions["CoordinateFrame"]["properties"]
    frame["units"] = {"const": "m"}
    frame["handedness"] = {"const": "right"}
    for name, size in [("origin_m", 3), ("rotation", 9)]:
        frame[name].update(minItems=size, maxItems=size, uniqueItems=False)
    frame["rotation"]["items"].update(minimum=-1.0000000001, maximum=1.0000000001)
    definitions["SIParameter"]["properties"]["dimension"].update(minItems=7, maxItems=7, uniqueItems=False)
    for cls_name, names in {"DesignSnapshot": ["parameters_si", "frames", "source_refs"],
                            "GeometryFeatureGraph": ["features", "output_feature_ids"],
                            "GeometryBuildRequest": ["output_formats"], "GeometryCheck": ["evidence_refs"],
                            "GeometryValidationReport": ["checks"], "GeometryBuildRecord": ["events"]}.items():
        for name in names:
            definitions[cls_name]["properties"][name]["minItems"] = 1
    definitions["DesignSnapshot"]["properties"]["frames"]["maxItems"] = 64
    definitions["GeometryFeatureGraph"]["properties"]["features"]["maxItems"] = 512
    artifact = definitions["GeometryArtifact"]["properties"]
    artifact["units"] = {"const": "m"}
    artifact["storage_uri"].update(maxLength=512, pattern=r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$",
                                    **{"not": {"pattern": r"(^|/)\.\.?(/|$)"}})
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:cosmos:ngg:contracts:1.0.0",
            "title": "COSMOS P06 geometry contracts", "description": "Shape validation only. NGG-json-v1 decoder additionally enforces checksums, SI, right-handed frames, lineage, DAG and publication guards.",
            "oneOf": [{"$ref": "#/$defs/" + cls.__name__} for cls in CONTRACT_TYPES], "$defs": definitions}
