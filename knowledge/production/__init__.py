"""Production local RAG engineering package (Step 7)."""

from __future__ import annotations

from knowledge.production.benchmark_suite import ProductionBenchmarkReport, ProductionBenchmarkSuite
from knowledge.production.embedding_evaluation import (
    EmbeddingEvaluationReport,
    EmbeddingRecommendation,
    EmbeddingStrategyEvaluator,
)
from knowledge.production.graph_merge import DocumentGraphMerger, GraphMergeResult
from knowledge.production.incremental_ingestion import (
    IncrementalIngestionCoordinator,
    IngestionAction,
)
from knowledge.production.local_rag_pipeline import (
    ProductionLocalRAGPipeline,
    ProductionLocalRAGResult,
)
from knowledge.production.observability import ObservabilityRecorder, ObservabilityStage
from knowledge.production.observability_export import (
    ObservabilityExporter,
    StructuredObservabilitySession,
)
from knowledge.production.operational_observability import (
    OperationalObservabilityBridge,
    OperationalEventTaxonomy,
    redact_sensitive_metadata,
)
from knowledge.production.offline_guard import OfflineExecutionGuard, ProviderInvocationState
from knowledge.production.performance import PerformanceBenchmark
from knowledge.production.recovery import RecoveryProcedure
from knowledge.production.retrieval_service import ProductionRetrievalService
from knowledge.production.scale_benchmark import (
    CorpusBenchmarkResult,
    ScaleBenchmarkReport,
    ScaleBenchmarkRunner,
    ScaleVerificationResult,
    generate_scale_corpus,
)

__all__ = (
    "CorpusBenchmarkResult",
    "DocumentGraphMerger",
    "EmbeddingEvaluationReport",
    "EmbeddingRecommendation",
    "EmbeddingStrategyEvaluator",
    "GraphMergeResult",
    "IncrementalIngestionCoordinator",
    "IngestionAction",
    "ObservabilityExporter",
    "ObservabilityRecorder",
    "ObservabilityStage",
    "OfflineExecutionGuard",
    "OperationalEventTaxonomy",
    "OperationalObservabilityBridge",
    "PerformanceBenchmark",
    "ProductionBenchmarkReport",
    "ProductionBenchmarkSuite",
    "ProductionLocalRAGPipeline",
    "ProductionLocalRAGResult",
    "ProductionRetrievalService",
    "ProviderInvocationState",
    "RecoveryProcedure",
    "ScaleBenchmarkReport",
    "ScaleBenchmarkRunner",
    "ScaleVerificationResult",
    "StructuredObservabilitySession",
    "generate_scale_corpus",
    "redact_sensitive_metadata",
)
