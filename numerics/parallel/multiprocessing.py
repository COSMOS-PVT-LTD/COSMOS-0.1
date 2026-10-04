"""
COSMOS Rocket Propulsion Platform

Module: numerics.parallel.multiprocessing
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral parallel.multiprocessing foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import multiprocessing as mp
from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor

from numerics.parallel.workload import InputType, OutputType, bounded_items, workers


def map_ordered(function: Callable[[InputType],OutputType], items: Iterable[InputType], *,
                worker_count: int, max_jobs: int = 10000) -> tuple[OutputType,...]:
    """Spawn-only bounded jobs; callback must be importable/pickleable, caller main guarded."""
    n=workers(worker_count)
    data=bounded_items(items,max_jobs)
    pool=ProcessPoolExecutor(max_workers=n,mp_context=mp.get_context("spawn"))
    try:
        futures=[pool.submit(function,item) for item in data]
        return tuple(future.result() for future in futures)
    finally:
        pool.shutdown(wait=True,cancel_futures=True)
