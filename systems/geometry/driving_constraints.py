"""Deterministic, unit-aware directed dimensional constraints; no expression eval.

This extends the existing feature model, not a free-form sketch/assembly solver.
Rules remain in the source specification; resolved dimensions enter the frozen
DesignSnapshot/GeometryFeatureGraph pipeline and normal build verification.
"""
from __future__ import annotations

import copy
import math

from systems.contracts.geometry._wire import digest, require

SCHEMA = "cosmos.component-driving-constraints.v1"


def resolve(specification):
    require(type(specification) is dict, "DRIVING_INPUT", "Component specification required")
    spec = copy.deepcopy(specification)
    block = spec.get("constraints", {"schema": SCHEMA, "rules": []})
    require(type(block) is dict and set(block) == {"schema", "rules"} and block["schema"] == SCHEMA,
            "DRIVING_FIELDS", "Versioned explicit driving constraints required")
    rules = block["rules"]
    require(type(rules) is list and len(rules) <= 64, "DRIVING_CAPACITY", "At most64 directed constraints")
    features = {v["id"]: v for v in spec.get("features", [])}
    frames = {v["id"]: v for v in spec.get("frames", [])}

    def reference(raw):
        require(type(raw) is dict, "DRIVING_REFERENCE", "Typed dimensional reference required")
        if set(raw) == {"feature", "parameter"}:
            require(raw["feature"] in features and raw["parameter"] in features[raw["feature"]]["parameters"],
                    "DRIVING_REFERENCE", "Unknown feature/parameter; constraints never detach on rename")
            return ("parameter", raw["feature"], raw["parameter"])
        require(set(raw) == {"frame", "axis"} and raw["frame"] in frames and raw["frame"] != "world" and raw["axis"] in "xyz" and len(raw["axis"]) == 1,
                "DRIVING_REFERENCE", "Explicit non-world frame local-origin axis required")
        return ("origin", raw["frame"], raw["axis"])

    def quantity(key):
        return features[key[1]]["parameters"][key[2]] if key[0] == "parameter" else frames[key[1]]["origin"]["xyz".index(key[2])]

    def checked(q, unit):
        require(type(q) is dict and set(q) == {"value", "unit"} and q["unit"] == unit and type(q["value"]) in (int, float) and math.isfinite(q["value"]),
                "DRIVING_UNIT", "Finite explicit matching SI unit required; no guessed conversion")
        return float(q["value"])

    by_target, identifiers = {}, set()
    for rule in rules:
        require(type(rule) is dict and type(rule.get("id")) is str and 0 < len(rule["id"]) <= 80 and rule["id"] not in identifiers,
                "DRIVING_ID", "Unique bounded constraint IDs required")
        identifiers.add(rule["id"])
        kind = rule.get("type")
        expected = {"id", "type", "target", "value"} if kind in {"fixed", "diameter"} else {"id", "type", "target", "source", "factor", "offset"}
        require(kind in {"fixed", "diameter", "affine"} and set(rule) == expected, "DRIVING_FIELDS", "Supported fixed, diameter or affine rule with exact fields required")
        target = reference(rule["target"])
        require(target not in by_target, "DRIVING_OVERCONSTRAINED", "A dimension may have only one driver, even if duplicate rules agree")
        unit = quantity(target)["unit"]
        require(unit in {"m", "rad", "1"}, "DRIVING_UNIT", "Canonical dimensional/angle/count unit required")
        if kind == "diameter":
            name = target[2]
            require(target[0] == "parameter" and unit == "m" and ("radius" in name or name.startswith(("inner", "outer")) and name[5:].isdigit()),
                    "DRIVING_DIAMETER", "Diameter may drive only an explicit radial parameter")
        if kind in {"fixed", "diameter"}:
            checked(rule["value"], unit)
        else:
            source = reference(rule["source"])
            require(quantity(source)["unit"] == unit and type(rule["factor"]) in (int, float) and math.isfinite(rule["factor"]),
                    "DRIVING_UNIT", "Affine source and target units must match; finite dimensionless factor required")
            if target[0] == source[0] == "origin":
                require(frames[target[1]]["parent"] == frames[source[1]]["parent"], "DRIVING_FRAME", "Origin links require a common parent frame; no implicit world/local conversion")
            checked(rule["offset"], unit)
        by_target[target] = rule

    visiting, done, changes = set(), set(), []

    def evaluate(target):
        if target in done or target not in by_target:
            return
        require(target not in visiting, "DRIVING_CYCLE", "Cyclic driving constraints; no iterative guessing or silently dropped equations")
        visiting.add(target)
        rule = by_target[target]; q = quantity(target); unit = q["unit"]
        if rule["type"] == "affine":
            source = reference(rule["source"]); evaluate(source)
            value = checked(quantity(source), unit) * rule["factor"] + checked(rule["offset"], unit)
        else:
            value = checked(rule["value"], unit) / (2 if rule["type"] == "diameter" else 1)
        require(math.isfinite(value), "DRIVING_RANGE", "Constraint arithmetic overflow")
        if unit == "1":
            require(value.is_integer(), "DRIVING_INTEGER", "Count/flag dimensions must resolve to exact integers; no rounding")
        before = copy.deepcopy(q); q["value"] = value
        changes.append({"constraint_id": rule["id"], "target": rule["target"], "before": before, "resolved": copy.deepcopy(q)})
        visiting.remove(target); done.add(target)

    for target in by_target:
        evaluate(target)
    return {"specification": spec, "report": {"schema": SCHEMA, "rule_count": len(rules), "constraint_sha256": digest(block),
            "resolved": changes, "method": "DIRECTED_UNIT_AWARE_AFFINE_DIMENSIONS", "scope": "Fixed dimensions, diameter-to-radius and affine equality/offset/ratio links, including same-parent local origin axes. Not a general nonlinear sketch/assembly constraint solver."}}
