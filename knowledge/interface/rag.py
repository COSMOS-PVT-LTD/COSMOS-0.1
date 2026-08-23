"""Controlled RAG orchestration for KG-048."""

from __future__ import annotations

from knowledge.graph.query import GraphQueryService
from knowledge.graph.repository import GraphStore
from knowledge.indexing.w7 import W7IndexBundle
from knowledge.interface.exceptions import InterfaceValidationError
from knowledge.interface.identity import deterministic_package_digest
from knowledge.interface.models import ControlledRAGRequest, ControlledRAGResult
from knowledge.reasoning.evidence import EvidenceRanker
from knowledge.reasoning.w10 import W10EngineeringContextBuilder
from knowledge.search.contracts import SearchFilter, SearchQuery
from knowledge.search.w8 import HybridSearchEngine, ValidationAwareSearchEngine
from knowledge.validation.models import ValidationReport

__all__ = (
    "ControlledRAGOrchestrator",
)


class ControlledRAGOrchestrator:
    """
    Controlled retrieval/context orchestrator.

    Performs explicit retrieval and context assembly only — no LLM invocation.
    """

    def __init__(
        self,
        *,
        index_bundle: W7IndexBundle,
        graph_query: GraphQueryService,
        store: GraphStore,
    ) -> None:
        self._index_bundle = index_bundle
        self._graph_query = graph_query
        self._store = store
        self._hybrid = HybridSearchEngine(
            index_bundle,
            graph_query,
            store,
        )
        self._context_builder = W10EngineeringContextBuilder()
        self._evidence_ranker = EvidenceRanker(graph_query)

    def retrieve(
        self,
        request: ControlledRAGRequest,
        *,
        validation_report: ValidationReport | None = None,
    ) -> ControlledRAGResult:
        """Execute controlled retrieval and assemble engineering context."""

        if not isinstance(request, ControlledRAGRequest):
            raise InterfaceValidationError(
                "request must be a ControlledRAGRequest instance.",
            )

        filters = SearchFilter()

        if request.allowed_document_ids:
            if len(request.allowed_document_ids) != 1:
                raise InterfaceValidationError(
                    "allowed_document_ids supports one document filter in "
                    "reference implementation.",
                )

            filters = SearchFilter(document_id=request.allowed_document_ids[0])

        query = SearchQuery(
            text=request.query.text,
            mode=request.query.mode,
            filters=filters,
            order=request.query.order,
            limit=min(request.max_results, request.query.limit),
            offset=request.query.offset,
        )

        search_engine: HybridSearchEngine | ValidationAwareSearchEngine = (
            self._hybrid
        )

        if validation_report is not None:
            search_engine = ValidationAwareSearchEngine(
                self._hybrid,
                validation_report=validation_report,
            )

        page = search_engine.search(query)
        evidence = self._evidence_ranker.assemble(page.results)
        context = self._context_builder.build(
            task=request.task,
            query=query,
            evidence=evidence,
            validation_report=validation_report,
            retrieval_metadata={
                "request_id": request.request_id,
                "result_count": page.total_count,
            },
        )

        package_digest = deterministic_package_digest(
            request.request_id,
            context.context_digest,
            context.outcome.classification.value,
        )

        return ControlledRAGResult(
            request=request,
            context=context,
            retrieval_methods=("keyword", "semantic", "graph", "hybrid"),
            package_digest=package_digest,
            provider_invoked=False,
        )
