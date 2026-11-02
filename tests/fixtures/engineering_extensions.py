"""Synthetic contracts only; no engineering defaults or hardware evidence."""

from systems.cycle.operating_contract import FEED_UNITS, SCHEMA
from systems.cycle.operating_sensitivity import SCHEMA as STUDY_SCHEMA
from systems.geometry.engine_intent import SCHEMA as INTENT_SCHEMA
from systems.geometry.engine_intent import TEMPLATE


def recipe():
    feeds = {}
    for name in ("oxidizer", "fuel"):
        values = {"density": 1000, "cp": 2500, "viscosity": .001, "conductivity": .6, "temperature": 300, "reference_temperature": 300, "reference_pressure": 1e5, "tank_pressure": 4e6, "min_temperature": 200, "max_temperature": 500, "vapour_pressure": 1e4, "core_resistance": 1e6}
        feeds[name] = {key: {"value": values[key], "unit": unit} for key, unit in FEED_UNITS.items()}
        feeds[name].update(source="Synthetic analytic test contract, not real liquid properties", phase="LIQUID", pump=None, gg_resistance=None)
    v = lambda value, unit: {"value": value, "unit": unit}
    return {"schema": SCHEMA, "cycle_type": "PRESSURE_FED", "regime": "STEADY_FROZEN_NOZZLE_CEA_HP", "feeds": feeds, "gas_generator": None,
        "unknowns": {key: {"lower": v(.1, unit), "initial": v(1., unit), "upper": v(2., unit), "scale": v(1., unit)} for key, unit in (("chamber_pressure", "Pa"), ("oxidizer_flow", "kg/s"), ("fuel_flow", "kg/s"))},
        "solver": {"max_iterations": 20, "max_evaluations": 200, "max_seconds": v(10, "s"), "difference_step": 1e-5, "residual_tolerance": .1},
        "cooling": {"mode": "NONE_EXPLICIT", "wall_initial_temperature": v(300, "K"), "wall_temperature_tolerance": v(.001, "K"), "heat_tolerance": v(.01, "W"), "gas_min_temperature": v(100, "K"), "gas_max_temperature": v(6000, "K"), "max_iterations": 20, "relaxation": .5, "source": "Synthetic thermal software test only"},
        "tolerances": {key: v(1, unit) for key, unit in (("pressure", "Pa"), ("mass_flow", "kg/s"), ("power", "W"), ("momentum", "N"), ("specific_energy", "J/kg"))}}


def sensitivity(model_recipe=None):
    model_recipe = model_recipe or recipe()
    x = model_recipe["feeds"]["fuel"]["tank_pressure"]["value"]
    h = x * .001
    return {"schema": STUDY_SCHEMA, "recipe": model_recipe, "parameter": "feeds.fuel.tank_pressure", "unit": "Pa", "values": [x - h, x, x + h], "output": "core.thrust_n", "step": {"value": h, "unit": "Pa"}, "max_seconds": {"value": 120, "unit": "s"}, "source": "Synthetic software qualification samples and step, not an uncertainty/physical applicability claim"}


def intent():
    return {"schema": INTENT_SCHEMA, "template": TEMPLATE, "frame": "THROAT_X_AXIS_RIGHT_HANDED_M", "wall_thickness": {"value": .002, "unit": "m"}, "source_tolerance": {"value": 1e-5, "unit": "m"}, "export_tolerance": {"value": 2e-5, "unit": "m"}, "wall_source": "Synthetic explicit radial wall software intent only; not structural sizing or hardware evidence"}
