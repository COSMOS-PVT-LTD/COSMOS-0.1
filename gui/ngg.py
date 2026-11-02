"""P08 presentation wiring uses API facade; no deep scientific imports."""
from api.ngg_workbench import (
    ASSETS,
    CATALOG_ITEM,
    dispatch,
    read_payload,
    transport_guard,
)
from gui.app_shell import shell_flag

__all__ = ("ASSETS", "CATALOG_ITEM", "dispatch", "enabled", "read_payload", "transport_guard")


def enabled(value: str | None, modern_shell: bool) -> bool:
    return modern_shell and shell_flag(value).enabled
