"""Verify and relocate the retained source-built PicoGK runtime for local research."""
import argparse
from hashlib import sha256,sha512
import json
from pathlib import Path
import shutil
import subprocess


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--root",type=Path,required=True);a=p.parse_args()
    repo=Path(__file__).resolve().parents[1];root=a.root.resolve()
    if repo/".runtime-picogk" not in root.parents:raise ValueError("Explicit ignored private local runtime root required")
    old=json.loads((repo/"docs/implementation/evidence/R07_COMPONENTS_2026-10-20/runtime-qualified-groove-fit-v1.json").read_bytes())
    sdk=json.loads((repo/"docs/implementation/evidence/P02_2026-10-08/dependency_manifest.json").read_bytes())["sdk"]
    archive=root/"dotnet-sdk-9.0.318-osx-arm64.tar.gz"
    if sha512(archive.read_bytes()).hexdigest()!=sdk["sha512"]:raise ValueError("SDK official archive checksum mismatch")
    source=root/"PicoGK"
    pin=subprocess.check_output(["git","-C",str(source),"rev-parse","HEAD"],text=True).strip()
    if pin!="7b30d22f7b550175962e478f626384cd7ab15411":raise ValueError("PicoGK source pin mismatch")
    if list(source.rglob("AGENTS.md")):raise ValueError("Read upstream repository instructions before proceeding")
    paths={"PicoGK.dll":"/private/tmp/cosmos-r05_3-native.IcKKdc/pico-worker/PicoGK.dll",
           "picogk.26.2.dylib":"/private/tmp/cosmos-r05_3-native.IcKKdc/pico-worker/picogk.26.2.dylib",
           "libtbb.12.dylib":"/private/tmp/cosmos-r05_3-native.IcKKdc/native-deps/lib/libtbb.12.16.dylib"}
    proof={"purpose":"Local source-built native research runtime restoration, not distribution approval","managed_source":pin,"sdk_archive_sha512":sdk["sha512"],"restored":{}}
    target=root/"worker";target.mkdir(exist_ok=True)
    for name,path in paths.items():
        original=Path(path);digest=sha256(original.read_bytes()).hexdigest()
        if old["sha256"].get(path)!=digest:raise ValueError("Historical source-built byte identity mismatch: "+name)
        output=target/name
        if output.exists():raise ValueError("Refuse runtime overwrite: "+str(output))
        shutil.copy2(original,output);proof["restored"][name]={"original_path":path,"original_sha256":digest}
    dylib=target/"picogk.26.2.dylib"
    subprocess.run(["install_name_tool","-rpath","/tmp/cosmos-r05_3-native.IcKKdc/native-deps/lib","@loader_path",str(dylib)],check=True)
    subprocess.run(["codesign","--force","--sign","-",str(dylib)],check=True,capture_output=True)
    for name in paths:proof["restored"][name]["relocated_sha256"]=sha256((target/name).read_bytes()).hexdigest()
    proof["relocation"]="Changed only native LC_RPATH to @loader_path and ad-hoc signed this private copy; historical bytes unchanged"
    with (root/"restoration-provenance.json").open("x") as f:json.dump(proof,f,indent=2)
    print("Verified retained native bytes and persistent local relocation:",target)


if __name__=="__main__":main()
