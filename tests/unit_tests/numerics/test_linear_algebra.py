"""NUM-003 analytic linear systems and independent NumPy algorithm comparisons."""

import math

import numpy as np
import pytest

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.linear_algebra.decomposition import lu, qr
from numerics.linear_algebra.dense_matrix import DenseMatrix
from numerics.linear_algebra.eigenvalues import symmetric_eigensystem
from numerics.linear_algebra.eigenvectors import eigenvectors
from numerics.linear_algebra.matrix_operations import matrix_matrix, matrix_vector
from numerics.linear_algebra.solvers import solve_linear
from numerics.linear_algebra.sparse_matrix import SparseMatrix
from numerics.linear_algebra.vector import Vector
from numerics.utilities.tolerances import Tolerances


@pytest.mark.parametrize("a,x", [
    (np.eye(3), [1, 2, 3]), ([[2, 1], [1, 3]], [2, -1]),
    ([[0, 2, 1], [2, 3, 1], [1, 1, 1]], [1, 2, -3]),
    (np.diag([1e-3, 2, 1e3]), [1, 2, 3]),
])
def test_analytic_systems_and_factorization(a, x):
    a, expected = np.array(a, dtype=float), np.array(x, dtype=float)
    b = a @ expected
    result = solve_linear(a, b)
    np.testing.assert_allclose(result.value, expected, atol=1e-12)
    assert np.linalg.norm(b-a@result.value) <= 1e-10
    assert result.method == "partial-pivot-lu"
    factors = lu(a)
    np.testing.assert_allclose(factors.permutation @ a, factors.lower @ factors.upper, atol=1e-12)
    np.testing.assert_allclose(solve_linear(a, b).value, result.value, rtol=0, atol=0)


@pytest.mark.parametrize("shape", [(3, 2), (2, 3), (4, 4)])
def test_householder_qr_independent_reconstruction(shape):
    a = np.random.default_rng(124).normal(size=shape)
    factors = qr(a)
    np.testing.assert_allclose(factors.orthogonal @ factors.upper, a, atol=1e-12)
    np.testing.assert_allclose(factors.orthogonal.T @ factors.orthogonal, np.eye(shape[0]), atol=1e-12)


@pytest.mark.parametrize("a", [np.eye(3), np.diag([-2, 1, 4]), [[2, 1], [1, 2]],
                             [[3, 1, -1], [1, 4, 2], [-1, 2, 5]]])
def test_symmetric_jacobi_against_analytic_and_numpy(a):
    a = np.array(a, dtype=float)
    result = symmetric_eigensystem(a)
    state = result.value
    np.testing.assert_allclose(state.values, np.linalg.eigvalsh(a), atol=2e-9)
    np.testing.assert_allclose(a @ state.vectors, state.vectors * state.values, atol=2e-9)
    np.testing.assert_allclose(state.vectors.T @ state.vectors, np.eye(len(a)), atol=1e-12)
    np.testing.assert_allclose(eigenvectors(a), state.vectors, rtol=0, atol=0)


def test_hilbert_condition_diagnostics_and_guard():
    a = 1.0/(np.arange(6)[:, None] + np.arange(6)[None, :] + 1)
    result = solve_linear(a, a @ np.ones(6))
    assert float(dict(result.diagnostics)["condition_number"]) > 1e6
    assert result.residual_norm < 1e-10
    with pytest.raises(SolverConvergenceError, match="condition"):
        solve_linear(a, np.ones(6), max_condition=1e5)


@pytest.mark.parametrize("a,b,error", [
    ([[1, 2], [2, 4]], [1, 2], SolverConvergenceError),
    ([[1, 1], [1, 1+1e-16]], [1, 2], SolverConvergenceError),
    ([[1, 2]], [1], InvalidInputError),
    (np.eye(2), [1], InvalidInputError),
    ([[1, math.nan], [0, 1]], [1, 2], InvalidInputError),
    (np.eye(2), [math.inf, 2], InvalidInputError),
])
def test_invalid_and_singular_systems(a, b, error):
    with pytest.raises(error):
        solve_linear(a, b)


def test_symmetric_precondition_and_iteration_exhaustion():
    with pytest.raises(InvalidInputError):
        symmetric_eigensystem([[1, 2], [0, 1]])
    with pytest.raises(SolverConvergenceError, match="MAX_ITERATIONS"):
        symmetric_eigensystem([[3, 1, 2], [1, 2, 1], [2, 1, 4]],
                              policy=Tolerances(max_iterations=1))


def test_immutable_storage_products_and_sparse_contract():
    data = np.eye(2)
    dense = DenseMatrix.from_array(data)
    data[0, 0] = 4
    assert dense.data[0, 0] == 1
    assert not dense.data.flags.writeable
    vector = Vector.from_array([1, 2])
    assert not vector.data.flags.writeable
    np.testing.assert_equal(matrix_vector(dense.data, vector.data), [1, 2])
    np.testing.assert_equal(matrix_matrix(dense.data, dense.data), np.eye(2))
    sparse = SparseMatrix((2, 2), (0, 0, 1), (0, 0, 1), (1., 2., 4.))
    np.testing.assert_equal(sparse.to_dense(), np.diag([3, 4]))
    np.testing.assert_equal(sparse.matvec([2, 3]), [6, 12])
    with pytest.raises(InvalidInputError):
        SparseMatrix((2, 2), (2,), (0,), (1.,))
    with pytest.raises(InvalidInputError):
        matrix_vector(np.eye(2), [1])
