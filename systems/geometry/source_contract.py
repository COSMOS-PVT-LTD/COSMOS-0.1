"""Structural input boundary shared by live and captured geometry services."""
from typing import Any, Protocol

from systems.geometry.service import VerifiedCandidate
from systems.geometry.workbench import Revision


class GeometrySource(Protocol):
    def accepted(self, actor: str, job: str, snapshot: str) -> tuple[Revision, VerifiedCandidate]: ...
    def context(self, actor: str) -> dict[str, Any]: ...
