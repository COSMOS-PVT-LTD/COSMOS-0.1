"""Context packaging for KG-049."""

from __future__ import annotations

from knowledge.interface.exceptions import InterfaceValidationError
from knowledge.interface.identity import (
    deterministic_context_package_id,
    deterministic_package_digest,
)
from knowledge.interface.models import ContextPackage, ControlledRAGResult

__all__ = (
    "ContextPackager",
)

_PACKAGE_VERSION = "1.0.0"


class ContextPackager:
    """Create stable serializable context packages for downstream consumers."""

    def package(self, result: ControlledRAGResult) -> ContextPackage:
        """Package a controlled RAG result."""

        if not isinstance(result, ControlledRAGResult):
            raise InterfaceValidationError(
                "result must be a ControlledRAGResult instance.",
            )

        package_digest = deterministic_package_digest(
            result.package_digest,
            result.context.context_digest,
            _PACKAGE_VERSION,
        )
        package_id = deterministic_context_package_id(
            result.request_id,
            package_digest,
        )

        return ContextPackage(
            package_id=package_id,
            package_version=_PACKAGE_VERSION,
            request=result.request,
            result=result,
            classification=result.context.outcome.classification,
            package_digest=package_digest,
        )
