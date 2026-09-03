"""
COSMOS Systems — propulsion workflow orchestration above frozen Physics.

Layer rule:
    systems → physics → core
    gui ─X→ systems internals (HTTP/API only)
"""

from __future__ import annotations

from typing import Final

from core.version import COSMOS_VERSION

__all__ = (
    "SYSTEMS_SCHEMA_VERSION",
    "SYSTEMS_PACKAGE_VERSION",
)

SYSTEMS_SCHEMA_VERSION: Final[str] = "0.1.0"
SYSTEMS_PACKAGE_VERSION: Final[str] = COSMOS_VERSION
