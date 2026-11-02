"""P11 feature flag and presentation-only bridge."""
from api.knowledge_reports import ASSETS, CATALOG_ITEM, dispatch
from gui.app_shell import shell_flag

__all__ = ("ASSETS", "CATALOG_ITEM", "dispatch", "enabled")


def enabled(value: str | None, shell_enabled: bool) -> bool:
    return shell_enabled and shell_flag(value).enabled
