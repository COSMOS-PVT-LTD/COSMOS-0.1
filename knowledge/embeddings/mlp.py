"""Pure-Python MLP for local neural embedding inference."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

__all__ = ("MLPWeights", "mlp_forward", "seeded_mlp_weights")


def _relu(value: float) -> float:
    return value if value > 0.0 else 0.0


@dataclass(frozen=True, slots=True)
class MLPWeights:
    """Frozen MLP weight matrices for local inference."""

    input_dim: int
    hidden_dim: int
    output_dim: int
    w1: tuple[tuple[float, ...], ...]
    b1: tuple[float, ...]
    w2: tuple[tuple[float, ...], ...]
    b2: tuple[float, ...]


def seeded_mlp_weights(
    *,
    seed: str,
    input_dim: int,
    hidden_dim: int,
    output_dim: int,
) -> MLPWeights:
    """Generate deterministic pseudo-random MLP weights from a seed string."""

    def _matrix(rows: int, cols: int, tag: str) -> tuple[tuple[float, ...], ...]:
        matrix: list[tuple[float, ...]] = []

        for row in range(rows):
            row_values: list[float] = []

            for col in range(cols):
                digest = hashlib.sha256(f"{seed}:{tag}:{row}:{col}".encode()).digest()
                raw = int.from_bytes(digest[:4], "big") / 2**32
                row_values.append((raw * 2.0) - 1.0)

            matrix.append(tuple(row_values))

        return tuple(matrix)

    def _vector(length: int, tag: str) -> tuple[float, ...]:
        return tuple(
            (int.from_bytes(
                hashlib.sha256(f"{seed}:{tag}:{index}".encode()).digest()[:4],
                "big",
            ) / 2**32)
            * 2.0
            - 1.0
            for index in range(length)
        )

    return MLPWeights(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        output_dim=output_dim,
        w1=_matrix(hidden_dim, input_dim, "w1"),
        b1=_vector(hidden_dim, "b1"),
        w2=_matrix(output_dim, hidden_dim, "w2"),
        b2=_vector(output_dim, "b2"),
    )


def mlp_forward(features: list[float], weights: MLPWeights) -> tuple[float, ...]:
    """Run a 2-layer ReLU MLP and L2-normalize the output."""

    hidden = [
        _relu(
            sum(weights.w1[row][col] * features[col] for col in range(weights.input_dim))
            + weights.b1[row],
        )
        for row in range(weights.hidden_dim)
    ]

    output = [
        sum(weights.w2[row][col] * hidden[col] for col in range(weights.hidden_dim))
        + weights.b2[row]
        for row in range(weights.output_dim)
    ]

    norm = math.sqrt(sum(value * value for value in output))

    if norm == 0.0:
        return tuple(output)

    return tuple(value / norm for value in output)
