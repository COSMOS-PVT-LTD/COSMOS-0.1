"""Fetch fixed official npm release files, not executable installers or UI CDNs.

Generated vendor assets are excluded from authorship edits. Keep licenses and
an integrity manifest; rerunning uses the same package versions.
"""
from __future__ import annotations

import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

PACKAGES = {
    "three": ("0.186.0", {"build/three.module.js": "three.module.js", "build/three.core.js": "three.core.js",
                          "examples/jsm/controls/OrbitControls.js": "OrbitControls.js", "LICENSE": "LICENSE"}),
    "echarts": ("6.1.0", {"dist/echarts.min.js": "echarts.min.js", "LICENSE": "LICENSE", "NOTICE": "NOTICE"}),
}


def main():
    root = Path(__file__).resolve().parents[1] / "gui/static/vendor"
    manifest = {"schema_version": 1, "source": "fixed official npm release archives", "packages": {}}
    for name, (version, files) in PACKAGES.items():
        url = f"https://registry.npmjs.org/{name}/-/{name}-{version}.tgz"
        # Use the OS curl trust store on macOS; certificate checks stay enabled.
        archive = subprocess.run(["curl", "--fail", "--silent", "--show-error", "--location",
            "--proto", "=https", "--proto-redir", "=https", "--max-time", "60",
            "--max-filesize", str(24 * 1024**2), url], check=True, capture_output=True).stdout
        if len(archive) > 24 * 1024**2:
            raise ValueError("Vendor archive exceeds limit")
        target = root / name
        target.mkdir(parents=True, exist_ok=True)
        entries = {}
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as bundle:
            for source, destination in files.items():
                member = bundle.getmember("package/" + source)
                if not member.isfile() or not 0 < member.size < 8 * 1024**2:
                    raise ValueError("Unexpected vendor member")
                stream = bundle.extractfile(member)
                assert stream is not None
                data = stream.read()
                upstream_sha256 = hashlib.sha256(data).hexdigest()
                if name == "three" and destination == "OrbitControls.js":
                    data = data.replace(b"from 'three'", b"from './three.module.js'")
                (target / destination).write_bytes(data)
                entries[destination] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                    "upstream_sha256": upstream_sha256,
                    "modification": "local relative module import" if destination == "OrbitControls.js" else "none"}
        manifest["packages"][name] = {"version": version, "url": url, "archive_sha256": hashlib.sha256(archive).hexdigest(), "files": entries}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Pinned Three.js and ECharts assets downloaded; licenses and integrity manifest saved.")


if __name__ == "__main__":
    main()
