"""Issue a NEW local PicoGK component software receipt from executed evidence."""
import argparse
from hashlib import sha256
import json
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

from api.pico_component_runtime import SCHEMA,configuration
from plugins.geometry.pico_components import VERSION,POLICY
from systems.geometry.pico_component_builds import methods


def report(path,minimum):
    path=path.resolve();root=ET.parse(path).getroot();suites=[root] if root.tag=="testsuite" else root.findall("testsuite")
    totals={key:sum(int(s.get(key,"0")) for s in suites) for key in ("tests","failures","errors","skipped")}
    if totals["tests"]<minimum or any(totals[k] for k in ("failures","errors","skipped")):raise ValueError("Insufficient executed unskipped passing evidence: "+str(path))
    return {**totals,"path":str(path),"sha256":sha256(path.read_bytes()).hexdigest()}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("runtime-root","unit","native","http","preview","preview-python","output"):p.add_argument("--"+key,type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[1];runtime=a.runtime_root.resolve();out=a.output.resolve()
    if repo/".runtime-picogk" not in runtime.parents or out.exists():raise ValueError("Persistent private runtime and NEW qualification directory required; no resealing")
    reports={k:report(getattr(a,k),n) for k,n in (("unit",10),("native",10),("http",3),("preview",5))}
    preview_case=ET.parse(a.preview).find(".//testcase[@name='test_actual_16_part_engine_display_under_process_budget']")
    if preview_case is None or preview_case.find("properties/property[@name='actual_engine_display']") is None:
        raise ValueError("Executed actual-engine supervised display evidence required; small fixtures alone are insufficient")
    restoration=runtime/"restoration-provenance.json";original=json.loads(restoration.read_bytes())
    if original["managed_source"]!="7b30d22f7b550175962e478f626384cd7ab15411":raise ValueError("Wrong managed source basis")
    sources={str(repo/n):v for n,v in methods().items()};hashes=dict(sources)
    python=a.preview_python.absolute()
    if python!=repo/".venv-cad-inspection/bin/python":raise ValueError("Explicit existing private CAD interpreter required for display-only VTK reduction")
    packages=json.loads(subprocess.check_output([str(python),"-c","import importlib.metadata as m,json;print(json.dumps({k:{'version':m.version(k),'root':str(m.distribution(k).locate_file('vtkmodules' if k=='vtk' else k))} for k in ('vtk','numpy')}))"],timeout=15))
    if packages["vtk"]["version"]!="9.3.1":raise ValueError("Display reducer requires pinned VTK9.3.1")
    files=[runtime/"dotnet9/dotnet",restoration,*[f for f in (runtime/"worker").iterdir() if f.is_file()]]
    files.extend((python.resolve(),repo/".venv-cad-inspection/pyvenv.cfg"))
    for package in packages.values():
        files.extend(f for f in Path(package["root"]).rglob("*") if f.is_file() and f.suffix in {".py",".so",".dylib"} and not {"__pycache__","tests","test"}&set(f.parts))
    for directory in (runtime/"dotnet9/shared/Microsoft.NETCore.App/9.0.20",runtime/"dotnet9/host/fxr/9.0.20"):
        if not directory.is_dir():raise ValueError("Missing pinned .NET runtime closure")
        files.extend(f for f in directory.rglob("*") if f.is_file())
    for f in files:
        if f.is_symlink():raise ValueError("Runtime qualification refuses symlink ambiguity")
        hashes[str(f)]=sha256(f.read_bytes()).hexdigest()
    cfg={"schema":SCHEMA,"qualification":"local-software-research-only","production_enabled":False,"policy":POLICY,"version":VERSION,
        "worker":{"argv":[str(runtime/"dotnet9/dotnet"),str(runtime/"worker/PicoComponents.dll")],"environment":{"DOTNET_ROOT":str(runtime/"dotnet9"),"DOTNET_CLI_TELEMETRY_OPTOUT":"1"}},
        "preview_worker":{"argv":[str(python),str(repo/"plugins/geometry/workers/pico_preview_worker.py")],"environment":{"PYTHONPATH":str(repo),"OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1"}},"sha256":hashes}
    proof={"schema":SCHEMA,"software_qa_pass":True,"physical_validation":"NOT_PERFORMED","manufacturing_acceptance":"NOT_PERFORMED","method_sources":sources,"runtime_hashes":hashes,"reports":reports,
        "preview_packages":packages,"scope":"Local PicoGK named fields and independently checked meshes, separately checked topology-preserving display reduction; not generic fixture G5, analytic STEP, manufacturing or physical approval"}
    out.mkdir(parents=True);receipt=out/"software-receipt.json"
    with receipt.open("x") as f:json.dump(proof,f,indent=2)
    cfg.update(receipt=str(receipt),receipt_sha256=sha256(receipt.read_bytes()).hexdigest());manifest=out/"runtime.json"
    with manifest.open("x") as f:json.dump(cfg,f,indent=2)
    configuration(manifest);print("Qualified local PicoGK components:",manifest,"; no owner root/runtime switched")


if __name__=="__main__":main()
