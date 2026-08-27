#!/usr/bin/env python3
"""Deterministic power-law geometry for EGHM.

For the accepted p_shape grid {6,12,18}, every geometry exponent used by the
model is an exact small rational power:

  A(V): exponent 2/(p+2) -> 1/4, 1/7, 1/10
  h(V): exponent p/(p+2) -> 3/4, 6/7, 9/10
  A(h): exponent 2/p     -> 1/3, 1/6, 1/9

Calling platform fractional-power routines is therefore unnecessary. This
module evaluates the same mathematical relations with fixed-iteration integer
roots using IEEE-754 basic arithmetic plus exact frexp/ldexp scaling. No fitted
constant, rounding lattice, tolerance search, or scientific equation change is
introduced.
"""
from __future__ import annotations

import math

A0_DEFAULT = 2241.762
A_WET_DEFAULT = 5939.5
NEWTON_ITERATIONS = 12
SUPPORTED_ROOTS = (3, 4, 6, 7, 9, 10)


def _pow_nm1(y: float, n: int) -> float:
    """Return y**(n-1) using an explicit fixed multiplication graph."""
    y2 = y * y
    if n == 3:       # y^2
        return y2
    if n == 4:       # y^3
        return y2 * y
    y4 = y2 * y2
    if n == 6:       # y^5
        return y4 * y
    if n == 7:       # y^6
        return y4 * y2
    y8 = y4 * y4
    if n == 9:       # y^8
        return y8
    if n == 10:      # y^9
        return y8 * y
    raise ValueError(f'unsupported root degree: {n}')


def nth_root_ieee(x: float, n: int) -> float:
    """Deterministic positive n-th root for the small supported root degrees."""
    x = float(x)
    if x < 0.0:
        raise ValueError('nth_root_ieee requires x >= 0')
    if x == 0.0:
        return 0.0
    if not math.isfinite(x):
        return x
    if n not in SUPPORTED_ROOTS:
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
    """Root degree for A(V), i.e. exponent 2/(p+2)."""
    p = float(p_shape)
    if p == 6.0:
        return 4
    if p == 12.0:
        return 7
    if p == 18.0:
        return 10
    raise ValueError(
        f'deterministic geometry is defined for p_shape {{6,12,18}}; got {p_shape!r}'
    )


def depth_root_degree_from_p(p_shape: float) -> int:
    """Root degree for A(h), i.e. exponent 2/p."""
    p = float(p_shape)
    if p == 6.0:
        return 3
    if p == 12.0:
        return 6
    if p == 18.0:
        return 9
    raise ValueError(
        f'deterministic geometry is defined for p_shape {{6,12,18}}; got {p_shape!r}'
    )


def reference_depth(V0: float, p_shape: float, A0: float = A0_DEFAULT) -> float:
    """h0 implied by the accepted power-law hypsometry."""
    p = float(p_shape)
    return float(V0) * (p + 2.0) / (float(A0) * p)


def area_v_deterministic(
    v: float,
    V0: float,
    p_shape: float,
    A0: float = A0_DEFAULT,
    A_WET: float = A_WET_DEFAULT,
) -> float:
    """A(V)=A0*(V/V0)^(2/(p+2)), evaluated without fractional libm pow."""
    v = float(v)
    if v <= 0.0:
        return 0.0
    n = root_degree_from_p(p_shape)
    a = float(A0) * nth_root_ieee(v / float(V0), n)
    return min(float(A_WET), a)


def depth_v_deterministic(
    v: float,
    V0: float,
    p_shape: float,
    A0: float = A0_DEFAULT,
) -> float:
    """h(V)=h0*(V/V0)^(p/(p+2)) via the same root used by A(V)."""
    v = float(v)
    if v <= 0.0:
        return 0.0
    n = root_degree_from_p(p_shape)
    root = nth_root_ieee(v / float(V0), n)
    return reference_depth(V0, p_shape, A0=A0) * _pow_nm1(root, n)


def area_h_deterministic(
    h: float,
    h0: float,
    p_shape: float,
    A0: float = A0_DEFAULT,
    A_WET: float = A_WET_DEFAULT,
) -> float:
    """A(h)=A0*(h/h0)^(2/p), evaluated as a 3rd/6th/9th root."""
    h = float(h)
    if h <= 0.0:
        return 0.0
    n = depth_root_degree_from_p(p_shape)
    a = float(A0) * nth_root_ieee(h / float(h0), n)
    return min(float(A_WET), a)
