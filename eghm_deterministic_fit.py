#!/usr/bin/env python3
"""Deterministic small constrained least-squares solvers for EGHM.

The model has only six mapped pond-area targets and at most two linear
observation-operator coefficients. Using a general LAPACK least-squares routine
is unnecessary and introduced avoidable cross-run numerical variation. These
solvers enumerate the feasible 1-D/2-D box/nonnegative boundaries and solve the
interior normal equations using 80-digit Decimal arithmetic constructed exactly
from the input float values.

No scientific parameter, objective, or constraint is changed.
"""
from __future__ import annotations
from decimal import Decimal, localcontext
from typing import Iterable, List, Sequence, Tuple
import numpy as np


def D(x):
    return Decimal.from_float(float(x))


def dot(a,b):
    return sum((D(x)*D(y) for x,y in zip(a,b)),Decimal(0))


def decimal_sse(X,target,b):
    X=np.asarray(X,float); target=np.asarray(target,float)
    return sum((D(target[i])-sum(D(X[i,j])*D(b[j]) for j in range(X.shape[1])))**2 for i in range(X.shape[0]))


def fit_nonnegative(X,target,upper_first=None):
    """Deterministic constrained LS for one or two coefficients.

    Constraints: all coefficients >=0; optionally coefficient 0 <= upper_first.
    Returns a float NumPy coefficient vector.
    """
    X=np.asarray(X,float); target=np.asarray(target,float)
    if X.ndim==1: X=X[:,None]
    n=X.shape[1]; cand=[]
    with localcontext() as ctx:
        ctx.prec=80
        if n==1:
            a=dot(X[:,0],X[:,0]); d=dot(X[:,0],target)
            z=Decimal(0) if a==0 else max(Decimal(0),d/a)
            if upper_first is not None: z=min(z,D(upper_first))
            cand=[np.array([float(z)]),np.array([0.0])]
        elif n==2:
            a=dot(X[:,0],X[:,0]); b=dot(X[:,0],X[:,1]); c=dot(X[:,1],X[:,1])
            d=dot(X[:,0],target); e=dot(X[:,1],target); det=a*c-b*b
            if det!=0:
                z0=(d*c-b*e)/det; z1=(a*e-b*d)/det
                if z0>=0 and z1>=0 and (upper_first is None or z0<=D(upper_first)):
                    cand.append(np.array([float(z0),float(z1)]))
            z0=Decimal(0) if a==0 else max(Decimal(0),d/a)
            if upper_first is not None: z0=min(z0,D(upper_first))
            cand.append(np.array([float(z0),0.0]))
            z1=Decimal(0) if c==0 else max(Decimal(0),e/c)
            cand.append(np.array([0.0,float(z1)]));cand.append(np.array([0.0,0.0]))
            if upper_first is not None:
                u=D(upper_first)
                rhs=[D(target[i])-u*D(X[i,0]) for i in range(len(target))]
                num=sum((D(X[i,1])*rhs[i] for i in range(len(target))),Decimal(0))
                z1=Decimal(0) if c==0 else max(Decimal(0),num/c)
                cand.append(np.array([float(u),float(z1)]))
        else:
            raise ValueError('Only one or two coefficients are supported')
    return min(cand,key=lambda q:decimal_sse(X,target,q))


def fit_constrained_state(S,H,y,A0):
    """Legacy-compatible deterministic EGHM fit: yhat=A0-Kc*S+Kh*H."""
    S=np.asarray(S,float); H=np.asarray(H,float); y=np.asarray(y,float)
    X=np.c_[-S,H]
    b=fit_nonnegative(X,y-float(A0),upper_first=float(A0))
    return b,float(A0)+X@b


def _sse_state_decimal(
    S: Sequence[Decimal], H: Sequence[Decimal], target: Sequence[Decimal],
    kc: Decimal, kh: Decimal,
) -> Decimal:
    return sum(
        (target[i] - ((-S[i]) * kc + H[i] * kh)) ** 2
        for i in range(len(target))
    )


def fit_constrained_state_fixed(
    S: Sequence[float], H: Sequence[float], y: Sequence[float], A0: float,
) -> Tuple[Tuple[float, float], List[float]]:
    """Pure fixed-order Decimal fit for y=A0-Kc*S+Kh*H.

    Constraints are exactly 0<=Kc<=A0 and Kh>=0.  The feasible interior and
    all relevant box/nonnegative boundaries are enumerated.  No NumPy ufunc,
    BLAS, matrix multiply, or platform least-squares implementation is used in
    the fitted coefficients or predictions.
    """
    if not (len(S) == len(H) == len(y)):
        raise ValueError('S, H and y must have equal lengths')
    if len(S) == 0:
        raise ValueError('at least one observation is required')

    with localcontext() as ctx:
        ctx.prec = 80
        sd = [D(v) for v in S]
        hd = [D(v) for v in H]
        a0 = D(A0)
        td = [D(v) - a0 for v in y]

        # Basis columns are x0=-S (coefficient Kc) and x1=H (coefficient Kh).
        x0 = [-v for v in sd]
        x1 = hd
        aa = sum((v*v for v in x0), Decimal(0))
        bb = sum((x0[i]*x1[i] for i in range(len(x0))), Decimal(0))
        cc = sum((v*v for v in x1), Decimal(0))
        dd = sum((x0[i]*td[i] for i in range(len(x0))), Decimal(0))
        ee = sum((x1[i]*td[i] for i in range(len(x0))), Decimal(0))
        det = aa*cc - bb*bb

        candidates: List[Tuple[Decimal, Decimal]] = []

        # Interior.
        if det != 0:
            kc = (dd*cc - bb*ee) / det
            kh = (aa*ee - bb*dd) / det
            if Decimal(0) <= kc <= a0 and kh >= 0:
                candidates.append((kc, kh))

        # Kh=0 boundary.
        kc = Decimal(0) if aa == 0 else dd/aa
        kc = min(a0, max(Decimal(0), kc))
        candidates.append((kc, Decimal(0)))

        # Kc=0 boundary.
        kh = Decimal(0) if cc == 0 else max(Decimal(0), ee/cc)
        candidates.append((Decimal(0), kh))

        # Kc=A0 boundary.
        rhs = [td[i] - x0[i]*a0 for i in range(len(td))]
        num = sum((x1[i]*rhs[i] for i in range(len(td))), Decimal(0))
        kh = Decimal(0) if cc == 0 else max(Decimal(0), num/cc)
        candidates.append((a0, kh))

        # Origin.
        candidates.append((Decimal(0), Decimal(0)))

        kc, kh = min(candidates, key=lambda z: _sse_state_decimal(sd, hd, td, z[0], z[1]))
        pred_d = [a0 - kc*sd[i] + kh*hd[i] for i in range(len(sd))]
        return (float(kc), float(kh)), [float(v) for v in pred_d]
