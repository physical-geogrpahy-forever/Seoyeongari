#!/usr/bin/env python3
"""Deterministic storage-area geometry for EGHM.

The accepted EGHM p_shape grid is {6, 12, 18}. Therefore

    A(V) = A0 * (V/V0) ** (2/(p+2))

uses the exact rational exponents 1/4, 1/7 and 1/10.  Calling the platform
libm fractional-power routine is unnecessary and produced two reproducible
last-bit trajectories on heterogeneous GitHub runners after thousands of daily
feedback steps.

This module evaluates those *same mathematical powers* as integer n-th roots
using only IEEE-754 basic arithmetic plus frexp/ldexp scaling.  The Newton loop
has a fixed iteration count: there is no data-dependent tolerance, fitted
constant, rounding lattice, or scientific parameter change.
"""
from __future__ import annotations

import math

A0_DEFAULT = 2241.762
A_WET_DEFAULT = 5939.5
NEWTON_ITERATIONS = 12


def _pow_nm1(y: float, n: int) -> float:
    """Return y**(n-1) using an explicit fixed multiplication graph."""
    y2 = y * y
    if n == 4:       # y^3
        return y2 * y
    if n == 7:       # y^6
        y4 = y2 * y2
        return y4 * y2
    if n == 10:      # y^9
        y4 = y2 * y2
        y8 = y4 * y4
        return y8 * y
    raise ValueError(f'unsupported root degree: {n}')


def nth_root_ieee(x: float, n: int) -> float:
    """Deterministic positive n-th root for n in {4,7,10}.

    x=m*2**e from frexp.  Write e=q*n+r with 0<=r<n, so only the bounded
    mantissa z=m*2**r is iterated.  Its n-th root is always between about 0.9
    and 2 for the supported n, making a fixed 12 Newton steps ample for binary64.
    """
    x = float(x)
    if x < 0.0:
        raise ValueError('nth_root_ieee requires x >= 0')
    if x == 0.0:
        return 0.0
    if not math.isfinite(x):
        return x
    if n not in (4, 7, 10):
        raise ValueError(f'unsupported root degree: {n}')

    m, e = math.frexp(x)  # exact binary decomposition: x=m*2**e
    q, r = divmod(e, n)
    z = math.ldexp(m, r)  # exact power-of-two scaling
    y = 1.0 if z <= 1.0 else 2.0

    nf = float(n)
    nm1 = float(n - 1)
    for _ in range(NEWTON_ITERATIONS):
        ynm1 = _pow_nm1(y, n)
        y = (nm1 * y + z / ynm1) / nf
    return math.ldexp(y, q)


def root_degree_from_p(p_shape: float) -> int:
    p = float(p_shape)
    if p == 6.0:
        return 4
    if p == 12.0:
        return 7
    if p == 18.0:
        return 10
    raise ValueError(
        f'deterministic geometry is defined for the accepted p_shape grid '
        f'{{6,12,18}}; got {p_shape!r}'
    )


def area_v_deterministic(
    v: float,
    V0: float,
    p_shape: float,
    A0: float = A0_DEFAULT,
    A_WET: float = A_WET_DEFAULT,
) -> float:
    """Same EGHM storage-area equation without a general fractional pow call."""
    v = float(v)
    if v <= 0.0:
        return 0.0
    n = root_degree_from_p(p_shape)
    a = float(A0) * nth_root_ieee(v / float(V0), n)
    return min(float(A_WET), a)
