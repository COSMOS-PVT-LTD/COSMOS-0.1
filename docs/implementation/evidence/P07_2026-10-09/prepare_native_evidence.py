"""Generate explicit local test configuration and dependency receipts, never activate app."""
import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--dotnet", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--wire-probe", type=Path, required=True)
    parser.add_argument("--run-id", default="final")
    args = parser.parse_args()
    scratch, dotnet, candidate = args.scratch.resolve(), args.dotnet.resolve(), args.candidate.resolve()
    tools = scratch / "cad-tools"
    assert tools.is_dir() and dotnet.is_file() and candidate.is_file()
    config = {"qualification": "local-software-fixtures-only", "production_enabled": False,
              "evidence_directory": str(HERE / "runs" / args.run_id), "picogk": {"argv": [str(dotnet), str(candidate)],
              "environment": {"DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_ROOT": str(dotnet.parent)}},
              "occt": {"argv": [sys.executable, "-m", "plugins.geometry.workers.occt_worker"],
                       "environment": {"PYTHONPATH": str(ROOT) + ":" + str(tools), "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}},
              "step_reader": {"argv": [sys.executable, str(ROOT / "plugins/geometry/workers/step_reader.py")],
                              "environment": {"PYTHONPATH": str(ROOT) + ":" + str(tools), "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}}}
    probe = args.wire_probe.resolve()
    config["wire_probe"] = {"argv": [str(dotnet), str(probe)], "environment": {"DOTNET_ROOT": str(dotnet.parent), "DOTNET_CLI_TELEMETRY_OPTOUT": "1"}}
    Path(config["evidence_directory"]).mkdir(parents=True, exist_ok=False)
    paths = [dotnet, candidate, *candidate.parent.glob("*.dylib"), *candidate.parent.glob("*.dll"),
             *candidate.parent.glob("*.json"), *tools.glob("OCP/*.so"), tools / "libgmsh.4.15.dylib",
             *tools.glob("OCP/.dylibs/*.dylib"), probe, *probe.parent.glob("*.json"),
             ROOT / "plugins/geometry/workers/occt_worker.py", ROOT / "plugins/geometry/workers/step_reader.py"]
    config["sha256"] = {str(p): sha(p) for p in sorted(set(paths))}
    (scratch / "native-config.json").write_text(json.dumps(config, indent=2) + "\n")
    (HERE / "native-runtime-manifest.json").write_text(json.dumps({"platform": platform.platform(),
        "python": sys.version, "config": config, "commercial_distribution_approved": False,
        "source_pins": {"PicoGK": "7b30d22f7b550175962e478f626384cd7ab15411", "PicoGKRuntime": "0f26321c18ed878a7820ef769c38fd5d49d39242"},
        "managed_patch": {"path": "plugins/geometry/workers/patches/picogk-vdb-disposal.patch",
                          "sha256": sha(ROOT / "plugins/geometry/workers/patches/picogk-vdb-disposal.patch")},
        "occt": {"ocp_wheel": "7.8.1.1.post1", "ocp_runtime": "7.8.1.1", "occt": "7.8.1", "source_to_wheel_build_commit_unverified": True},
        "gmsh": {"version": "4.15.0", "role": "external QA tool only", "application_dependency": False},
        "limitations": ["Paths are ephemeral test installations, not deployment configuration", "Python dependency wheels are test-only; app environment unchanged", "Sampled RSS is worker leader only, not aggregate peak", "No malicious-code filesystem/network sandbox", "No native redistribution/signing/relocation or other-platform acceptance"]}, indent=2) + "\n")
    report = json.loads((scratch / "cad-install.json").read_text())
    (HERE / "native-install.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = ["# macOS arm64 / CPython 3.11 local developer QA only; no application dependency.",
             "# wheel selection captured in native-install.json; all transitive wheels pinned."]
    sbom = []
    for item in report["install"]:
        metadata = item["metadata"]
        digest = item["download_info"]["archive_info"]["hashes"]["sha256"]
        lines.append(f"{metadata['name']}=={metadata['version']} --hash=sha256:{digest}")
        sbom.append({"name": metadata["name"], "version": metadata["version"], "wheel_sha256": digest,
                     "wheel_url": item["download_info"]["url"], "license_metadata": metadata.get("license_expression", metadata.get("license")),
                     "requested": item["requested"], "role": "developer isolated QA only", "redistribution_approved": False})
    (HERE / "requirements-native-tests.txt").write_text("\n".join(lines) + "\n")
    (HERE / "dependency-inventory.json").write_text(json.dumps({"schema": "cosmos.p07.developer-dependency-inventory.v1",
        "not_a_complete_distribution_sbom": True, "components": sbom}, indent=2) + "\n")
    print(json.dumps({"config": str(scratch / "native-config.json"), "runtimeHashes": len(config["sha256"]), "wheelPins": len(sbom), "applicationActivation": False}))


if __name__ == "__main__":
    main()
