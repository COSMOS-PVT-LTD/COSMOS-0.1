"""
COSMOS Rocket Propulsion Platform

Module: numerics.automatic_differentiation.forward_mode
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral automatic_differentiation.forward_mode foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from core.exceptions import SolverConvergenceError
from numerics.utilities.numerical_checks import (
    FloatArray,
    failure,
    finite,
    invalid,
    same_shape,
    vector,
)


@dataclass(frozen=True, slots=True)
class Dual:
    """Forward-mode first-order dual value with an explicit tangent vector."""
    value: float
    tangent: FloatArray

    def __post_init__(self) -> None:
        object.__setattr__(self,"value",finite(self.value,"dual value"))
        d=vector(self.tangent,"dual tangent")
        d.setflags(write=False)
        object.__setattr__(self,"tangent",d)

    def _coerce(self, other: Dual | float) -> Dual:
        if isinstance(other,Dual):
            same_shape(self.tangent,other.tangent)
            return other
        return Dual(finite(other),np.zeros_like(self.tangent))

    def __add__(self, other: Dual | float) -> Dual:
        b=self._coerce(other)
        return Dual(self.value+b.value,self.tangent+b.tangent)

    def __radd__(self, other: Dual | float) -> Dual:
        return self+other

    def __neg__(self) -> Dual:
        return Dual(-self.value,-self.tangent)

    def __sub__(self, other: Dual | float) -> Dual:
        return self+-self._coerce(other)

    def __rsub__(self, other: Dual | float) -> Dual:
        return self._coerce(other)+-self

    def __mul__(self, other: Dual | float) -> Dual:
        b=self._coerce(other)
        return Dual(self.value*b.value,self.tangent*b.value+b.tangent*self.value)

    def __rmul__(self, other: Dual | float) -> Dual:
        return self*other

    def __truediv__(self, other: Dual | float) -> Dual:
        b=self._coerce(other)
        if b.value==0:
            invalid("Dual division by zero.")
        return Dual(self.value/b.value,(self.tangent-(self.value/b.value)*b.tangent)/b.value)

    def __rtruediv__(self, other: Dual | float) -> Dual:
        return self._coerce(other)/self

    def __pow__(self, exponent: float) -> Dual:
        p=finite(exponent)
        if p==0:
            return Dual(1.,np.zeros_like(self.tangent))
        if (self.value<0 and not p.is_integer()) or (self.value==0 and p<1):
            invalid("Dual real power/derivative is undefined at this value.")
        return Dual(self.value**p,p*self.value**(p-1)*self.tangent)

def sin(value: Dual) -> Dual:
    return Dual(math.sin(value.value),math.cos(value.value)*value.tangent)

def cos(value: Dual) -> Dual:
    return Dual(math.cos(value.value),-math.sin(value.value)*value.tangent)

def exp(value: Dual) -> Dual:
    try:
        result=math.exp(value.value)
    except OverflowError as exc:
        raise SolverConvergenceError("AD exponential overflow.") from exc
    return Dual(result,result*value.tangent)

def log(value: Dual) -> Dual:
    if value.value<=0:
        invalid("Dual logarithm requires positive input.")
    return Dual(math.log(value.value),value.tangent/value.value)

def sqrt(value: Dual) -> Dual:
    return value**.5

ScalarADFunction = Callable[[Dual],Dual | float]

def derivative(function: ScalarADFunction, point: float) -> float:
    """Exact chain-rule tangent propagation, no finite perturbations."""
    try:
        result=function(Dual(point,np.ones(1)))
    except (ArithmeticError,ValueError,TypeError) as exc:
        raise SolverConvergenceError("AD callback failed.") from exc
    if isinstance(result,Dual):
        if result.tangent.shape!=(1,):
            failure("Scalar AD callback returned incompatible tangent.")
        return float(result.tangent[0])
    finite(result,"constant AD output")
    return 0.
