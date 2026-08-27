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
            cand.append(np.array([0.0,float(z1)]))
            if upper_first is not None:
                u=D(upper_first)
                rhs=[D(target[i])-u*D(X[i,0]) for i in range(len(target))]
                num=sum((D(X[i,1])*rhs[i] for i in range(len(target))),Decimal(0))
                z1=Decimal(0) if c==0 else max(Decimal(0),num/c)
                cand.append(np.array([float(u),float(z1)]))
            cand.append(np.array([0.0,0.0]))
        else:
            raise ValueError('Only one or two coefficients are supported')
    return min(cand,key=lambda q:decimal_sse(X,target,q))


def fit_constrained_state(S,H,y,A0):
    """EGHM hydrosere operator: yhat=A0-Kc*S+Kh*H."""
    S=np.asarray(S,float); H=np.asarray(H,float); y=np.asarray(y,float)
    X=np.c_[-S,H]
    b=fit_nonnegative(X,y-float(A0),upper_first=float(A0))
    return b,float(A0)+X@b
