"""Compare the current bounded component implementation to the preceding source inventory."""
import json
import subprocess
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"docs/implementation/evidence/R07_COMPONENTS_2026-10-20"
PREVIOUS=ROOT/"docs/implementation/evidence/R07_NATIVE_INTEGRATION_2026-10-20"
DECLARED={"systems/geometry/qa.py","systems/geometry/service.py","infrastructure/persistence/durable_jobs.py","api/nozzle_geometry.py","api/project_authority.py","api/context_projects.py","gui/server.py","gui/static/projects.js","gui/static/workbench/native-geometry.html"}


def main():
    previous_file=PREVIOUS/"source-final.json";old=json.loads(previous_file.read_bytes())["sha256"]
    current={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for d in ("core","physics","numerics","knowledge","systems","api","gui","infrastructure","simulation","validation","plugins","tests") for p in sorted((ROOT/d).rglob("*")) if p.is_file() and p.suffix in {".py",".js",".cjs",".ts",".css",".html"}}
    changed=sorted(k for k in old if k in current and current[k]!=old[k]);missing=sorted(set(old)-set(current));unexpected=sorted(set(changed)-DECLARED)
    report={"preceding_manifest_sha256":sha256(previous_file.read_bytes()).hexdigest(),"preceding_sources":len(old),"unchanged":len(old)-len(changed)-len(missing),"declared_edits":changed,"unexpected":unexpected,"missing":missing,"new_sources":sorted(set(current)-set(old)),"old_core_physics_numerics_changed":[k for k in changed if k.startswith(("core/","physics/","numerics/"))],"pass":not unexpected and not missing}
    xml=ET.parse(EVIDENCE/"full-python-verified.xml").getroot();counts={k:sum(int(s.attrib.get(k,0)) for s in xml.iter("testsuite")) for k in ("tests","failures","errors","skipped")};counts["passed"]=counts["tests"]-sum(counts[k] for k in ("failures","errors","skipped"))
    cases={(t.attrib["classname"],t.attrib["name"]) for t in xml.iter("testcase")};prior={(t.attrib["classname"],t.attrib["name"]) for t in ET.parse(PREVIOUS/"full-python-verified.xml").getroot().iter("testcase")}
    (EVIDENCE/"source-final.json").write_text(json.dumps({"head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"scope":"Dirty local bounded component/editor/study-setup software, NOT remote CI/release/physical acceptance","sha256":current},indent=2)+"\n")
    (EVIDENCE/"preservation.json").write_text(json.dumps(report,indent=2)+"\n")
    (EVIDENCE/"test-summary.json").write_text(json.dumps({"python":counts,"new_cases":len(cases-prior),"preceding_cases_missing":sorted(prior-cases),"skip_reasons":sorted({s.attrib.get("message","") for s in xml.iter("skipped")}),"skips_are_not_passes":True},indent=2)+"\n")
    print("Preservation:",report["unchanged"],"unchanged;",len(changed),"declared edits;",len(unexpected),"unexpected;",len(missing),"missing.",counts)
    if not report["pass"] or prior-cases or counts["failures"] or counts["errors"]: raise SystemExit(1)


if __name__=="__main__": main()
