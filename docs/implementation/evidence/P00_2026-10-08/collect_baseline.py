"""Read-only P00 source inventory and isolated baseline snapshot generator.

Generated JSON/CSV are evidence, not a claim that an AST symbol is operational.
The isolated source copy keeps cache-writing tests away from user data.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
AREAS = ("core", "knowledge", "physics", "numerics", "systems", "engineering",
         "simulation", "optimization", "ai", "gui", "visualization", "databases",
         "plugins", "api", "io", "validation", "projects", "infrastructure",
         "governance", "external", "tests", "scripts", "tools")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    paths = sorted(set(git("ls-files", "-co", "--exclude-standard").splitlines()))
    paths = [p for p in paths if not p.startswith("docs/implementation/evidence/")
             and (ROOT / p).is_file()]
    hashes = {p: digest(ROOT / p) for p in paths}
    fingerprint = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    rows, edges, parse_errors = [], [], []
    counts = {}
    for area in AREAS:
        files = [p for p in paths if p.startswith(area + "/")]
        py = [p for p in files if p.endswith(".py")]
        counts[area] = {"directory_exists": (ROOT / area).is_dir(),
                        "files": len(files), "python_files": len(py)}
        for relative in py:
            source = (ROOT / relative).read_text(encoding="utf-8")
            try:
                tree = ast.parse(source)
            except SyntaxError as exc:
                parse_errors.append({"path": relative, "error": str(exc)})
                continue
            symbols = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
            state = "DEFERRED_METADATA" if 'CAPABILITY_STATE = "DEFERRED"' in source else "SOURCE_PRESENT"
            rows.append({"path": relative, "lines": len(source.splitlines()),
                         "state": state, "symbols": "; ".join(f"{n.name}:{n.lineno}-{n.end_lineno}" for n in symbols),
                         "sha256": hashes[relative]})
            for node in ast.walk(tree):
                modules = []
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    modules = [node.module]
                for module in modules:
                    edges.append({"source": relative, "line": node.lineno, "target": module})
    versions = {d.metadata["Name"]: d.version for d in importlib.metadata.distributions() if d.metadata["Name"]}
    spec = ROOT / "docs/implementation/COSMOS_0_1_MODERNIZATION_CODEX_PACK"
    manifest = json.loads((spec / "MANIFEST.json").read_text())
    entries = manifest.get("files", [])
    manifest_mismatches = [e["path"] for e in entries if digest(spec / e["path"]) != e["sha256"]]
    metadata = {"recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                "user_date": "2026-10-08", "repo_root": str(ROOT),
                "repo_sha": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
                "remote": git("remote", "get-url", "origin"),
                "remote_head": git("ls-remote", "origin", "HEAD", "refs/heads/main"),
                "git_status_before": git("status", "--short"),
                "snapshot_fingerprint_sha256": fingerprint, "snapshot_file_count": len(hashes),
                "python": sys.version, "python_executable": sys.executable,
                "platform": platform.platform(), "machine": platform.machine(),
                "installed_distributions": versions, "area_counts": counts,
                "deferred_numerics_modules": [r["path"] for r in rows if r["state"] == "DEFERRED_METADATA"],
                "parse_errors": parse_errors, "spec_manifest_entries": len(entries),
                "spec_manifest_mismatches": manifest_mismatches,
                "import_root_counts": dict(Counter(e["target"].split(".")[0] for e in edges))}
    for name, value in (("repository_baseline.json", metadata), ("source_hashes.json", hashes), ("import_edges.json", edges)):
        (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    with (OUT / "source_inventory.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("path", "lines", "state", "symbols", "sha256"))
        writer.writeheader()
        writer.writerows(rows)
    scratch = Path(tempfile.mkdtemp(prefix="cosmos-p00-baseline-"))
    snapshot = scratch / "source"
    for relative in paths:
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    (OUT / "snapshot_location.txt").write_text(str(snapshot) + "\n")
    print(json.dumps({"sha": metadata["repo_sha"], "fingerprint": fingerprint,
                      "files": len(hashes), "python_modules": len(rows),
                      "deferred_numerics": len(metadata["deferred_numerics_modules"]),
                      "parse_errors": len(parse_errors), "manifest_mismatches": manifest_mismatches,
                      "snapshot": str(snapshot)}))


if __name__ == "__main__":
    main()
