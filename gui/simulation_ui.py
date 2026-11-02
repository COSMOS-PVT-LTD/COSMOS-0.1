"""Presentation flag and thin API bridge; no numerical computation in GUI."""
from api.simulation_workbench import ASSETS, catalog_item, dispatch
from gui.app_shell import shell_flag

__all__ = ("ASSETS", "catalog_item", "dispatch", "enabled")


def enabled(value: str | None, shell_enabled: bool) -> bool:
    return shell_enabled and shell_flag(value).enabled
