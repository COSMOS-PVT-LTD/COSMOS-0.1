"""Explicit manufactured software fixtures; not engine manufacturing defaults."""

from systems.geometry.component_model import (
    IDENTITY,
    SCHEMA,
    compile_model,
    profile_parameters,
)


def model(kind="profile.wall",*,fluids=True):
    q=lambda v,u="m":{"value":v,"unit":u}
    profile=((0.,.02,.024),(.03,.02,.024),(.05,.01,.014),(.055,.01,.014),(.08,.015,.019))
    parameters=profile_parameters(profile)
    if kind in {"injector.showerhead","injector.doublet","injector.biprop_doublet","injector.biprop_radial_doublet","injector.triplet"}:
        parameters={"radius":q(.025),"thickness":q(.004),"ring_radius":q(.012),"count":q(3,"1"),"hole_radius":q(.0008),"phase":q(0.,"rad")}
        if kind!="injector.showerhead": parameters.update(separation=q(.006),angle=q(.2,"rad"))
        if kind in {"injector.biprop_doublet","injector.biprop_radial_doublet"}:
            parameters.pop("hole_radius")
            parameters.update(fuel_hole_radius=q(.0007),oxidizer_hole_radius=q(.0011))
    elif kind in {"pipe.circular","pipe.elbow"}:
        parameters={"bore_radius":q(.0035),"wall_thickness":q(.0012)}
        parameters.update({"bend_radius":q(.015),"angle":q(1.5707963267948966,"rad")} if kind=="pipe.elbow" else {"length":q(.04)})
    elif kind=="manifold.dual_annular":
        parameters={k:q(v) for k,v in {"radius":.025,"back_web":.003,"plenum_length":.008,"front_web":.002,
            "fuel_inner":.005,"fuel_outer":.011,"oxidizer_inner":.013,"oxidizer_outer":.021,
            "fuel_inlet_radius":.0015,"oxidizer_inlet_radius":.002,"ring_radius":.013,"separation":.010,
            "fuel_hole_radius":.0007,"oxidizer_hole_radius":.0011}.items()}
        parameters.update(count=q(3,"1"),phase=q(.1,"rad"),fuel_inlet_phase=q(.2,"rad"),oxidizer_inlet_phase=q(1.2,"rad"))
    elif kind in {"manifold.cooling_annular","manifold.cooling_front_supply"}:
        parameters={k:q(v) for k,v in {"bore_radius":.015,"outer_radius":.04,"back_web":.003,"plenum_length":.008,"front_web":.002,
            "plenum_inner":.018,"plenum_outer":.034,"port_inner":.022,"port_outer":.026,"supply_hole_radius":.003}.items()}
        parameters.update(count=q(4,"1"),width=q(.3,"rad"),phase=q(.1,"rad"),supply_phase=q(.2,"rad"))
        if kind=="manifold.cooling_front_supply":parameters.update(outer_radius=q(.06),plenum_outer=q(.05))
    elif kind=="interface.bolted_flange":
        parameters={k:q(v) for k,v in {"bore_radius":.015,"outer_radius":.035,"thickness":.004,"bolt_circle_radius":.027,"bolt_hole_radius":.002}.items()}
        parameters.update(count=q(6,"1"),phase=q(.1,"rad"))
    elif kind=="injector.coaxial":
        parameters={k:q(v) for k,v in {"length":.02,"inner_bore":.002,"inner_outer":.003,"outer_inner":.004,"outer_radius":.005}.items()}
    elif kind=="injector.pintle":
        parameters={k:q(v) for k,v in {"length":.02,"rod_radius":.001,"stem_inner":.002,"stem_outer":.003,"sleeve_inner":.004,"sleeve_outer":.005,"radial_gap":.001,"tip_length":.002,"tip_radius":.0045}.items()}
    source_operation="profile.wall" if kind=="cooling.axial_sector" else kind
    features=[{"id":"body","operation":source_operation,"frame":"world","depends_on":[],"parameters":parameters}]
    outputs=["body"]
    if kind=="cooling.axial_sector":
        features.append({"id":"channels","operation":kind,"frame":"world","depends_on":["body"],"parameters":{"count":q(4,"1"),"width":q(.3,"rad"),"hot_ligament":q(.001),"depth":q(.001),"phase":q(.1,"rad"),"fluid_domains":q(int(fluids),"1")}})
        outputs=["channels"]
    if kind=="interface.bolt_pattern":
        source=model("manifold.cooling_annular")
        source["features"][0]["parameters"]["outer_radius"]["value"]=.05
        source["features"].append({"id":"bolted-header","operation":kind,"frame":"world","depends_on":["body"],"parameters":{
            "bolt_circle_radius":q(.042),"bolt_hole_radius":q(.002),"count":q(6,"1"),"phase":q(.1,"rad")}})
        source["outputs"]=["bolted-header"]
        return source
    if kind in {"bolted-injector","grooved-bolted-injector","five-grooved-bolted-injector"}:
        source=model("injector.biprop_radial_doublet")
        source["features"][0]["parameters"]["radius"]["value"]=.045
        source["features"].append({"id":"bolted","operation":"interface.bolt_pattern","frame":"world","depends_on":["body"],
            "parameters":{"bolt_circle_radius":q(.035),"bolt_hole_radius":q(.002),"count":q(6,"1"),"phase":q(.1,"rad")}})
        source["outputs"]=["bolted"]
        if kind=="grooved-bolted-injector":
            source["features"].append({"id":"grooved","operation":"interface.face_groove","frame":"world","depends_on":["bolted"],
                "parameters":{"inner_radius":q(.025),"outer_radius":q(.028),"depth":q(.001),"face":q(-1,"1")}})
            source["outputs"]=["grooved"]
        if kind=="five-grooved-bolted-injector":
            ranges=((.003,.005,-1),(.018,.020,-1),(.022,.024,-1),(.026,.028,-1),(.030,.032,1))
            parameters={"count":q(5,"1")}
            for index,(low,high,face) in enumerate(ranges):
                parameters.update({"inner_radius"+str(index):q(low),"outer_radius"+str(index):q(high),
                    "depth"+str(index):q(.001),"face"+str(index):q(face,"1")})
            source["features"].append({"id":"five-grooves","operation":"interface.face_grooves","frame":"world",
                "depends_on":["bolted"],"parameters":parameters})
            source["outputs"]=["five-grooves"]
        return source
    if kind=="interface.face_groove":
        source=model("interface.bolted_flange")
        source["features"].append({"id":"grooved","operation":kind,"frame":"world","depends_on":["body"],
            "parameters":{"inner_radius":q(.018),"outer_radius":q(.021),"depth":q(.001),"face":q(-1,"1")}})
        source["outputs"]=["grooved"]
        return source
    return {"schema":SCHEMA,"source":"Manufactured component software qualification only; no hardware evidence","source_tolerance":q(1e-6),"export_tolerance":q(2e-5),"frames":[{"id":"world","parent":None,"origin":[q(0.)]*3,"rotation":list(IDENTITY)}],"features":features,"outputs":outputs}


def plan(kind="profile.wall",**kwargs):
    return compile_model(model(kind,**kwargs),"engine-component-synthetic-qa","synthetic-revision","2026-10-20T00:00:00+00:00")


def qa_spec():
    q=lambda v,u:{"value":v,"unit":u}
    return {"relative_volume":q(.01,"1"),"centroid":q(5e-5,"m"),"implicit_residual":q(5e-5,"m"),"reverse_distance":q(5e-5,"m"),"semantic_relative_area":q(.001,"1"),"semantic_centroid":q(1e-5,"m"),"source":"Predeclared manufactured software-only limits; not engineering tolerances"}
