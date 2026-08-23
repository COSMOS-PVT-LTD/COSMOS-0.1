"""Validation-aware search wrapper for W8 integration."""

from __future__ import annotations

from knowledge.search.contracts import SearchQuery, SearchResultPage
from knowledge.search.exceptions import SearchValidationError
from knowledge.validation.models import ValidationReport, ValidationStatus

__all__ = (
    "ValidationAwareSearchEngine",
)


class ValidationAwareSearchEngine:
    """Filter search results using W9 validation findings without mutating inputs."""

    def __init__(
        self,
        inner_engine,
        *,
        validation_report: ValidationReport | None = None,
        exclude_invalid_targets: bool = True,
    ) -> None:
        self._inner_engine = inner_engine
        self._validation_report = validation_report
        self._exclude_invalid_targets = exclude_invalid_targets

    def search(self, query: SearchQuery) -> SearchResultPage:
        """Execute search and apply validation-aware filtering."""

        if not isinstance(query, SearchQuery):
            raise SearchValidationError(
                "query must be a SearchQuery instance.",
            )

        page = self._inner_engine.search(query)

        if self._validation_report is None or not self._exclude_invalid_targets:
            return page

        invalid_targets = {
            finding.object_id
            for finding in self._validation_report.findings
            if finding.status is ValidationStatus.INVALID
        }

        filtered = tuple(
            result
            for result in page.results
            if result.target_id not in invalid_targets
        )

        return SearchResultPage(
            results=filtered,
            total_count=len(filtered),
            limit=page.limit,
            offset=page.offset,
        )

    def has_verified_results(self, page: SearchResultPage) -> bool:
        """Return True only when results include approved lifecycle states."""

        return any(
            result.lifecycle_state in {"APPROVED", "VERIFIED"}
            for result in page.results
        )
