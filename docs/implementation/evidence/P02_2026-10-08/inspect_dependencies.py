"""Record exact official source revisions, package metadata and native link closure."""
import argparse
import hashlib
import json
import platform
import struct
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent


def command(*args):
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    return {"exitCode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(root):
    projects = [
        ("PicoGK", "PicoGK", "PicoGK-v2.2.0", "Apache-2.0", ["LICENSE", "PicoGK.csproj", "Internals/Config.cs", "IO/MeshIo.cs", "Library/Library.cs", "Base/GlobalObjects.cs"]),
        ("PicoGKRuntime", "PicoGKRuntime", "PicoGK-v2.2.0", "Apache-2.0", ["LICENSE", "CMakeLists.txt", ".gitmodules", "Source/PicoGKVdbVoxels.h", "Source/PicoGKMesh.h", "Install_Dependencies/Mac.sh"]),
        ("LEAP71_ShapeKernel", "LEAP71_ShapeKernel", "ShapeKernel-v2.1.0", "Apache-2.0", ["LICENSE", "README.md", "ShapeKernel/BaseShapes/BaseSphere.cs", "ShapeKernel/BaseShapes/BaseBox.cs"]),
        ("OpenVDB", "PicoGKRuntime/openvdb", "runtime gitlink (13.0.0 source)", "Apache-2.0", ["LICENSE", "RE-LICENSE_NOTE.txt", "CMakeLists.txt", "openvdb/openvdb/LICENSE"]),
        ("GLFW", "PicoGKRuntime/GLFW", "runtime gitlink", "Zlib", ["LICENSE.md", "CMakeLists.txt"]),
        ("Dear ImGui", "PicoGKRuntime/imgui", "runtime gitlink", "MIT", ["LICENSE.txt", "backends/imgui_impl_opengl3_loader.h"]),
        ("oneTBB", "oneTBB", "v2022.2.0", "Apache-2.0", ["LICENSE.txt", "CMakeLists.txt"]),
    ]
    sources = []
    for name, relative, tag, license_id, files in projects:
        path = root / relative
        sha = command("git", "-C", str(path), "rev-parse", "HEAD")["stdout"].strip()
        url = command("git", "-C", str(path), "remote", "get-url", "origin")["stdout"].strip()
        sources.append({"name": name, "sourceDirectory": str(path), "repository": url, "pinLabel": tag,
            "commit": sha, "licenseAtPin": license_id,
            "workingTreeAfterBuild": command("git", "-C", str(path), "status", "--short"),
            "inspectedFiles": [{"path": f, "sha256": digest(path / f)} for f in files]})
    packages = []
    for nuspec in sorted((root / "nuget").glob("*/*/*.nuspec")):
        tree = ET.parse(nuspec)
        # NuGet XML namespace is package-specific; inspect local element names.
        values = {node.tag.split("}")[-1]: node.text for node in tree.iter()
            if node.tag.split("}")[-1] in ("id", "version", "license", "licenseUrl", "projectUrl")}
        folder = nuspec.parent
        licenses = [{"file": str(f.relative_to(root)), "sha256": digest(f)}
            for f in folder.glob("*LICENSE*")]
        archives = [{"file": str(f.relative_to(root)), "sha256": digest(f)} for f in folder.glob("*.nupkg")]
        packages.append({**values, "nuspecSha256": digest(nuspec), "licenseFiles": licenses,
            "sourceRepository": next((node.attrib for node in tree.iter()
                if node.tag.split("}")[-1] == "repository"), {}),
            "archives": archives, "upstreamHash": next(folder.glob("*.nupkg.sha512")).read_text().strip()})
    native = []
    for group, paths in [
        ("upstream-prebuilt", (root / "PicoGK/native/osx-arm64").glob("*.dylib")),
        ("source-built", [root / "source-worker/picogk.26.2.dylib", root / "native-deps/lib/libtbb.12.16.dylib",
            root / "native-deps/lib/libtbbmalloc.2.16.dylib"]),
    ]:
        for path in paths:
            native.append({"group": group, "path": str(path), "sha256": digest(path),
                "bytes": path.stat().st_size, "format": command("file", str(path)),
                "linkedLibraries": command("otool", "-L", str(path)),
                "loadCommands": command("otool", "-l", str(path)),
                "signature": command("codesign", "-dv", "--verbose=2", str(path))})
    sdk_tar = root / "dotnet-sdk-9.0.318-osx-arm64.tar.gz"
    expected_sdk = "4305c929005f47a933f33c253b6f47f8b21fd6096c7e359e78495e0de7c8ed1c6700aec2785a983d76ac7c99a66b1422abedb4056259b00e748ffbe36f243532"
    sdk_hash = hashlib.sha512(sdk_tar.read_bytes()).hexdigest()
    if sdk_hash != expected_sdk:
        raise ValueError("SDK archive checksum mismatch")
    font = root / "PicoGK/assets/Jost.ttf"
    font_data = font.read_bytes()
    names = []
    for index in range(struct.unpack_from(">H", font_data, 4)[0]):
        tag, _, offset, _ = struct.unpack_from(">4sIII", font_data, 12 + index * 16)
        if tag == b"name":
            _, count, storage = struct.unpack_from(">HHH", font_data, offset)
            for record in range(count):
                pid, _encoding, _language, name_id, size, relative = struct.unpack_from(">HHHHHH", font_data, offset + 6 + record * 12)
                if name_id in (0, 1, 8, 9, 13, 14):
                    raw = font_data[offset + storage + relative:offset + storage + relative + size]
                    names.append({"nameId": name_id, "value": raw.decode("utf-16-be" if pid in (0, 3) else "mac_roman", errors="replace")})
    build_tools = []
    for name, version in (("cmake", "3.31.6"), ("ninja", "1.11.1.4")):
        folder = next((root / "build-tools/lib").glob(f"python*/site-packages/{name}-{version}.dist-info"))
        build_tools.append({"name": name, "version": version, "metadataSha256": digest(folder / "METADATA"),
            "recordSha256": digest(folder / "RECORD"),
            "licenseFiles": [{"file": str(f.relative_to(root)), "sha256": digest(f)}
                for f in sorted((folder / "licenses").glob("LICENSE*"))],
            "downloadArchiveHash": "NOT_CAPTURED; installed metadata and record hashes retained"})
    result = {
        "date": "2026-10-08", "scope": "Isolated P02 feasibility; not a release SBOM",
        "baselineHead": "293223ebef190eaa647e67dc581eb186b2b5d987", "scratch": str(root),
        "platform": {"architecture": platform.machine(), "macOS": platform.mac_ver()[0],
            "ramBytes": command("sysctl", "-n", "hw.memsize")["stdout"].strip()},
        "sdk": {"version": "9.0.318", "runtimeVersion": "9.0.20", "sha512": sdk_hash,
            "checksumVerified": True, "metadata": "https://dotnetcli.blob.core.windows.net/dotnet/release-metadata/9.0/releases.json",
            "archive": "https://builds.dotnet.microsoft.com/dotnet/Sdk/9.0.318/dotnet-sdk-9.0.318-osx-arm64.tar.gz",
            "licenseSha256": digest(root / "dotnet9/LICENSE.txt"),
            "thirdPartyNoticesSha256": digest(root / "dotnet9/ThirdPartyNotices.txt")},
        "tools": {"cmake": "3.31.6", "ninja": "1.11.1.4", "oneTBB": "2022.2.0",
            "clang": command("clang", "--version"), "dotnetInfo": command(str(root / "dotnet9/dotnet"), "--info")},
        "sourcePins": sources, "nugetPackages": packages, "nativeArtifacts": native,
        "buildToolPackages": build_tools,
        "embeddedAssets": {"font": {"path": "PicoGK/assets/Jost.ttf", "sha256": digest(font), "nameTable": names},
            "environment": {"path": "PicoGK/assets/ViewerEnvironment.zip", "sha256": digest(root / "PicoGK/assets/ViewerEnvironment.zip"),
                "provenance": "Repository license recorded; asset-specific provenance not independently established."}},
        "nativeConfiguration": {"mode": "Release, osx-arm64, C++20, one build job",
            "openvdbStatic": True, "glfwStatic": True, "tbbDynamic": True,
            "openvdbDelayedLoading": False, "blosc": False, "imathHalf": False,
            "submoduleRemoteUpdate": False, "cxxHeaderPath": "/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include/c++/v1"},
        "distributionBlockers": [
            "Upstream prebuilt Boost/ICU/lzma/zstd exact source revisions and notice closure are not provided by the managed source manifest.",
            "Native Skia transitive notices need a complete release-level SBOM; no rendering path was exercised.",
            "Local native rpath references the temporary dependency prefix; relocation, signing and notarization are unverified.",
            "Upstream prebuilt minOS is 26.5; locally compiled minOS is 26.0. Older macOS compatibility is unverified.",
            "The embedded Jost font declares SIL OFL-1.1, not Apache-2.0; font notices and environment asset provenance need release review."
        ]
    }
    (HERE / "dependency_manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"sourcePins": len(sources), "nugetPackages": len(packages),
        "nativeArtifacts": len(native), "sdkChecksumVerified": True}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("scratch", type=Path)
    collect(parser.parse_args().scratch.resolve())
