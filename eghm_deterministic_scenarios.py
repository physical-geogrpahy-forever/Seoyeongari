#!/usr/bin/env python3
"""Deterministic four-scenario utilities for Seoyeongari EGHM."""
from __future__ import annotations

from decimal import Decimal, localcontext
from typing import Dict, List, Mapping, Sequence, Tuple

import pandas as pd

from eghm_deterministic_fit import D
from eghm_deterministic_geometry import (
    area_h_deterministic,
    area_v_deterministic,
    depth_v_deterministic,
    reference_depth,
)
from eghm_deterministic_kernel import A0, A_WET


def _sse(target: Sequence[Decimal], x0: Sequence[Decimal], x1: Sequence[Decimal], b0: Decimal, b1: Decimal) -> Decimal:
    return sum((target[i] - x0[i]*b0 - x1[i]*b1) ** 2 for i in range(len(target)))


def fit_two_nonnegative_fixed(
    x0: Sequence[float], x1: Sequence[float], target: Sequence[float], upper_first: float | None = None,
) -> Tuple[float, float]:
    """Fixed-order 80-digit two-basis LS; b0,b1>=0 and optional b0 upper bound."""
    if not (len(x0) == len(x1) == len(target)) or not x0:
        raise ValueError('basis/target lengths must be equal and nonzero')
    with localcontext() as ctx:
        ctx.prec = 80
        a0 = [D(v) for v in x0]; a1 = [D(v) for v in x1]; t = [D(v) for v in target]
        aa = sum((v*v for v in a0), Decimal(0))
        ab = sum((a0[i]*a1[i] for i in range(len(t))), Decimal(0))
        bb = sum((v*v for v in a1), Decimal(0))
        da = sum((a0[i]*t[i] for i in range(len(t))), Decimal(0))
        db = sum((a1[i]*t[i] for i in range(len(t))), Decimal(0))
        det = aa*bb - ab*ab
        upper = None if upper_first is None else D(upper_first)
        cand: List[Tuple[Decimal, Decimal]] = []
        if det != 0:
            b0 = (da*bb - ab*db) / det
            b1 = (aa*db - ab*da) / det
            if b0 >= 0 and b1 >= 0 and (upper is None or b0 <= upper):
                cand.append((b0,b1))
        b0 = Decimal(0) if aa == 0 else max(Decimal(0), da/aa)
        if upper is not None: b0 = min(upper,b0)
        cand.append((b0,Decimal(0)))
        b1 = Decimal(0) if bb == 0 else max(Decimal(0), db/bb)
        cand.append((Decimal(0),b1))
        if upper is not None:
            rhs = [t[i]-a0[i]*upper for i in range(len(t))]
            num = sum((a1[i]*rhs[i] for i in range(len(t))),Decimal(0))
            b1 = Decimal(0) if bb == 0 else max(Decimal(0),num/bb)
            cand.append((upper,b1))
        cand.append((Decimal(0),Decimal(0)))
        best=min(cand,key=lambda z:_sse(t,a0,a1,z[0],z[1]))
        return float(best[0]),float(best[1])


def fit_one_nonnegative_fixed(x: Sequence[float], target: Sequence[float]) -> float:
    if len(x) != len(target) or not x:
        raise ValueError('basis/target lengths must be equal and nonzero')
    with localcontext() as ctx:
        ctx.prec=80
        xd=[D(v) for v in x]; td=[D(v) for v in target]
        xx=sum((v*v for v in xd),Decimal(0)); xt=sum((xd[i]*td[i] for i in range(len(td))),Decimal(0))
        b=Decimal(0) if xx == 0 else max(Decimal(0),xt/xx)
        return float(b)


def predict_fixed(offset: Sequence[float], x0: Sequence[float], b0: float, x1: Sequence[float] | None = None, b1: float = 0.0) -> List[float]:
    with localcontext() as ctx:
        ctx.prec=80
        bd0=D(b0); bd1=D(b1)
        out=[]
        for i in range(len(offset)):
            v=D(offset[i])+D(x0[i])*bd0
            if x1 is not None: v += D(x1[i])*bd1
            out.append(float(v))
        return out


