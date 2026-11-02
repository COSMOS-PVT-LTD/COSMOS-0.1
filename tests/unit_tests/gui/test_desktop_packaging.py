"""Packaging refusal/closure behavior without creating another large bundle."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import build_standalone_desktop as builder


def test_complete_or_unmarked_existing_app_is_never_overwritten(tmp_path, monkeypatch):
    monkeypatch.setattr(builder.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(builder.platform, "machine", lambda: "arm64")
    app = tmp_path / "Existing.app"
    app.mkdir()
    marker = app / "precious.txt"
    marker.write_text("preserve")
    with pytest.raises(ValueError, match="nothing is overwritten"):
        builder.build(tmp_path, app, tmp_path, tmp_path, tmp_path, [], resume=True)
    assert marker.read_text() == "preserve"


def test_disk_guard_does_not_create_an_app(tmp_path, monkeypatch):
    monkeypatch.setattr(builder.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(builder.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(
        builder.shutil, "disk_usage", lambda _: SimpleNamespace(free=2 * 1024**3)
    )
    app = tmp_path / "New.app"
    with pytest.raises(ValueError, match="3GiB free"):
        builder.build(tmp_path, app, tmp_path, tmp_path, tmp_path, [])
    assert not app.exists()


def test_mach_o_universal_duplicate_dependency_is_rebased_once(tmp_path, monkeypatch):
    copier = builder.Copier()
    source = tmp_path / "original"
    source.write_bytes(b"native")
    target = tmp_path / "app" / "lib.dylib"
    target.parent.mkdir()
    target.write_bytes(b"\xcf\xfa\xed\xfe")
    copier.origins[target] = source
    calls = []

    def run(args):
        calls.append(args)
        if "-D" in args:
            return str(target) + ":\n /build-only/lib.dylib\n"
        if "-L" in args:
            return (
                str(target)
                + ":\n\t/build-only/lib.dylib (compatibility version 1)\n\t/build-only/lib.dylib (compatibility version 1)\n"
            )
        return ""

    monkeypatch.setattr(builder, "run", run)
    copier.relocate(target.parent, Path("/unused"))
    edit = next(args for args in calls if "install_name_tool" in str(args[0]))
    assert edit.count("-id") == 1
