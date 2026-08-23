"""Embedding strategy evaluation for Gate-6 readiness (Step 7)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from enum import Enum

from knowledge.embeddings import DeterministicLocalEmbeddingBackend
from knowledge.embeddings.identity import EmbeddingModelIdentity

__all__ = (
    "EmbeddingEvaluationReport",
    "EmbeddingRecommendation",
    "EmbeddingStrategyEvaluator",
)


class EmbeddingRecommendation(Enum):
    """Gate-6 embedding strategy recommendation."""

    KEEP_DETERMINISTIC_V1 = "KEEP_DETERMINISTIC_V1"
    ADOPT_LOCAL_NEURAL_BACKEND = "ADOPT_LOCAL_NEURAL_BACKEND"
    SUPPORT_BOTH_AS_QUALIFIED_CONFIGURATIONS = "SUPPORT_BOTH_AS_QUALIFIED_CONFIGURATIONS"
    DEFER_NEURAL_BACKEND = "DEFER_NEURAL_BACKEND"


@dataclass(frozen=True, slots=True, kw_only=True)
class EmbeddingBackendMetrics:
    """Measured embedding backend metrics."""

    backend_id: str
    dimension: int
    embed_latency_p50_ms: float
    embed_latency_max_ms: float
    requires_network: bool
    bitwise_deterministic: bool
    locally_evaluated: bool
    notes: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "backend_id": self.backend_id,
            "bitwise_deterministic": self.bitwise_deterministic,
            "dimension": self.dimension,
            "embed_latency_max_ms": round(self.embed_latency_max_ms, 4),
            "embed_latency_p50_ms": round(self.embed_latency_p50_ms, 4),
            "locally_evaluated": self.locally_evaluated,
            "notes": self.notes,
            "requires_network": self.requires_network,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class EmbeddingEvaluationReport:
    """Embedding evaluation synthesis for human Gate-6 review."""

    deterministic_metrics: EmbeddingBackendMetrics
    neural_metrics: EmbeddingBackendMetrics | None
    recommendation: EmbeddingRecommendation
    retrieval_comparison_available: bool
    licensing_ip_notes: str
    offline_notes: str
    decision_conditions: tuple[str, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "decision_conditions": list(self.decision_conditions),
            "deterministic_metrics": self.deterministic_metrics.to_mapping(),
            "licensing_ip_notes": self.licensing_ip_notes,
            "neural_metrics": (
                None if self.neural_metrics is None else self.neural_metrics.to_mapping()
            ),
            "offline_notes": self.offline_notes,
            "recommendation": self.recommendation.value,
            "retrieval_comparison_available": self.retrieval_comparison_available,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), indent=2, sort_keys=True)


class EmbeddingStrategyEvaluator:
    """Evaluate embedding options without introducing cloud dependencies."""

    _SAMPLE_TEXTS: tuple[str, ...] = (
        "chamber pressure nominal LOX flow",
        "thrust vector control subsystem margin",
        "engine ignition sequence verification",
        "turbopump inlet temperature monitoring",
    )

    def evaluate_deterministic(self, *, dimension: int = 8) -> EmbeddingBackendMetrics:
        backend = DeterministicLocalEmbeddingBackend(dimension=dimension)
        latencies: list[float] = []

        for text in self._SAMPLE_TEXTS:
            start = time.perf_counter()
            backend.embed_query(text)
            latencies.append((time.perf_counter() - start) * 1000.0)

        sorted_latencies = sorted(latencies)

        return EmbeddingBackendMetrics(
            backend_id=backend.identity.fingerprint(),
            dimension=dimension,
            embed_latency_p50_ms=sorted_latencies[len(sorted_latencies) // 2],
            embed_latency_max_ms=sorted_latencies[-1],
            requires_network=False,
            bitwise_deterministic=True,
            locally_evaluated=True,
            notes="Approved Gate-2 Option A backend; qualification plumbing only.",
        )

    def evaluate_neural_local(self) -> EmbeddingBackendMetrics | None:
        """Attempt local neural evaluation; return None if unavailable."""

        try:
            import importlib.util

            if importlib.util.find_spec("sentence_transformers") is None:
                return None
        except ModuleNotFoundError:
            return None

        # Neural backend not bundled in COSMOS dev dependencies — defer.
        return None

    def build_report(self, *, dimension: int = 8) -> EmbeddingEvaluationReport:
        deterministic = self.evaluate_deterministic(dimension=dimension)
        neural = self.evaluate_neural_local()

        if neural is None:
            return EmbeddingEvaluationReport(
                deterministic_metrics=deterministic,
                neural_metrics=None,
                recommendation=EmbeddingRecommendation.DEFER_NEURAL_BACKEND,
                retrieval_comparison_available=False,
                licensing_ip_notes=(
                    "Deterministic backend has no external model licensing burden. "
                    "Neural candidate not present in repository dependencies."
                ),
                offline_notes=(
                    "Deterministic backend is fully offline. "
                    "Neural evaluation deferred — no approved local model artifact bundled."
                ),
                decision_conditions=(
                    "Select and bundle a local neural model artifact under separate ADR",
                    "Pin model version and document reproducibility envelope",
                    "Re-index all persisted bundles on model change",
                    "Run retrieval comparison on representative engineering corpus",
                    "Obtain human Gate-2 amendment before replacing deterministic-only qualification",
                ),
            )

        return EmbeddingEvaluationReport(
            deterministic_metrics=deterministic,
            neural_metrics=neural,
            recommendation=EmbeddingRecommendation.SUPPORT_BOTH_AS_QUALIFIED_CONFIGURATIONS,
            retrieval_comparison_available=True,
            licensing_ip_notes="Requires per-model license review.",
            offline_notes="Local neural path must remain offline after artifact provisioning.",
            decision_conditions=("Human review required for dual-backend qualification.",),
        )

    @staticmethod
    def deterministic_identity() -> EmbeddingModelIdentity:
        return DeterministicLocalEmbeddingBackend().identity
