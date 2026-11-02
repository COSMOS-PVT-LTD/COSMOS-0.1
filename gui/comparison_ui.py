"""P10 presentation flag and API bridge; no scientific computation in GUI."""
from api.comparison_workbench import ASSETS, CATALOG_ITEM, dispatch
from gui.app_shell import shell_flag

__all__ = ("ASSETS", "CATALOG_ITEM", "dispatch", "enabled")


def enabled(value: str | None, shell_enabled: bool) -> bool:
    return shell_enabled and shell_flag(value).enabled
