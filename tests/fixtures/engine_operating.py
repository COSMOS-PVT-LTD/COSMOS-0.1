"""Synthetic manufactured operating points, never owner inputs or hardware evidence."""


from physics.compressible_flow.heated_nozzle import nonadiabatic_nozzle
from physics.feed.gas_generator import Turbine
from plugins.nasa_cea.chamber import NasaHPChamber
from systems.cycle.operating_contract import SCHEMA
from systems.cycle.operating_contract import quantity as q
from tests.fixtures.coupled_cycle import design as cycle_design


def v(value, unit):
    return {"value": value, "unit": unit}


def design(cycle="PRESSURE_FED"):
    return cycle_design(cycle, cooling=True)


def specification(baseline, *, cooling=False):
    gg = baseline.cycle_configuration.cycle_type.value == "GAS_GENERATOR"
    feeds = {}
    for name in ("oxidizer", "fuel"):
        temperature = 90.17 if name == "oxidizer" else 298.15
        feeds[name] = {
            "phase": "LIQUID", "density": v(1000 if name == "oxidizer" else 800, "kg/m3"),
            "cp": v(2500,"J/kg/K"), "viscosity": v(.0005,"Pa*s"), "conductivity": v(.6,"W/m/K"),
            "temperature":v(temperature,"K"), "reference_temperature":v(temperature,"K"), "reference_pressure":v(101325,"Pa"),
            "tank_pressure":v(1e6 if gg else (7e6 if name == "oxidizer" else 9e6),"Pa"),
            "min_temperature":v(80 if name == "oxidizer" else 200,"K"), "max_temperature":v(500 if name == "oxidizer" else 1500,"K"),
            "vapour_pressure":v(1e5,"Pa"), "core_resistance":v(1,"Pa*s2/kg2"),
            "pump":None, "gg_resistance":None,
            "source":"Synthetic constant-property/map manufacture for software only; not RP1/LOX physical evidence or engineering criteria.",
        }
    chamber = NasaHPChamber(baseline.propellant_configuration.fuel_id,baseline.propellant_configuration.oxidizer_id,298.15,90.17)
    ratio, pc, speed, pg = 2.3, 5e6, 1000., 1e6
    dp = {"oxidizer":6e6,"fuel":8e6}
    work = {name:dp[name]/(feeds[name]["density"]["value"]*.7) if gg else 0 for name in feeds}
    increments = {name:(feeds[name]["tank_pressure"]["value"]-101325)/feeds[name]["density"]["value"]+work[name] for name in feeds}
    delta = (ratio*increments["oxidizer"]+increments["fuel"])/(1+ratio)
    gas = chamber.solve(q(pc,"Pa"), ratio, q(delta,"J/kg"))
    at = baseline.workflow.current_result("nozzle").outputs["throat_area_m2"]

    def mass(state, pressure, area):
        return nonadiabatic_nozzle(q(pressure,"Pa"),q(state.temperature_k,"K"),q(state.cp_j_kg_k,"J/kg/K"),q(state.gas_constant_j_kg_k,"J/kg/K"),(q(area,"m2"),q(area*2,"m2")),(q(0,"W"),)).mass_flow_kg_s

    total = mass(gas,pc,at)
    core = {"oxidizer":total*ratio/(1+ratio),"fuel":total/(1+ratio)}
    gflows = {name:0. for name in feeds}
    gas_generator = None
    if gg:
        ggas = chamber.solve(q(pg,"Pa"),ratio,q(delta,"J/kg"))
        gamma = ggas.cp_j_kg_k/(ggas.cp_j_kg_k-ggas.gas_constant_j_kg_k)
        wt,_ = Turbine(q(ggas.temperature_k,"K"),q(pg,"Pa"),q(1e5,"Pa"),q(ggas.cp_j_kg_k,"J/kg/K"),gamma,.8,.9).evaluate()
        base_power = sum(core[name]*work[name] for name in feeds)
        weighted_work = (ratio*work["oxidizer"]+work["fuel"])/(1+ratio)
        mgg = base_power/(.9*wt-weighted_work)
        gflows = {"oxidizer":mgg*ratio/(1+ratio),"fuel":mgg/(1+ratio)}
        gat = mgg/mass(ggas,pg,1.)
        gas_generator = {"throat_area":v(gat,"m2"),"exhaust_pressure":v(1e5,"Pa"),"auxiliary_power":v(0,"W"),"turbine_efficiency":.8,"shaft_efficiency":.9,"source":"Synthetic manufactured effective choked throat and constant turbine efficiencies; not a physical component map."}
    for name, feed in feeds.items():
        discharge = feed["tank_pressure"]["value"]+(dp[name] if gg else 0)
        feeds[name]["core_resistance"] = v((discharge-pc)/core[name]**2,"Pa*s2/kg2")
        if gg:
            flow = core[name]+gflows[name]
            feeds[name]["pump"] = {"speed_coefficient":v((dp[name]+1000*flow**2)/speed**2,"Pa*s2/rad2"),"flow_coefficient":v(1000,"Pa*s2/kg2"),"efficiency":.7,"speed_min":v(500,"rad/s"),"speed_max":v(1500,"rad/s"),"flow_min":v(.01,"kg/s"),"flow_max":v(10,"kg/s"),"source":"Synthetic quadratic manufacture only, no hardware map."}
            feeds[name]["gg_resistance"] = v((discharge-pg)/gflows[name]**2,"Pa*s2/kg2")
    targets = {"chamber_pressure":(pc,"Pa"),"oxidizer_flow":(core["oxidizer"],"kg/s"),"fuel_flow":(core["fuel"],"kg/s")}
    if gg:
        targets |= {"shaft_speed":(speed,"rad/s"),"gg_pressure":(pg,"Pa"),"gg_oxidizer_flow":(gflows["oxidizer"],"kg/s"),"gg_fuel_flow":(gflows["fuel"],"kg/s")}
    unknowns = {key:{"initial":v(value*.99,unit),"lower":v(value*.4,unit),"upper":v(value*1.6,unit),"scale":v(value,unit)} for key,(value,unit) in targets.items()}
    spec = {
        "schema":SCHEMA,"cycle_type":"GAS_GENERATOR" if gg else "PRESSURE_FED","regime":"STEADY_FROZEN_NOZZLE_CEA_HP",
        "feeds":feeds,"gas_generator":gas_generator,
        "cooling":{"mode":"FUEL_CORE_SERIES" if cooling else "NONE_EXPLICIT","wall_initial_temperature":v(800,"K"),"wall_temperature_tolerance":v(.001,"K"),"heat_tolerance":v(.01,"W"),"gas_min_temperature":v(100,"K"),"gas_max_temperature":v(6000,"K"),"max_iterations":100,"relaxation":.6,"source":"Synthetic broad property window for software only, not physical applicability."},
        "unknowns":unknowns,
        "solver":{"difference_step":1e-5,"residual_tolerance":.05,"max_iterations":30,"max_evaluations":500,"max_seconds":v(60,"s")},
        "tolerances":{"pressure":v(10,"Pa"),"mass_flow":v(1e-5,"kg/s"),"power":v(10,"W"),"momentum":v(1e-6,"N"),"specific_energy":v(1,"J/kg")},
    }
    return spec, {key:value for key,(value,unit) in targets.items()}