def metrics_fixed(pred: Sequence[float], obs: Sequence[float]) -> Dict[str,float]:
    with localcontext() as ctx:
        ctx.prec=80
        pd=[D(v) for v in pred]; od=[D(v) for v in obs]; n=Decimal(len(pd))
        sse=sum(((pd[i]-od[i])**2 for i in range(len(pd))),Decimal(0))
        rm=(sse/n).sqrt(); mean=sum(od,Decimal(0))/n
        return {'RMSE_m2':float(rm),'nRMSE_pct':float(Decimal(100)*rm/mean)}


def peat_geomorphic_loss(
    dates: Sequence[object], V: Sequence[float], rate_mm_yr: float,
    V0: float, p_shape: float,
) -> Tuple[List[float], float, List[float]]:
    """Daily surface-expression loss G=A_hyd-A_peat under persistent peat rise.

    Water storage is not removed. Peat rise changes only the surface-expression
    geometry, matching Stage50/51/57 science but without fractional libm powers.
    """
    dt=pd.to_datetime(dates)
    h0=reference_depth(V0,p_shape,A0=A0)
    origin=pd.Timestamp('2011-01-01')
    G=[]; B=[]
    for stamp,vraw in zip(dt,V):
        v=float(vraw)
        elapsed=max((stamp-origin).days/365.2425,0.0)
        b=float(rate_mm_yr)/1000.0*elapsed
        ah=area_v_deterministic(v,V0,p_shape,A0=A0,A_WET=A_WET)
        h=depth_v_deterministic(v,V0,p_shape,A0=A0)
        hres=max(h-b,0.0)
        ap=area_h_deterministic(hres,h0,p_shape,A0=A0,A_WET=A_WET)
        G.append(max(ah-ap,0.0)); B.append(b)
    return G,h0,B


def fit_four_scenarios(S: Sequence[float],H: Sequence[float],G: Sequence[float],obs: Sequence[float],a0: float=A0) -> List[Dict[str,object]]:
    S=[float(v) for v in S]; H=[float(v) for v in H]; G=[float(v) for v in G]; y=[float(v) for v in obs]
    base=[float(a0)]*len(y)
    geom=[float(a0)-G[i] for i in range(len(y))]
    negS=[-v for v in S]
    rows=[]

    kh=fit_one_nonnegative_fixed(H,[y[i]-base[i] for i in range(len(y))])
    pred=predict_fixed(base,H,kh); rows.append({'Scenario':'Baseline Model','K_colonizable_m2':0.0,'K_hydro_m2_per_m3':kh,'pred':pred,**metrics_fixed(pred,y)})

    kc,kh=fit_two_nonnegative_fixed(negS,H,[y[i]-base[i] for i in range(len(y))],upper_first=a0)
    pred=predict_fixed(base,negS,kc,H,kh); rows.append({'Scenario':'Hydrosere Only Model','K_colonizable_m2':kc,'K_hydro_m2_per_m3':kh,'pred':pred,**metrics_fixed(pred,y)})

    kh=fit_one_nonnegative_fixed(H,[y[i]-geom[i] for i in range(len(y))])
    pred=predict_fixed(geom,H,kh); rows.append({'Scenario':'Eco-Geo Only Model','K_colonizable_m2':0.0,'K_hydro_m2_per_m3':kh,'pred':pred,**metrics_fixed(pred,y)})

    kc,kh=fit_two_nonnegative_fixed(negS,H,[y[i]-geom[i] for i in range(len(y))],upper_first=a0)
    pred=predict_fixed(geom,negS,kc,H,kh); rows.append({'Scenario':'Integrated Model','K_colonizable_m2':kc,'K_hydro_m2_per_m3':kh,'pred':pred,**metrics_fixed(pred,y)})
    return rows
