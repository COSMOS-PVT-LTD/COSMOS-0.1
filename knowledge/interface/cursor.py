"""Cursor development context for KG-050."""

from __future__ import annotations

from knowledge.interface.exceptions import InterfaceValidationError
from knowledge.interface.identity import (
    deterministic_cursor_context_id,
    deterministic_package_digest,
)
from knowledge.interface.models import ContextPackage, CursorDevelopmentContext

__all__ = (
    "CursorContextBuilder",
)

_CONTENT_KIND = "knowledge_evidence"


class CursorContextBuilder:
    """Build controlled Cursor development context from context packages."""

    def build(
        self,
        *,
        project_id: str,
        engineering_task_id: str,
        package: ContextPackage,
        constraints: tuple[str, ...] = (),
        assumptions: tuple[str, ...] = (),
    ) -> CursorDevelopmentContext:
        """Assemble a Cursor development context boundary package."""

        if not isinstance(package, ContextPackage):
            raise InterfaceValidationError(
                "package must be a ContextPackage instance.",
            )

        if not project_id.strip():
            raise InterfaceValidationError("project_id must not be blank.")

        if not engineering_task_id.strip():
            raise InterfaceValidationError(
                "engineering_task_id must not be blank.",
            )

        context_digest = deterministic_package_digest(
            project_id.strip(),
            engineering_task_id.strip(),
            package.package_digest,
            _CONTENT_KIND,
        )
        context_id = deterministic_cursor_context_id(
            project_id.strip(),
            engineering_task_id.strip(),
            package.package_digest,
        )

        return CursorDevelopmentContext(
            context_id=context_id,
            project_id=project_id.strip(),
            engineering_task_id=engineering_task_id.strip(),
            package=package,
            constraints=tuple(sorted(constraints)),
            assumptions=tuple(sorted(assumptions)),
            content_kind=_CONTENT_KIND,
            context_digest=context_digest,
        )
