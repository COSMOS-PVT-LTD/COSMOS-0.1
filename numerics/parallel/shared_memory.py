"""
COSMOS Rocket Propulsion Platform

Module: numerics.parallel.shared_memory
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral parallel.shared_memory foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from multiprocessing.shared_memory import SharedMemory

import numpy as np
from numpy.typing import ArrayLike

from numerics.utilities.numerical_checks import FloatArray, vector


@dataclass(frozen=True, slots=True)
class SharedVector:
    """Borrowed array view valid only inside the owner's context; not retained afterward."""

    name: str
    values: FloatArray


@contextmanager
def shared_vector(values: ArrayLike) -> Iterator[SharedVector]:
    """Create, initialize, and always close/unlink a real float64 shared-memory segment."""
    data = vector(values)
    handle = SharedMemory(create=True, size=data.nbytes)
    try:
        view: FloatArray = np.ndarray(data.shape, dtype=np.float64, buffer=handle.buf)
        view[:] = data
        yield SharedVector(handle.name, view)
    finally:
        handle.close()
        handle.unlink()
