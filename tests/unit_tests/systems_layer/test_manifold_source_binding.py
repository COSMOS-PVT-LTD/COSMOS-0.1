from copy import deepcopy

import pytest

from systems.configuration.subsystems import configure_subsystems
from systems.geometry.component_authority import (
    injector_dimensions,
    validate_injector_binding,
)
from systems.projects.authority import InvalidRecord
from tests.fixtures.component_geometry import model
from tests.fixtures.coupled_cycle import design
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)


def source_model(d):
    value=model("manifold.dual_annular")
    dims,_=injector_dimensions(d)
    value["features"][0]["parameters"].update(deepcopy(dims))
    return value


def test_manifold_requires_exact_current_hydraulic_radii_and_counts():
    d=design(cooling=True); value=source_model(d)
    validate_injector_binding(d,value)
    changed=deepcopy(value);changed["features"][0]["parameters"]["fuel_hole_radius"]["value"]*=1.01
    with pytest.raises(InvalidRecord,match="hydraulic source"):validate_injector_binding(d,changed)
    cfg=deepcopy(d.subsystem_inputs["injector"]);cfg["fuel_cd"]*=.9
    configure_subsystems(d,{"injector":cfg})
    with pytest.raises(InvalidRecord,match="CURRENT injector"):validate_injector_binding(d,value)


def test_radial_pair_layout_must_match_manifold_and_tangential_mapping_rejects():
    d=design(cooling=True); value=source_model(d)
    radial=model("injector.biprop_radial_doublet")["features"][0]
    radial["id"]="plate"
    keys=("count","ring_radius","separation","phase","fuel_hole_radius","oxidizer_hole_radius")
    for key in keys:radial["parameters"][key]=deepcopy(value["features"][0]["parameters"][key])
    value["features"].append(radial)
    validate_injector_binding(d,value)
    radial["parameters"]["separation"]["value"]*=1.1
    with pytest.raises(InvalidRecord,match="matching layout"):validate_injector_binding(d,value)
    radial["operation"]="injector.biprop_doublet"
    with pytest.raises(InvalidRecord,match="Tangential"):validate_injector_binding(d,value)
