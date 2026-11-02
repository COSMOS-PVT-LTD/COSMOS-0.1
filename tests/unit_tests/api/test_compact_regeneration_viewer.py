"""Read-only viewer preflight tests: no GUI, network listener or owner store."""

import json
import re
import shutil
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import view_compact_regeneration as viewer


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("Preflight must reject before server/window startup")

    monkeypatch.setitem(
        sys.modules,
        "webview",
        SimpleNamespace(create_window=forbidden, start=forbidden),
    )
    monkeypatch.setattr(viewer, "ThreadingHTTPServer", forbidden)
    campaign = tmp_path / "campaign"
    display = campaign / "display"
    display.mkdir(parents=True)
    # Minimal manufactured byte payload; guard tests never decode/render it.
    mesh = display / "DISPLAY-ONLY-export.stl"
    mesh.write_bytes(b"Manufactured preflight byte fixture, not an engine mesh")
    manifest = {
        "schema": "cosmos.compact-engine-display.v1",
        "recipe_sha256": "a" * 64,
        "source_commit_id": "manufactured-source-commit",
        "artifacts": {mesh.name: sha256(mesh.read_bytes()).hexdigest()},
    }
    (display / "manifest.json").write_text(json.dumps(manifest))
    (campaign / "preflight.json").write_text(
        json.dumps(
            {
                "recipe_sha256": manifest["recipe_sha256"],
                "component_source_commit_id": manifest["source_commit_id"],
            }
        )
    )
    return campaign, mesh, manifest, calls


@pytest.mark.parametrize("seconds", [-1, 46, True, 1.5])
def test_invalid_hold_interval_rejected_before_native_start(isolated, seconds):
    campaign, _, _, calls = isolated
    with pytest.raises(ValueError, match="inspection interval"):
        viewer.launch(campaign, inspect_seconds=seconds)
    assert calls == []


def test_existing_verification_output_is_never_overwritten(isolated, tmp_path):
    campaign, _, _, calls = isolated
    output = tmp_path / "existing-proof.json"
    output.write_text("Retained test proof")
    with pytest.raises(ValueError, match="verification output"):
        viewer.launch(campaign, output=output)
    assert output.read_text() == "Retained test proof"
    assert calls == []


@pytest.mark.parametrize("kind", ["relative", "missing-parent", "broken-symlink"])
def test_invalid_verification_target_rejected_before_native_start(
    isolated, tmp_path, kind
):
    campaign, _, _, calls = isolated
    output = tmp_path / "proof.json"
    if kind == "relative":
        output = Path("relative-proof.json")
    elif kind == "missing-parent":
        output = tmp_path / "absent-parent" / "proof.json"
    else:
        output.symlink_to(tmp_path / "absent-target.json")
    with pytest.raises(ValueError, match="verification output"):
        viewer.launch(campaign, output=output)
    assert calls == []


@pytest.mark.parametrize("key", ["schema", "recipe_sha256", "source_commit_id"])
def test_mismatched_campaign_source_recipe_schema_rejected_before_start(isolated, key):
    campaign, _, manifest, calls = isolated
    manifest[key] = "different-retained-value"
    (campaign / "display/manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="exact source/recipe"):
        viewer.launch(campaign)
    assert calls == []


def test_changed_display_bytes_cannot_reuse_manifest_hash(isolated):
    campaign, mesh, _, calls = isolated
    mesh.write_bytes(b"Changed manufactured byte fixture")
    with pytest.raises(ValueError, match="exact source/recipe"):
        viewer.launch(campaign)
    assert calls == []


def test_missing_mesh_fails_before_server_window_start(isolated):
    campaign, mesh, _, calls = isolated
    mesh.unlink()
    with pytest.raises((FileNotFoundError, ValueError)):
        viewer.launch(campaign)
    assert calls == []


def test_oversized_mesh_rejected_without_rendering_or_hash_allocation(isolated):
    campaign, mesh, _, calls = isolated
    # Sparse temporary fixture exercises stat limit, not a large CAD allocation.
    with mesh.open("wb") as stream:
        stream.truncate(10_000_085)
    with pytest.raises(ValueError, match="display mesh|exact source/recipe"):
        viewer.launch(campaign)
    assert calls == []


@pytest.mark.parametrize("name", ["display/manifest.json", "preflight.json"])
def test_oversized_manifest_rejected_before_json_allocation(isolated, name):
    campaign, _, _, calls = isolated
    with (campaign / name).open("wb") as stream:
        stream.truncate(262145)
    with pytest.raises(ValueError, match="Bounded source manifests"):
        viewer.launch(campaign)
    assert calls == []


def test_window_creation_failure_closes_the_stubbed_server(isolated, monkeypatch):
    campaign, _, _, _ = isolated
    events = []

    class Server:
        server_port = 12345

        def __init__(self, *_):
            pass

        def serve_forever(self):
            pass

        def shutdown(self):
            events.append("shutdown")

        def server_close(self):
            events.append("close")

    class Thread:
        def __init__(self, **_):
            pass

        def start(self):
            events.append("thread-start")

        def join(self, **_):
            events.append("thread-join")

    def fail_window(*_, **__):
        raise ValueError("Manufactured native-window startup failure")

    monkeypatch.setattr(viewer, "ThreadingHTTPServer", Server)
    monkeypatch.setattr(viewer.threading, "Thread", Thread)
    monkeypatch.setattr(sys.modules["webview"], "create_window", fail_window)
    with pytest.raises(ValueError, match="startup failure"):
        viewer.launch(campaign)
    assert events == ["thread-start", "shutdown", "close", "thread-join"]


def test_classic_script_dependencies_publish_browser_viewport_globals():
    """Catch CommonJS decoder bridge leaking into browser-only dependencies."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node required for offline classic-script integration check")
    root = Path(viewer.__file__).resolve().parents[1]
    scripts = re.findall(r"<script([^>]*)>(.*?)</script>", viewer.PAGE, re.DOTALL)
    dependency_scripts = []
    for attrs, body in scripts:
        source = re.search(r'src="(/assets/[^\"]+)"', attrs)
        if source:
            dependency_scripts.append(
                (root / "gui/static" / source[1][len("/assets/") :]).read_text()
            )
        elif "fetch(" not in body:
            dependency_scripts.append(body)
    program = """
const vm = require('node:vm');
const scripts = JSON.parse(process.argv[1]);
const context = vm.createContext({});
vm.runInContext('window=globalThis', context);
for (const script of scripts) vm.runInContext(script, context);
if (vm.runInContext('typeof CosmosNGGViewport',context) !== 'function' ||
    vm.runInContext('typeof CosmosNGGViewTools?.mountTools',context) !== 'function' ||
    vm.runInContext('typeof compactResearchDecoder',context) !== 'function') {
  throw Error('Offline browser viewport globals were suppressed by module.exports');
}
"""
    completed = subprocess.run(
        [node, "-e", program, json.dumps(dependency_scripts)],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr[-1200:]
