"""Launcher refuses missing data and occupied ports without initialization/kills."""

import sqlite3
import sys
from types import ModuleType

import pytest

from scripts import launch_compact_engine


def test_missing_root_is_never_initialized(tmp_path, monkeypatch):
    monkeypatch.setattr(
        launch_compact_engine,
        "__file__",
        str(tmp_path / "scripts/launch_compact_engine.py"),
    )
    monkeypatch.setattr(sys, "argv", ["launch_compact_engine"])
    with pytest.raises(SystemExit, match="nothing was initialized"):
        launch_compact_engine.main()
    assert not (tmp_path / "output").exists()


@pytest.fixture
def configured_repo(tmp_path):
    root = tmp_path / "output/picogk-components-2026-10-24/app-data"
    store = root / "engineering_state/v1"
    store.mkdir(parents=True)
    (root / "auth").mkdir()
    (root / "auth/users.sqlite").touch()
    with sqlite3.connect(store / "metadata.sqlite3") as database:
        database.execute("CREATE TABLE objects(project_id TEXT,domain TEXT)")
        database.execute(
            "INSERT INTO objects VALUES(?,?)",
            ("bb7ebea6-15f9-43b8-b6c0-fd2a2d358155", "engine-development-baseline"),
        )
    return tmp_path


def test_occupied_port_is_not_stopped_or_bypassed(configured_repo, monkeypatch):

    class Occupied:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def bind(self, _):
            raise OSError("Test occupied port")

    monkeypatch.setattr(
        launch_compact_engine,
        "__file__",
        str(configured_repo / "scripts/launch_compact_engine.py"),
    )
    monkeypatch.setattr(launch_compact_engine.socket, "socket", Occupied)
    monkeypatch.setattr(sys, "argv", ["launch_compact_engine"])
    with pytest.raises(SystemExit, match="No process was stopped"):
        launch_compact_engine.main()


def test_integrity_failure_is_explained_without_reset(configured_repo, monkeypatch):
    from systems.projects.authority import IntegrityFailure

    for profile in ("occt-runtime", "pico-runtime-v4"):
        path = (
            configured_repo
            / "docs/implementation/evidence/PICOGK_COMPONENTS_2026-10-24"
            / profile
        )
        path.mkdir(parents=True)
        (path / "runtime.json").write_text("{}")
    launched = []

    def fail(**kwargs):
        launched.append(kwargs)
        raise IntegrityFailure("Retained source bytes are missing or inaccessible.")

    application = ModuleType("gui.application")
    application.launch_desktop_application = fail
    monkeypatch.setitem(sys.modules, "gui.application", application)

    class Available:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def bind(self, _):
            pass

    monkeypatch.setattr(launch_compact_engine.socket, "socket", Available)
    monkeypatch.setattr(
        launch_compact_engine,
        "__file__",
        str(configured_repo / "scripts/launch_compact_engine.py"),
    )
    monkeypatch.setattr(sys, "argv", ["launch_compact_engine"])
    for flag in (
        "COSMOS_NEW_SHELL",
        "COSMOS_DURABLE_PROJECTS",
        "COSMOS_NGG",
        "COSMOS_NEW_SIM_UI",
        "COSMOS_NEW_VV_UI",
        "COSMOS_NEW_KNOWLEDGE_REPORTS_UI",
        "COSMOS_NGG_RUNTIME_CONFIG",
        "COSMOS_PICOGK_COMPONENT_CONFIG",
    ):
        monkeypatch.setenv(flag, "test-sentinel")
    database = (
        configured_repo
        / "output/picogk-components-2026-10-24/app-data/engineering_state/v1/metadata.sqlite3"
    )
    before = database.read_bytes()
    with pytest.raises(SystemExit, match="No project history was reset"):
        launch_compact_engine.main()
    assert len(launched) == 1
    assert database.read_bytes() == before


def test_privileged_port_rejected_before_opening_data(tmp_path, monkeypatch):
    monkeypatch.setattr(
        launch_compact_engine,
        "__file__",
        str(tmp_path / "scripts/launch_compact_engine.py"),
    )
    monkeypatch.setattr(sys, "argv", ["launch_compact_engine", "--port", "80"])
    with pytest.raises(SystemExit):
        launch_compact_engine.main()
    assert not (tmp_path / "output").exists()
