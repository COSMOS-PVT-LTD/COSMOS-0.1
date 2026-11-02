"""New research-only compact CSG builder. Old admitted workers stay unchanged.

Native construction uses millimetres; reports use metres. No healing, sewing,
fuzzy Boolean tolerance, face-ID transfer, material assignment or acceptance.
"""

from __future__ import annotations

import math

import numpy as np


class Builder:
    def __init__(self, plan):
        import OCP

        if OCP.__version__ != "7.8.1.1":
            raise ValueError("Separately tested OCP 7.8.1.1 required")
        self.plan = plan
        self.tolerance = next(
            p.value_si
            for p in plan.snapshot.parameters_si
            if p.name == "source_tolerance"
        )

    @staticmethod
    def entities(shape, kind):
        from OCP.TopExp import TopExp_Explorer

        explorer, values = TopExp_Explorer(shape, kind), []
        while explorer.More():
            values.append(explorer.Current())
            explorer.Next()
        return values

    @staticmethod
    def boolean(left, right, operation):
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
        from OCP.TopTools import TopTools_ListOfShape

        maker = (BRepAlgoAPI_Fuse if operation == "union" else BRepAlgoAPI_Cut)()
        arguments, tools = TopTools_ListOfShape(), TopTools_ListOfShape()
        arguments.Append(left)
        tools.Append(right)
        maker.SetArguments(arguments)
        maker.SetTools(tools)
        maker.SetNonDestructive(True)
        maker.SetRunParallel(False)
        maker.SetFuzzyValue(0.0)
        maker.Build()
        if not maker.IsDone():
            raise ValueError("Exact compact Boolean failed; no automatic repair")
        return maker.Shape()

    @staticmethod
    def transform(shape, rotation, translation):
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
        from OCP.gp import gp_Trsf

        r, t = np.asarray(rotation).reshape(3, 3), np.asarray(translation) * 1000
        tr = gp_Trsf()
        tr.SetValues(*[float(v) for row in range(3) for v in (*r[row], t[row])])
        operation = BRepBuilderAPI_Transform(shape, tr, True)
        if not operation.IsDone():
            raise ValueError("Rigid compact placement failed")
        return operation.Shape()

    def revolve(self, profile, sector=None):
        from OCP.BRepBuilderAPI import (
            BRepBuilderAPI_MakeEdge,
            BRepBuilderAPI_MakeFace,
            BRepBuilderAPI_MakeWire,
        )
        from OCP.BRepPrimAPI import BRepPrimAPI_MakeRevol
        from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt

        points = [(x, ri) for x, ri, _ in profile] + [
            (x, ro) for x, _, ro in reversed(profile)
        ]
        wire = BRepBuilderAPI_MakeWire()
        for a, b in zip(points, points[1:] + points[:1], strict=True):
            if a != b:
                wire.Add(
                    BRepBuilderAPI_MakeEdge(
                        gp_Pnt(a[0] * 1000, a[1] * 1000, 0),
                        gp_Pnt(b[0] * 1000, b[1] * 1000, 0),
                    ).Edge()
                )
        face = BRepBuilderAPI_MakeFace(wire.Wire(), True)
        if not face.IsDone():
            raise ValueError("Closed compact profile failed")
        axis = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0))
        maker = (
            BRepPrimAPI_MakeRevol(face.Face(), axis, sector[1], True)
            if sector
            else BRepPrimAPI_MakeRevol(face.Face(), axis, True)
        )
        if not maker.IsDone():
            raise ValueError("Compact profile revolution failed")
        shape = maker.Shape()
        if sector:
            angle = sector[0]
            shape = self.transform(
                shape,
                (
                    (1, 0, 0),
                    (0, math.cos(angle), -math.sin(angle)),
                    (0, math.sin(angle), math.cos(angle)),
                ),
                (0, 0, 0),
            )
        return shape

    def part(self, part):
        from OCP.BRepBuilderAPI import (
            BRepBuilderAPI_MakeEdge,
            BRepBuilderAPI_MakeFace,
            BRepBuilderAPI_MakeWire,
        )
        from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeRevol
        from OCP.gp import gp_Ax1, gp_Ax2, gp_Circ, gp_Dir, gp_Pnt
        from OCP.TopoDS import TopoDS

        pipe = part.pipe
        if pipe and pipe.bend_radius is not None:
            axis = gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0))
            rings = [
                BRepBuilderAPI_MakeWire(
                    BRepBuilderAPI_MakeEdge(gp_Circ(axis, radius * 1000)).Edge()
                ).Wire()
                for radius in (pipe.outer_radius, pipe.bore_radius)
            ]
            face = BRepBuilderAPI_MakeFace(rings[0], True)
            face.Add(TopoDS.Wire_s(rings[1].Reversed()))
            maker = BRepPrimAPI_MakeRevol(
                face.Face(),
                gp_Ax1(gp_Pnt(0, pipe.bend_radius * 1000, 0), gp_Dir(0, 0, 1)),
                pipe.angle_rad,
                True,
            )
            if not maker.IsDone():
                raise ValueError("Compact elbow failed")
            shape = maker.Shape()
        else:
            shape = self.revolve(part.profile, part.sector)
        pad = 10 * self.tolerance + 1e-8
        for cavity in part.cavities:
            rows = cavity.profile
            if cavity.open_passage:
                rows = (
                    (rows[0][0] - pad, *rows[0][1:]),
                    (rows[-1][0] + pad, *rows[-1][1:]),
                )
            elif cavity.open_face:
                rows = (
                    (
                        rows[0][0] - (pad if cavity.open_face == "start" else 0),
                        *rows[0][1:],
                    ),
                    (
                        rows[-1][0] + (pad if cavity.open_face == "end" else 0),
                        *rows[-1][1:],
                    ),
                )
            shape = self.boolean(shape, self.revolve(rows, cavity.sector), "cut")
        if part.cooling:
            c = part.cooling
            rows = tuple(
                (x, ri + c.hot_ligament, ri + c.hot_ligament + c.depth)
                for x, ri, _ in part.profile
            )
            for i in range(c.count):
                shape = self.boolean(
                    shape,
                    self.revolve(
                        rows, (c.phase_rad + 2 * math.pi * i / c.count, c.width_rad)
                    ),
                    "cut",
                )
        for hole in part.holes:
            direction = np.r_[1.0, hole.slope_yz]
            direction /= np.linalg.norm(direction)
            over = (
                pad + hole.radius * math.sqrt(max(0.0, 1 - direction[0] ** 2))
            ) / direction[0]
            begin, end = hole.axial_range or (part.profile[0][0], part.profile[-1][0])
            start = (
                np.r_[begin, np.array(hole.center_yz) + begin * np.array(hole.slope_yz)]
                - direction * over
            )
            tool = BRepPrimAPI_MakeCylinder(
                gp_Ax2(gp_Pnt(*(start * 1000)), gp_Dir(*direction)),
                hole.radius * 1000,
                ((end - begin) / direction[0] + 2 * over) * 1000,
            ).Shape()
            shape = self.boolean(shape, tool, "cut")
        r, t = self.plan.placement(part.frame_id)
        return self.transform(shape, r, t)

    @staticmethod
    def properties(shape):
        from OCP.BRepGProp import BRepGProp
        from OCP.GProp import GProp_GProps

        prop = GProp_GProps()
        BRepGProp.VolumeProperties_s(shape, prop)
        p = prop.CentreOfMass()
        return prop.Mass() * 1e-9, [p.X() * 0.001, p.Y() * 0.001, p.Z() * 0.001]

    def build(self, candidate):
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
        from OCP.BRepCheck import BRepCheck_Analyzer
        from OCP.TopAbs import TopAbs_SOLID

        if candidate.plan is not self.plan:
            raise ValueError("Exact candidate source plan required")
        references = {p["part_id"]: p for p in candidate.wire()["groups"]}
        output = []
        for group in candidate.groups:
            # Fuse by connected frontier, not alphabetical source-part order.
            operands = [self.part(p) for p in group.add]
            shape, pending = operands[0], operands[1:]
            while pending:
                for i, operand in enumerate(pending):
                    merged = self.boolean(shape, operand, "union")
                    if len(self.entities(merged, TopAbs_SOLID)) == 1:
                        shape = merged
                        pending.pop(i)
                        break
                else:
                    raise ValueError(
                        "Compact group is disconnected; do not sew/heal across gaps"
                    )
            for part in group.subtract:
                shape = self.boolean(shape, self.part(part), "cut")
            if (
                len(self.entities(shape, TopAbs_SOLID)) != 1
                or not BRepCheck_Analyzer(shape, True).IsValid()
            ):
                raise ValueError("One valid solid per compact group required")
            volume, center = self.properties(shape)
            expected = references[group.part_id]["reference_volume_m3"]
            relative = abs(volume - expected) / expected
            if volume <= 0 or relative > 1e-6:
                raise ValueError(
                    "Compact volume disagrees with independent integral; overlaps or unexpected removal are not accepted"
                )
            for _, other, _ in output:
                common = BRepAlgoAPI_Common(shape, other)
                if not common.IsDone() or self.entities(common.Shape(), TopAbs_SOLID):
                    raise ValueError(
                        "Compact output metal groups interfere; no automatic assembly correction"
                    )
            output.append(
                (
                    group.part_id,
                    shape,
                    {
                        "volume_m3": volume,
                        "centroid_m": center,
                        "relative_integral_error": relative,
                        "solid_count": 1,
                        "valid": True,
                    },
                )
            )
        return output
