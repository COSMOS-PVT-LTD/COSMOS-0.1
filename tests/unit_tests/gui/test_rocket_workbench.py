"""P05 default-off delivery and asset boundaries without scientific writes."""
from pathlib import Path

import pytest

from gui.app_shell import ROCKET_WORKBENCH_ASSETS, inject_shell, shell_flag, use_shell

ROOT = Path(__file__).resolve().parents[3]


def test_flag_off_exact_rocket_bytes():
    original = (ROOT / "gui/static/workbench/rocket-engine.html").read_bytes()
    assert inject_shell(original, enabled=False) is original
    assert b"rocket-workbench/view.js" in inject_shell(original, enabled=True)


def test_other_workbenches_do_not_receive_rocket_ui():
    html = b'<html><head></head><body class="cosmos-app">Other</body></html>'
    assert b"rocket-workbench" not in inject_shell(html, enabled=True)


@pytest.mark.parametrize("query", ["shell=legacy", "shell=unknown", "shell=", "shell=modern&shell=legacy"])
def test_global_overrides_fail_closed(query):
    assert not use_shell(shell_flag("true"), "/app/workbench/rocket-engine?" + query)


def test_allowlisted_runtime_assets_exist():
    assert ROCKET_WORKBENCH_ASSETS == {"model.js", "view.js", "styles.css"}
    for name in ROCKET_WORKBENCH_ASSETS:
        assert (ROOT / "gui/static/rocket-workbench" / name).is_file()
