"""Desktop-only ownership, explicit roots, no browser fallback or migration."""

import json
import socket
import urllib.request
from types import SimpleNamespace

import pytest

from gui import application
from gui.desktop_app import DesktopSession, WorkspaceBridge
from gui.desktop_config import (
    FLAGS,
    RUNTIMES,
    Workspace,
    enable_workspaces,
    existing_root,
    read_profile,
)
from gui.desktop_runtime import DesktopServer
from gui.native_window import NativeWindowError


def test_native_window_closes_backend_and_port(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(application, "require_native_runtime", lambda: None)

    def window(**kwargs):
        seen.update(kwargs)
        assert b"LOGIN" in urllib.request.urlopen(kwargs["url"], timeout=5).read()

    monkeypatch.setattr(application, "launch_native_window", window)
    monkeypatch.setattr(
        application.webbrowser,
        "open",
        lambda *_: pytest.fail("Desktop must not open browser"),
    )
    application.launch_desktop_application(root=tmp_path, port=0)
    with pytest.raises(OSError):
        urllib.request.urlopen(seen["url"], timeout=1)


def test_missing_native_runtime_never_opens_data_or_browser(tmp_path, monkeypatch):
    def missing():
        raise NativeWindowError("missing native runtime")

    monkeypatch.setattr(application, "require_native_runtime", missing)
    monkeypatch.setattr(
        application.webbrowser, "open", lambda *_: pytest.fail("No fallback")
    )
    with pytest.raises(NativeWindowError):
        application.launch_desktop_application(root=tmp_path / "untouched", port=0)
    assert not (tmp_path / "untouched").exists()


@pytest.mark.parametrize(
    "path", ["https://example.com", "//example.com", "/\\example.com"]
)
def test_external_start_paths_rejected_before_data(tmp_path, path):
    with pytest.raises(ValueError):
        application.launch_desktop_application(
            root=tmp_path / "untouched", start_path=path
        )
    assert not (tmp_path / "untouched").exists()


@pytest.mark.parametrize(
    "host,port", [("0.0.0.0", 0), ("127.0.0.1", 80), ("127.0.0.1", -1)]
)
def test_desktop_loopback_only(tmp_path, host, port):
    with pytest.raises(ValueError):
        DesktopServer(tmp_path / "untouched", host=host, port=port)
    assert not (tmp_path / "untouched").exists()


def test_close_releases_managed_lease_for_next_desktop(tmp_path, monkeypatch):
    monkeypatch.setenv("COSMOS_NEW_SHELL", "1")
    monkeypatch.setenv("COSMOS_DURABLE_PROJECTS", "1")
    with DesktopServer(tmp_path) as first:
        assert first.thread.is_alive()
    first.close()
    with DesktopServer(tmp_path) as second:
        assert second.thread.is_alive()


def test_occupied_listener_is_not_adopted_or_stopped(tmp_path):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        with pytest.raises(OSError):
            DesktopServer(tmp_path, port=listener.getsockname()[1])
        assert listener.fileno() >= 0


def test_root_selection_never_initializes_missing_data(tmp_path):
    with pytest.raises(ValueError, match="Nothing was initialized"):
        existing_root(tmp_path / "missing")
    assert not (tmp_path / "missing").exists()


def profile(tmp_path):
    for name in ("occt.json", "pico.json"):
        (tmp_path / name).write_text("{}")
    path = tmp_path / "profile.json"
    value = {
        "schema": "cosmos.desktop-profile.v1",
        "workspaces": [
            {"key": "main", "label": "Main", "root": str(tmp_path / "existing")}
        ],
        "runtimes": dict(zip(RUNTIMES, ("occt.json", "pico.json"), strict=True)),
    }
    path.write_text(json.dumps(value))
    return path, value


def test_profile_enables_all_current_workspaces_without_opening_user_data(
    tmp_path, monkeypatch
):
    path, _ = profile(tmp_path)
    roots, runtimes = read_profile(path)
    for flag in FLAGS + RUNTIMES:
        monkeypatch.delenv(flag, raising=False)
    enable_workspaces(runtimes)
    import os

    assert all(os.environ[f] == "1" for f in FLAGS)
    assert roots[0].key == "main" and not roots[0].root.exists()


@pytest.mark.parametrize(
    "alter", ["duplicate", "escape", "absolute-runtime", "relative-root"]
)
def test_profile_refuses_ambiguous_paths(tmp_path, alter):
    path, value = profile(tmp_path)
    if alter == "duplicate":
        value["workspaces"] *= 2
    elif alter == "escape":
        value["runtimes"][RUNTIMES[0]] = "../outside.json"
    elif alter == "absolute-runtime":
        value["runtimes"][RUNTIMES[0]] = str(tmp_path / "occt.json")
    else:
        value["workspaces"][0]["root"] = "relative"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        read_profile(path)


def test_bridge_denies_engineering_and_external_origins(tmp_path):
    session = DesktopSession([Workspace("main", "Main", tmp_path)])
    session.window = SimpleNamespace(get_current_url=lambda: "https://example.com")
    assert "error" in WorkspaceBridge(session).open_workspace("main")
    session.window = SimpleNamespace(get_current_url=lambda: "about:blank")
    assert "Unknown" in WorkspaceBridge(session).open_workspace("/etc/passwd")["error"]


def test_chooser_escapes_labels_and_roots(tmp_path):
    session = DesktopSession(
        [Workspace("main", "<script>bad</script>", tmp_path / '"<unsafe>')]
    )
    assert "<script>bad" not in session.home()
    assert "&lt;unsafe&gt;" in session.home()


def test_declined_switch_leaves_running_server_untouched(tmp_path):
    session = DesktopSession([Workspace("main", "Main", tmp_path)])
    session.window = SimpleNamespace(create_confirmation_dialog=lambda *_: False)
    session.server = object()
    previous = session.server
    assert "unchanged" in session.open_workspace("main")["error"]
    session.choose()
    assert session.server is previous


def test_bridge_resolves_local_url_before_document_navigation():
    session = SimpleNamespace(
        window=SimpleNamespace(get_current_url=lambda: "about:blank"),
        open_workspace=lambda key, **kwargs: {"key": key, **kwargs},
    )
    assert WorkspaceBridge(session).open_workspace("main") == {
        "key": "main",
        "navigate": False,
    }
