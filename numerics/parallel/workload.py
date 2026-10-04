"""
COSMOS Rocket Propulsion Platform

Module: numerics.parallel.workload
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral parallel.workload foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Generic, TypeVar

from numerics.random.seeds import child_seeds
from numerics.utilities.numerical_checks import count, invalid

InputType = TypeVar("InputType")
OutputType = TypeVar("OutputType")


def workers(value: int) -> int:
    n = count(value, "workers")
    if n > 32:
        invalid("Foundation worker count is bounded to <=32.")
    return n


def bounded_items(items: Iterable[InputType], max_jobs: int) -> list[InputType]:
    limit = count(max_jobs, "max_jobs")
    result: list[InputType] = []
    for item in items:
        if len(result) >= limit:
            invalid("Workload exceeds explicit max_jobs bound.")
        result.append(item)
    return result


@dataclass(frozen=True, slots=True)
class SeededJob(Generic[InputType]):
    payload: InputType
    seed: int


def seeded_jobs(
    items: Iterable[InputType], *, seed: int, max_jobs: int = 10000
) -> tuple[SeededJob[InputType], ...]:
    data = bounded_items(items, max_jobs)
    if not data:
        from numerics.random.seeds import validate

        validate(seed)
        return ()
    seeds = child_seeds(seed, len(data))
    return tuple(
        SeededJob(item, child) for item, child in zip(data, seeds, strict=True)
    )
