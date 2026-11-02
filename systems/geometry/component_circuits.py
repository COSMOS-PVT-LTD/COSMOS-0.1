"""Explicit source-bound geometric circuit assignment, NOT a flow/seal solve."""
from systems.contracts.geometry._wire import require


def assess_circuits(plan, inspection, fuel_boundary, oxidizer_boundary):
    ports={p["id"]:p for p in inspection["ports"]}
    open_ends={p["port_id"] for p in inspection["unconnected_ports"]}
    require(type(fuel_boundary) is str and type(oxidizer_boundary) is str and fuel_boundary!=oxidizer_boundary
            and all(p in open_ends and ports[p]["kind"]=="PIPE_END" for p in (fuel_boundary,oxidizer_boundary)),
            "CIRCUIT_BOUNDARY","Choose two distinct actual unconnected pipe ends as explicit fuel/oxidizer boundaries")
    graph={key:set() for key in ports}
    def connect(a,b):
        require(a in graph and b in graph,"CIRCUIT_SOURCE","Internal passage endpoints must belong to exact saved source")
        graph[a].add(b);graph[b].add(a)
    for match in inspection["matches"]:connect(match["from"],match["to"])
    for pipe in inspection["pipe_paths"]:connect(pipe["end_a"],pipe["end_b"])
    for part in plan.parts:
        own=[p for p in ports.values() if p["part_id"]==part.part_id]
        for fluid in ("fuel","oxidizer"):
            inlet=[p["id"] for p in own if p["kind"]=="MANIFOLD_INLET" and p["fluid"]==fluid]
            outlet=[p["id"] for p in own if p["kind"]=="MANIFOLD_OUTLET" and p["fluid"]==fluid]
            if inlet or outlet:
                require(len(inlet)==1 and bool(outlet),"CIRCUIT_SOURCE","One segregated plenum inlet and actual outlet array required")
                for key in outlet:connect(inlet[0],key)
        supply=[p["id"] for p in own if p["kind"]=="COOLING_HEADER_SUPPLY"]
        channels=[p["id"] for p in own if p["kind"]=="COOLING_HEADER_CHANNEL"]
        if supply or channels:
            require(len(supply)==1 and bool(channels),"CIRCUIT_SOURCE","One real header supply and channel array required")
            for key in channels:connect(supply[0],key)
        if part.cooling:
            for index in range(part.cooling.count):
                prefix=part.part_id+".channel-"+str(index)+"-"
                connect(prefix+"upper_collector_connection",prefix+"nozzle_inlet_connection")
        for index,hole in enumerate(part.holes):
            if hole.role in {"fuel","oxidizer"} and hole.axial_range is None:
                prefix=part.part_id+".port-"+str(index)
                connect(prefix+"-inlet",prefix+"-discharge")
    def reachable(start,blocked=None):
        seen=set(); pending=[start]
        while pending:
            key=pending.pop()
            if key==blocked or key in seen:continue
            seen.add(key);pending.extend(graph[key]-seen)
        return seen
    reached={"fuel":reachable(fuel_boundary),"oxidizer":reachable(oxidizer_boundary)}
    sinks={fluid:{p["id"] for p in ports.values() if p["kind"]=="INJECTOR_DISCHARGE" and p["fluid"]==fluid}
        for fluid in ("fuel","oxidizer")}
    issues=[];cuts=[]
    if reached["fuel"]&reached["oxidizer"]:issues.append("FUEL_OXIDIZER_CROSS_CONNECTION")
    for fluid,reachable_ports in reached.items():
        if not sinks[fluid] or not sinks[fluid]<=reachable_ports:issues.append(fluid.upper()+"_INJECTOR_ARRAY_NOT_REACHED")
        wrong={p["id"] for p in ports.values() if p["fluid"] in {"fuel","oxidizer"} and p["fluid"]!=fluid}
        if wrong&reachable_ports:issues.append(fluid.upper()+"_REACHES_WRONG_PROPELLANT_OPENINGS")
    coolant={p["id"] for p in ports.values() if p["fluid"]=="COOLANT_UNASSIGNED"}
    if not coolant or not coolant<=reached["fuel"]:issues.append("COMPLETE_REGENERATIVE_ROUTE_NOT_REACHED_BY_FUEL")
    if coolant&reached["oxidizer"]:issues.append("OXIDIZER_REACHES_COOLING_CIRCUIT")
    if open_ends!={fuel_boundary,oxidizer_boundary}:issues.append("UNCONNECTED_INTERNAL_ENDS")
    unassigned=set(ports)-reached["fuel"]-reached["oxidizer"]
    if unassigned:issues.append("UNASSIGNED_PORTS")
    # Each real supply/return header and the segregated fuel-head inlet must be
    # a geometric cut vertex. A bypass cannot be hidden by simple reachability.
    required=[p["id"] for p in ports.values() if p["kind"]=="COOLING_HEADER_SUPPLY"
        or (p["kind"]=="MANIFOLD_INLET" and p["fluid"]=="fuel")]
    if len([p for p in ports.values() if p["kind"]=="COOLING_HEADER_SUPPLY"])!=2:
        issues.append("EXACT_INLET_AND_COLLECTOR_HEADER_PAIR_REQUIRED")
    def header_for_channel_end(kind):
        headers=set()
        for key,p in ports.items():
            if p["kind"]!=kind:continue
            for adjacent in graph[key]:
                if ports[adjacent]["kind"]!="COOLING_HEADER_CHANNEL":continue
                headers.update(v["id"] for v in ports.values() if v["part_id"]==ports[adjacent]["part_id"] and v["kind"]=="COOLING_HEADER_SUPPLY")
        return headers
    lower,upper=header_for_channel_end("NOZZLE_INLET_CONNECTION"),header_for_channel_end("UPPER_COLLECTOR_CONNECTION")
    if len(lower)!=1 or len(upper)!=1 or lower==upper:
        issues.append("HEADER_LOCATION_MAPPING_NOT_UNIQUE")
    else:
        inlet,collector=next(iter(lower)),next(iter(upper))
        if collector in reachable(fuel_boundary,blocked=inlet) or inlet not in reachable(fuel_boundary,blocked=collector):
            issues.append("FUEL_ROUTE_NOT_NOZZLE_TO_UPPER_COLLECTOR")
    for key in required:
        separates=not bool(sinks["fuel"]&reachable(fuel_boundary,blocked=key))
        cuts.append({"port_id":key,"separates_fuel_boundary_from_injectors":separates})
        if not separates:issues.append("REGENERATIVE_OR_INJECTOR_ROUTE_BYPASS")
    return {"schema":"cosmos.component-geometric-circuits.v1","topology_complete":not issues,
        "source_boundaries":{"fuel":fuel_boundary,"oxidizer":oxidizer_boundary},
        "assigned_ports":{key:sorted(value) for key,value in reached.items()},"unassigned_ports":sorted(unassigned),
        "required_cut_vertices":cuts,"issues":sorted(set(issues)),
        "pressure_closure":"NOT_CALCULATED","flow_distribution":"NOT_CALCULATED","seals":"NOT_ASSESSED",
        "physical_validation":"NOT_PERFORMED","scope":"Explicit requested fuel-through-regeneration / direct-oxidizer geometric topology only; bidirectional graph is not solved flow direction, pressure, phase, leakage or complete engine acceptance"}
