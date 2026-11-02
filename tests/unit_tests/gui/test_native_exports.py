"""Native download configuration only; not a native UI acceptance claim."""
import sys
from types import SimpleNamespace

from gui import native_window


def test_local_exports_enabled_before_native_creation_without_file_url_access(monkeypatch):
    events = []
    settings = {"ALLOW_DOWNLOADS": False, "ALLOW_FILE_URLS": True}

    def create_window(*_args, **_kwargs):
        events.append(dict(settings))
        return SimpleNamespace()

    fake = SimpleNamespace(settings=settings, create_window=create_window,
        start=lambda **_kwargs: events.append("started"))
    monkeypatch.setitem(sys.modules, "webview", fake)
    monkeypatch.setattr(native_window, "require_native_runtime", lambda: None)
    native_window.launch_native_window(url="http://127.0.0.1:8845", title="Synthetic isolated QA")
    assert events == [{"ALLOW_DOWNLOADS": True, "ALLOW_FILE_URLS": False}, "started"]
