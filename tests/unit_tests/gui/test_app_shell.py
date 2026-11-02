"""Presentation rollout flags must never enable a scientific backend."""

import pytest

from gui.app_shell import inject_shell, shell_flag, use_shell


@pytest.mark.parametrize("value", [None, "", "0", "false", "FALSE", " false "])
def test_defaults_off(value):
    assert not shell_flag(value).enabled


@pytest.mark.parametrize("value", ["1", "true", " TRUE "])
def test_opt_in(value):
    assert shell_flag(value).enabled


@pytest.mark.parametrize("value", ["yes", "on", "2", "null"])
def test_malformed(value):
    flag = shell_flag(value)
    assert not flag.enabled
    assert flag.diagnostic == "INVALID_SHELL_FLAG"


@pytest.mark.parametrize("query", ["legacy", "", "unknown", "modern&shell=legacy"])
def test_query_rollback_fails_closed(query):
    assert not use_shell(shell_flag("1"), "/app/projects?shell=" + query)


def test_query_cannot_enable_server_disabled_shell():
    assert not use_shell(shell_flag("0"), "/app/projects?shell=modern")
    assert use_shell(shell_flag("1"), "/app/projects?shell=modern")


def test_off_html_is_exact_original_bytes():
    html = b"<!doctype html><head></head><body>original</body>"
    assert inject_shell(html, enabled=False) is html
    modified = inject_shell(html, enabled=True)
    assert modified.count(b'content="p04-v1"') == 1
    assert b"/assets/app-shell/adapter.js" in modified
    assert modified.endswith(b"<body>original</body>")


def test_invalid_environment_keeps_legacy(tmp_path, monkeypatch):
    from gui.server import CosmosApplication

    monkeypatch.setenv("COSMOS_NEW_SHELL", "yes")
    flag = CosmosApplication(tmp_path).shell_flag
    assert flag.diagnostic == "INVALID_SHELL_FLAG"
    assert not flag.enabled


def test_environment_enable_and_explicit_rollback(tmp_path, monkeypatch):
    from gui.server import CosmosApplication

    monkeypatch.setenv("COSMOS_NEW_SHELL", "1")
    assert CosmosApplication(tmp_path / "enabled").shell_flag.enabled
    assert not CosmosApplication(
        tmp_path / "legacy", new_shell=False
    ).shell_flag.enabled
