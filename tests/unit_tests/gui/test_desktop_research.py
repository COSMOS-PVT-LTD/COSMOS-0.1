"""Native research dialogs preserve holds, explicit resolution and process ownership."""

from concurrent.futures import Future
from types import SimpleNamespace

import pytest

from gui import desktop_research


def tools(tmp_path):
    value = desktop_research.ResearchTools(tmp_path)
    value._window = SimpleNamespace(
        get_current_url=lambda: "about:blank",
        create_confirmation_dialog=lambda *_: True,
    )
    value._input = tmp_path / "research.json"
    value._input.write_text("{}")
    value._parent = tmp_path
    return value


def test_storage_hold_creates_nothing_and_starts_no_process(tmp_path, monkeypatch):
    tool = tools(tmp_path)
    monkeypatch.setattr(
        desktop_research.shutil,
        "disk_usage",
        lambda _: SimpleNamespace(free=9 * 1024**3),
    )
    before = set(tmp_path.iterdir())
    assert "paused" in tool.start("picogk", ".00025")["error"]
    assert set(tmp_path.iterdir()) == before and tool._future is None


@pytest.mark.parametrize("voxel", ["", None, "nan", "inf", "0", ".01", "not a number"])
def test_picogk_requires_explicit_bounded_resolution(tmp_path, monkeypatch, voxel):
    tool = tools(tmp_path)
    monkeypatch.setattr(
        desktop_research.shutil,
        "disk_usage",
        lambda _: SimpleNamespace(free=11 * 1024**3),
    )
    assert "error" in tool.start("picogk", voxel)
    assert tool._future is None


def test_declining_generation_never_starts_a_worker(tmp_path, monkeypatch):
    tool = tools(tmp_path)
    tool._window.create_confirmation_dialog = lambda *_: False
    monkeypatch.setattr(
        desktop_research.shutil,
        "disk_usage",
        lambda _: SimpleNamespace(free=11 * 1024**3),
    )
    assert tool.start("occt", "")["error"] == "No build started"
    assert tool._future is None


def test_external_origin_cannot_start_native_tool(tmp_path):
    tool = tools(tmp_path)
    tool._window.get_current_url = lambda: "https://example.com"
    assert "local native form" in tool.start("occt", "")["error"]


@pytest.mark.parametrize("backend", ["occt", "picogk"])
def test_trusted_bundled_command_and_cancellation(tmp_path, monkeypatch, backend):
    tool = tools(tmp_path)
    command = {}
    interpreter = tmp_path / ".venv-cad-inspection/bin/python"
    interpreter.parent.mkdir(parents=True)
    interpreter.write_text("#!/bin/sh\n")
    interpreter.chmod(0o755)

    class Supervisor:
        def __init__(self, **_):
            command["closed"] = False

        def submit(self, identity, worker, payload, directory):
            command.update(argv=worker.argv, directory=directory, payload=payload)
            return Future()

        def close(self):
            command["closed"] = True

    monkeypatch.setattr(desktop_research, "WorkerSupervisor", Supervisor)
    monkeypatch.setattr(
        desktop_research.shutil,
        "disk_usage",
        lambda _: SimpleNamespace(free=11 * 1024**3),
    )
    assert tool.start(backend, ".00025")["status"] == "RUNNING"
    assert command["argv"][0] == str(interpreter)
    assert command["argv"][2] == "scripts.generate_engine_redesign"
    assert "--research-only" in command["argv"]
    assert tool._output.parent == tmp_path and not tool._output.exists()
    assert tool.status()["status"] == "RUNNING"
    assert "One research build" in tool.start(backend, ".00025")["error"]
    tool._close()
    assert command["closed"]
