"""New append-only component/nozzle/fixture campaign; never reseal old evidence."""
from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path

from plugins.geometry.nozzle_protocol import POLICY as NOZZLE_POLICY
from plugins.geometry.nozzle_protocol import VERSION as NOZZLE_VERSION
from systems.geometry.component_authority import methods
from systems.geometry.component_model import POLICY, VERSION
from systems.geometry.engine_builds import methods as nozzle_methods

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"docs/implementation/evidence/R07_COMPONENTS_2026-10-20"
DECLARED={"systems/geometry/service.py","systems/geometry/qa.py","api/nozzle_geometry.py","infrastructure/persistence/durable_jobs.py"}


def write_new(path,value):
    with path.open("x",encoding="utf-8") as stream: json.dump(value,stream,indent=2,allow_nan=False);stream.write("\n")


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--seal",action="store_true");parser.add_argument("--campaign",required=True);args=parser.parse_args()
    if not re.fullmatch(r"[a-z0-9-]{1,16}",args.campaign): raise ValueError("Explicit bounded new campaign suffix required")
    prepared=EVIDENCE/("runtime-prepared-"+args.campaign+".json")
    if not args.seal:
        baseline=ROOT/"docs/implementation/evidence/R07_NATIVE_INTEGRATION_2026-10-20/runtime-qualified-config-v4.json"
        cfg=json.loads(baseline.read_bytes());changes=[]
        for name,expected in list(cfg["sha256"].items()):
            path=Path(name);actual=sha256(path.read_bytes()).hexdigest()
            if actual!=expected:
                if str(path.relative_to(ROOT)) not in DECLARED: raise ValueError("Undeclared preceding native identity changed: "+name)
                cfg["sha256"][name]=actual;changes.append({"path":name,"before":expected,"after":actual})
        cfg.pop("engine_nozzle",None)
        cfg["sha256"].update({str(ROOT/name):value for name,value in {**nozzle_methods(),**methods()}.items()})
        cfg["evidence_directory"]=str(EVIDENCE/("fixture-campaign-"+args.campaign));Path(cfg["evidence_directory"]).mkdir(mode=0o700)
        write_new(prepared,cfg);write_new(EVIDENCE/("declared-runtime-changes-"+args.campaign+".json"),{"baseline_sha256":sha256(baseline.read_bytes()).hexdigest(),"changes":changes,"native_identity_count":len(cfg["sha256"]),"scope":"New software campaign; preceding receipts remain unchanged; owner root disabled"})
        print("Prepared",len(cfg["sha256"]),"explicit runtime identities; qualification still pending.");return
    cfg=json.loads(prepared.read_bytes())
    for name,expected in cfg["sha256"].items():
        if sha256(Path(name).read_bytes()).hexdigest()!=expected: raise ValueError("Prepared source changed; preserve campaign and start a new named one: "+name)
    reports={}
    for group,minimum in (("native-components",16),("component-http",6),("native-nozzle",7),("fixture-regression",31)):
        path=EVIDENCE/(group+"-"+args.campaign+".xml");xml=ET.parse(path).getroot()
        counts={key:sum(int(s.attrib.get(key,0)) for s in xml.iter("testsuite")) for key in ("tests","failures","errors","skipped")}
        if counts["tests"]<minimum or any(counts[key] for key in ("failures","errors","skipped")): raise ValueError("Executed, passing, unskipped scope required: "+group)
        reports[group]={"sha256":sha256(path.read_bytes()).hexdigest(),**counts}
    for key,policy,version,method_sources,files in (("engine_nozzle",NOZZLE_POLICY,NOZZLE_VERSION,nozzle_methods(),("nozzle_worker.py","nozzle_step_reader.py")),("engine_components",POLICY,VERSION,methods(),("component_worker.py","component_step_reader.py"))):
        receipt=EVIDENCE/(key+"-software-receipt-"+args.campaign+".json")
        write_new(receipt,{"policy":policy,"version":version,"software_qa_pass":True,"physical_validation":"NOT_PERFORMED","engineering_acceptance":"NOT_PERFORMED","production_enabled":False,"method_sources":{str(ROOT/name):value for name,value in method_sources.items()},"reports":reports,"scope":"Bounded locally qualified component / preserved nozzle software only; synthetic reviewer tests are NOT real acceptance. Study handoff is geometry preparation, not engine CFD/FEA or manufacturing release."})
        command=lambda file:{"argv":[cfg["occt"]["argv"][0],str(ROOT/"plugins/geometry/workers"/file)],"environment":cfg["occt"]["environment"]}
        cfg[key]={"policy":policy,"version":version,"worker":command(files[0]),"reader":command(files[1]),"receipt":str(receipt),"receipt_sha256":sha256(receipt.read_bytes()).hexdigest()}
    target=EVIDENCE/("runtime-qualified-"+args.campaign+".json");write_new(target,cfg)
    from api.component_geometry import runtime_configuration
    runtime_configuration(target)
    print("New exact component/nozzle software receipts accepted. Owner data/runtime not enabled or migrated.")


if __name__=="__main__": main()
