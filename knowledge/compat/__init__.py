"""
KG-BLOCK-013 Phase B compatibility infrastructure.

Compatibility modules delegate to canonical implementations only.
Canonical code MUST NOT import from knowledge.compat.
"""

from __future__ import annotations

__all__ = ("COMPATIBILITY_LAYER",)

COMPATIBILITY_LAYER = True
