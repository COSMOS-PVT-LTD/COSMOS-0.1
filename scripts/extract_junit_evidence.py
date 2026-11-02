"""Select exact executed testcases from an intact JUnit report (no rerun/renaming)."""
import argparse
import copy
from hashlib import sha256
from pathlib import Path
import xml.etree.ElementTree as ET


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True);p.add_argument("--class-prefix",required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();source=a.input.resolve();raw=source.read_bytes();tree=ET.fromstring(raw)
    cases=[copy.deepcopy(t) for t in tree.iter("testcase") if t.get("classname","").startswith(a.class_prefix)]
    if not cases or a.output.exists():raise ValueError("Nonempty exact selection and NEW report path required")
    counts={k:sum(t.find(k[:-1] if k in {"errors","failures"} else k) is not None for t in cases) for k in ("errors","failures","skipped")}
    suite=ET.Element("testsuite",name="Exact testcase extraction",tests=str(len(cases)),time=str(sum(float(t.get("time",0)) for t in cases)),**{k:str(v) for k,v in counts.items()})
    properties=ET.SubElement(suite,"properties")
    for k,v in (("source_report",str(source)),("source_report_sha256",sha256(raw).hexdigest()),("class_prefix",a.class_prefix),("extraction_scope","Copied executed testcases, not new executions; counts are not additive to parent report")):
        ET.SubElement(properties,"property",name=k,value=v)
    suite.extend(cases);a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("xb") as f:ET.ElementTree(suite).write(f,encoding="utf-8",xml_declaration=True)
    print({"tests":len(cases),**counts,"output":str(a.output)})


if __name__=="__main__":main()
