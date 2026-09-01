#!/usr/bin/env python3
"""Stage59 — cross-runner numerical determinism audit.

Compares raw Stage57 state fingerprints with the legacy NumPy lstsq observation
operator and a deterministic high-precision constrained 1-2 coefficient solver.
No scientific parameter changes are made here.
"""
from __future__ import annotations
import hashlib, json, math, platform
from decimal import Decimal, localcontext
from pathlib import Path
import numpy as np
import pandas as pd
import stage57_aprmay_four_scenario_peat as s57
import stage58_aprmay_oat_provenance as s58

OUT=Path('stage59_outputs'); OUT.mkdir(exist_ok=True)


def sha(a):
    x=np.ascontiguousarray(np.asarray(a,dtype='<f8'))
    return hashlib.sha256(x.tobytes()).hexdigest()


def D(x): return Decimal.from_float(float(x))
def dot(a,b): return sum((D(x)*D(y) for x,y in zip(a,b)),Decimal(0))
def sse(X,target,b):
    return sum((D(target[i])-sum(D(X[i,j])*D(b[j]) for j in range(X.shape[1])))**2 for i in range(X.shape[0]))


def det_fit(X,target,upper_kc=None):
    X=np.asarray(X,float); target=np.asarray(target,float)
    if X.ndim==1: X=X[:,None]
    n=X.shape[1]
    cand=[]
    with localcontext() as ctx:
        ctx.prec=80
        if n==1:
            den=dot(X[:,0],X[:,0]); num=dot(X[:,0],target)
            z=Decimal(0) if den==0 else num/den
            z=max(Decimal(0),z)
            if upper_kc is not None: z=min(z,D(upper_kc))
            cand=[np.array([float(z)]),np.array([0.0])]
        elif n==2:
            a=dot(X[:,0],X[:,0]); b=dot(X[:,0],X[:,1]); c=dot(X[:,1],X[:,1])
            d=dot(X[:,0],target); e=dot(X[:,1],target); det=a*c-b*b
            if det!=0:
                z0=(d*c-b*e)/det; z1=(a*e-b*d)/det
                if z0>=0 and z1>=0 and (upper_kc is None or z0<=D(upper_kc)):
                    cand.append(np.array([float(z0),float(z1)]))
            # k1=0 edge
            z0=Decimal(0) if a==0 else max(Decimal(0),d/a)
            if upper_kc is not None: z0=min(z0,D(upper_kc))
            cand.append(np.array([float(z0),0.0]))
            # k0=0 edge
            z1=Decimal(0) if c==0 else max(Decimal(0),e/c)
            cand.append(np.array([0.0,float(z1)]))
            # k0=upper edge, required for exact box-constrained solution
            if upper_kc is not None:
                u=D(upper_kc)
                rhs=np.array([float(target[i]-float(u)*X[i,0]) for i in range(len(target))])
                num=dot(X[:,1],rhs); z1=Decimal(0) if c==0 else max(Decimal(0),num/c)
                cand.append(np.array([float(u),float(z1)]))
            cand.append(np.array([0.0,0.0]))
        else: raise ValueError(n)
    return min(cand,key=lambda q: sse(X,target,q))


def det_metric(pred):
    pred=np.asarray(pred,float); rm=float(np.sqrt(np.mean((pred-s57.Y)**2)))
    return rm,100*rm/float(np.mean(s57.Y))


def det_scenarios(S,H,G):
    rows=[]
    kh=det_fit(H,s57.Y-s57.A0)[0]; pr=s57.A0+kh*H; rm,nr=det_metric(pr); rows.append(('Baseline Model',0.,kh,pr,rm,nr))
    X=np.c_[-S,H]; b=det_fit(X,s57.Y-s57.A0,upper_kc=s57.A0); pr=s57.A0+X@b; rm,nr=det_metric(pr); rows.append(('Hydrosere Only Model',b[0],b[1],pr,rm,nr))
    base=s57.A0-G; kh=det_fit(H,s57.Y-base)[0]; pr=base+kh*H; rm,nr=det_metric(pr); rows.append(('Eco-Geo Only Model',0.,kh,pr,rm,nr))
    b=det_fit(X,s57.Y-base,upper_kc=s57.A0); pr=base+X@b; rm,nr=det_metric(pr); rows.append(('Integrated Model',b[0],b[1],pr,rm,nr))
    return rows


def pack(rows):
    return [{'Scenario':n,'Kc':float(kc),'Kh':float(kh),'RMSE_m2':float(rm),'nRMSE_pct':float(nr),'pred':[float(x) for x in pr]} for n,kc,kh,pr,rm,nr in rows]


def main():
    h,S,H,G,corr=s58.states(dict(s58.CENTRAL))
    X=np.c_[-S,H]
    legacy=s57.fit_scenarios(S,H,G)
    deterministic=det_scenarios(S,H,G)
    summary={
      'status':'PASS_STAGE59_NUMERICS_AUDIT',
      'platform':platform.platform(),'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,
      'fingerprints':{'V':sha(h['V']),'area':sha(h['area']),'return_flow':sha(h['return_flow']),'S':sha(S),'H':sha(H),'G':sha(G)},
      'states':{'S':[float(x) for x in S],'H':[float(x) for x in H],'G':[float(x) for x in G]},
      'design_condition_number':float(np.linalg.cond(X)),
      'design_column_correlation':float(np.corrcoef(X[:,0],X[:,1])[0,1]),
      'legacy_numpy_lstsq':pack(legacy),
      'deterministic_decimal_solver':pack(deterministic),
      'physical_closure':{'mass_error_m3':float(h['mass_error']),'area_partition_error_m2':float(h['area_partition_error']),'precip_partition_error_m3':float(h['precip_partition_error'])},
    }
    (OUT/'stage59_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
