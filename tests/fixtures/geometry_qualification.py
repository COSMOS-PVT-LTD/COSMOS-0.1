"""Manufactured numerical policy. NEVER an engine/hardware acceptance basis."""

import math

from systems.geometry.qualification_policy import SCHEMA


def pipe_policy(part_id="body", *, implicit=True):
    # Exact annular cylinder: x=0..0.04, radii 3.5 and 4.7 mm.
    ri, ro, length = 0.0035, 0.0047, 0.04
    area = 2 * math.pi * (ro + ri) * length + 2 * math.pi * (ro**2 - ri**2)
    return {
        "schema": SCHEMA,
        "unit_system": "SI_m",
        "intended_use": "SOFTWARE_QUALIFICATION",
        "applicability": "Manufactured pipe fixture only; not real engine/hardware acceptance",
        "reference_source": "Independent annular cylinder formulas, exact dimensions declared in tests/fixtures/component_geometry.py",
        "require_cross_representation": implicit,
        "require_certified_self_intersection": False,
        "sampling": {"samples_per_part": 32, "outlier_limit": 8},
        "refinement_resolutions_m": [0.0005, 0.00025, 0.000125] if implicit else [],
        "parts": [
            {
                "part_id": part_id,
                "relative_volume": 0.03,
                "relative_area": 0.04,
                "reference_area_m2": area,
                "area_reference_source": "2*pi*(ro+ri)*L + 2*pi*(ro^2-ri^2)",
                "centroid_m": 0.0005,
                "bounds_m": 0.0007,
                "reference_residual_m": 0.0007,
                "reverse_distance_m": 0.0007,
                "representation_distance_m": 0.0007,
                "critical_features": [
                    {
                        "id": "radial-wall-witness",
                        "kind": "WALL_SPAN",
                        "points_m": [[0.02, ri, 0], [0.02, ro, 0]],
                        "minimum_m": 0.0006,
                        "maximum_m": 0.0018,
                        "surface_tolerance_m": 0.0006,
                        "source": "Explicit synthetic radial wall endpoints; sampled span, NOT global wall minimum",
                    }
                ],
            }
        ],
        "regions": [
            {
                "part_id": part_id,
                "role": "metal",
                "material": "Synthetic region label only",
                "source": "No material property/strength approval",
            }
        ],
        "boundaries": [
            {
                "part_id": part_id,
                "semantic_id": part_id + ":all",
                "scope": "WHOLE_PART",
                "purpose": "Geometry-only fixture handoff",
                "source": "Whole retained source part; no CFD boundary inference",
            }
        ],
        "mesh_intent": {
            "maximum_edge_m": 0.0001,
            "minimum_feature_m": 0.0004,
            "cells_across_feature": 4,
            "curvature_tolerance_m": 0.00001,
            "maximum_cells": 100000,
            "source": "Synthetic mesh-intent fixture; mesh NOT_GENERATED",
        },
    }
