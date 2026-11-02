"""Persist concise build logs, source licenses and representative raw artifacts."""
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent


def collect(scratch):
    manifest = json.loads((HERE / "dependency_manifest.json").read_text())
    copied = []

    def copy(source, target):
        target = HERE / target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append({"path": str(target.relative_to(HERE)),
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "bytes": target.stat().st_size})

    for log in scratch.glob("*.log"):
        copy(log, Path("logs") / log.name)
    for project in manifest["sourcePins"]:
        for file in project["inspectedFiles"]:
            if "LICENSE" in file["path"] or file["path"] == "RE-LICENSE_NOTE.txt":
                copy(Path(project["sourceDirectory"]) / file["path"],
                    Path("licenses") / project["name"].replace(" ", "-") / file["path"])
    for package in manifest["nugetPackages"]:
        for file in package["licenseFiles"]:
            copy(scratch / file["file"], Path("licenses") / package["id"] / Path(file["file"]).name)
    for package in manifest["buildToolPackages"]:
        for file in package["licenseFiles"]:
            copy(scratch / file["file"], Path("licenses") / package["name"] / Path(file["file"]).name)
    copy(scratch / "dotnet9/LICENSE.txt", Path("licenses") / "dotnet-sdk/LICENSE.txt")
    copy(scratch / "dotnet9/ThirdPartyNotices.txt", Path("licenses") / "dotnet-sdk/ThirdPartyNotices.txt")
    # Embedded header notices stay in their complete functional source headers.
    for file in ("imstb_truetype.h", "imstb_rectpack.h", "imstb_textedit.h", "backends/imgui_impl_opengl3_loader.h"):
        copy(scratch / "PicoGKRuntime/imgui" / file, Path("licenses") / "Dear-ImGui" / file)
    data = json.loads((HERE / "source_benchmarks.json").read_text())
    artifact_map = []
    for case in data["cases"]:
        req = case["request"]
        if case["independentQa"] and (not case["pass"] or (req["operation"] == "sphere" and req["voxelM"] == .001)):
            source = Path(case["run"]["events"][-1]["cycles"][0]["path"])
            relative = Path("artifacts") / f"source-{req['operation']}-{req['voxelM']:.6f}m.stl"
            copy(source, relative)
            artifact_map.append({"sourcePath": str(source), "persistedPath": str(relative),
                "sha256": case["independentQa"]["sha256"], "unit": "m", "frame": "right-handed-xyz",
                "status": "UNVERIFIED", "p02FixturePass": case["pass"]})
    (HERE / "artifacts/manifest.json").write_text(json.dumps(artifact_map, indent=2) + "\n")
    (HERE / "collected_evidence.json").write_text(json.dumps(copied, indent=2) + "\n")
    print(json.dumps({"persistedFiles": len(copied), "rawMeshes": len(artifact_map)}))


if __name__ == "__main__":
    import sys
    collect(Path(sys.argv[1]).resolve())
