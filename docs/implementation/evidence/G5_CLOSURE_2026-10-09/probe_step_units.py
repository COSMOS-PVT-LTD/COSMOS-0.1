"""Developer diagnostic, fixed synthetic geometry and explicit new output directory."""
import json
import sys
from pathlib import Path

from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.BRepPrimAPI import BRepPrimAPI_MakeSphere
from OCP.gp import gp_Pnt
from OCP.Interface import Interface_Static
from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer

directory = Path(sys.argv[1]); assert directory.is_absolute() and directory.is_dir()
shape = BRepAlgoAPI_Fuse(BRepPrimAPI_MakeSphere(gp_Pnt(0, 0, 0), 10).Shape(), BRepPrimAPI_MakeSphere(gp_Pnt(10, 0, 0), 10).Shape()).Shape()
Interface_Static.SetCVal_s("write.step.unit", "M")
for mode in ("before-construction", "model-write-unit"):
    writer = STEPControl_Writer()
    if mode == "model-write-unit":
        writer.Model().SetWriteLengthUnit(1000)
    assert not (directory / (mode + ".step")).exists()
    writer.Transfer(shape, STEPControl_AsIs); writer.Write(str(directory / (mode + ".step")))
    print(json.dumps({"mode": mode, "model_write_unit": writer.Model().WriteLengthUnit()}))
