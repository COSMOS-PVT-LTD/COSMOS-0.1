import pytest

from gui.simulation_ui import enabled


@pytest.mark.parametrize("value", [None, "", "0", "false", "random", "2"])
def test_simulation_flag_default_off_and_strict(value):
    assert not enabled(value, True)


def test_requires_explicit_shell_and_flag():
    assert enabled("true", True) and enabled("1", True)
    assert not enabled("1", False)
