"""Tests for native desktop window runtime."""

from __future__ import annotations

import pytest

from gui.native_window import NativeWindowError, require_native_runtime


def test_require_native_runtime_with_pywebview() -> None:
    try:
        require_native_runtime()
    except NativeWindowError:
        pytest.skip("pywebview not installed in this environment")


def test_main_exits_without_pywebview(monkeypatch) -> None:
    import builtins

    real_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name == "webview":
            raise ImportError("blocked for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    with pytest.raises(NativeWindowError):
        require_native_runtime()
