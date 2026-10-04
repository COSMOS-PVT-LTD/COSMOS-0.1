"""
COSMOS Rocket Propulsion Platform

Module: numerics.linear_algebra.dense_matrix
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral dense_matrix foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numerics.linear_algebra.matrix import Matrix

# Dense storage uses the single validated Matrix contract, not another backend.
DenseMatrix = Matrix
__all__ = ("DenseMatrix",)
