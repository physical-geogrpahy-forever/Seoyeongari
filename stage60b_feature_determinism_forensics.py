#!/usr/bin/env python3
"""Stage60b — locate the first cross-run divergence in the selected Stage60 path.

No calibration and no model change. One locked central process setting is run and
fingerprinted after forcing, hydrology, exposure, rolling minimum, ecological
cumprod, April-May aggregation, and antecedent-flow aggregation. For each
reduction/rolling operation a simple fixed-order Python implementation is also
computed as a numerical-control path.
"""
from __future__ import annotations
import hashlib, json, math, os, platform
from pathlib import Path
import numpy as np
import pandas as pd

from stage31_topmodel_vsa import forcing
from stage38_domain_corrected import hydro
from stage35c_mass_balance_state_operator import A0
from stage49_six_observation_irreversible_recruitment import YEARS

OUT=Path('stage60b_outputs'); OUT.mkdir(exist_ok=True)
P={'V0':1000.0,'p_shape':18.0,'tau_surf':60.0,'local_frac':0.45,'tau_fast':30.0,'k_gw_mm_d':4.0}
R_EST=0.05; EST_W=7; HYDRO_W=14; MONTHS=(4,5)


def sha(a):
    x=np.ascontiguousarray(np.asarray(a,dtype='<f8'))
    return hashlib.sha256(x.tobytes()).hexdigest()


def hx(a): return [float(x).hex() for x in np.asarray(a,float)]

def maxabs(a,b): return float(np.max(np.abs(np.asarray(a,float)-np.asarray(b,float))))


def scalar_roll_min(x,w):
    x=np.asarray(x,float); out=np.zeros(len(x),float)
    for i in range(w-1,len(x)):
        m=float(x[i-w+1])
        for j in range(i-w+2,i+1):
            v=float(x[j])
            if v<m: m=v
        out[i]=m
    return out


def sequential_state(exposure,r):
    a=float(r)/365.0; prod=1.0; out=np.empty(len(exposure),float)
    for i,e in enumerate(np.asarray(exposure,float)):
        q=1.0-a*float(e)
        if q<0.0:q=0.0
        elif q>1.0:q=1.0
        prod=prod*q
        out[i]=1.0-prod
    return out


def fsum_window_means(dt,x,months=MONTHS):
    dt=pd.to_datetime(dt); x=np.asarray(x,float)
    yr=dt.year.to_numpy(); mo=dt.month.to_numpy()
    ans=[]
    for y in YEARS:
        vals=[float(x[i]) for i in range(len(x)) if yr[i]==y and int(mo[i]) in months]
        ans.append(math.fsum(vals)/len(vals))
    return np.asarray(ans,float)


def deterministic_roll_sum(x,w):
    x=np.asarray(x,float); out=np.empty(len(x),float)
    for i in range(len(x)):
        j=max(0,i-int(w)+1)
        out[i]=math.fsum(float(v) for v in x[j:i+1])
    return out


def deterministic_h_feature(dt,q,w):
    dt=pd.to_datetime(dt); rr=deterministic_roll_sum(q,w)
    yr=dt.year.to_numpy(); mo=dt.month.to_numpy()
    refvals=[float(rr[i]) for i in range(len(rr)) if yr[i]==2011 and int(mo[i]) in MONTHS]
    ref=math.fsum(refvals)/len(refvals)
    ans=[]
    for y in YEARS:
        vals=[float(rr[i]) for i in range(len(rr)) if yr[i]==y and int(mo[i]) in MONTHS]
        ans.append(math.fsum(vals)/len(vals)-ref)
    return np.asarray(ans,float),rr


def main():
    F,missing,annual=forcing()
    h=hydro(F,P)
    area=np.asarray(h['area'],float); qret=np.asarray(h['return_flow'],float)
    exposed=np.clip((A0-area)/A0,0.0,1.0)

    e_pd=(pd.Series(exposed).rolling(EST_W,min_periods=EST_W).min().fillna(0.0).to_numpy())
    e_scalar=scalar_roll_min(exposed,EST_W)

    a=R_EST/365.0
    q_np=np.clip(1.0-a*np.asarray(e_pd,float),0.0,1.0)
    state_np=1.0-np.cumprod(q_np)
    state_seq=sequential_state(e_scalar,R_EST)

    dt=pd.to_datetime(h['dates']); yr=dt.year.to_numpy(); mo=dt.month.to_numpy()
    S_np=np.array([float(np.mean(state_np[(yr==y)&np.isin(mo,MONTHS)])) for y in YEARS])
    S_fsum=fsum_window_means(dt,state_seq)

    rr_pd=pd.Series(qret,index=dt).rolling(HYDRO_W,min_periods=1).sum().to_numpy()
    ref_pd=float(np.mean(rr_pd[(yr==2011)&np.isin(mo,MONTHS)]))
    H_pd=np.array([float(np.mean(rr_pd[(yr==y)&np.isin(mo,MONTHS)])-ref_pd) for y in YEARS])
    H_fsum,rr_fsum=deterministic_h_feature(dt,qret,HYDRO_W)

    summary={
      'status':'PASS_STAGE60B_FORENSICS',
      'runner':{'platform':platform.platform(),'machine':platform.machine(),'processor':platform.processor(),'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'replica':os.environ.get('REPLICA','')},
      'forcing_missing':missing,
      'fingerprints':{
        'F_pre':sha(F['pre']),'F_eto':sha(F['eto']),'F_ep':sha(F['ep']),
        'hydro_V':sha(h['V']),'hydro_area':sha(area),'hydro_return_flow':sha(qret),
        'exposed':sha(exposed),'E7_pandas':sha(e_pd),'E7_scalar':sha(e_scalar),
        'q_for_cumprod':sha(q_np),'state_numpy_cumprod':sha(state_np),'state_sequential':sha(state_seq),
        'S_numpy_mean':sha(S_np),'S_fixed_order_fsum':sha(S_fsum),
        'rolling_return_pandas':sha(rr_pd),'rolling_return_fsum':sha(rr_fsum),
        'H_pandas_mean':sha(H_pd),'H_fixed_order_fsum':sha(H_fsum),
      },
      'within_run_differences':{
        'E7_pandas_vs_scalar_max_abs':maxabs(e_pd,e_scalar),
        'state_numpy_vs_sequential_max_abs':maxabs(state_np,state_seq),
        'S_numpy_vs_fsum_max_abs':maxabs(S_np,S_fsum),
        'rolling_return_pandas_vs_fsum_max_abs':maxabs(rr_pd,rr_fsum),
        'H_pandas_vs_fsum_max_abs':maxabs(H_pd,H_fsum),
      },
      'S_numpy':S_np.tolist(),'S_numpy_hex':hx(S_np),
      'S_fixed':S_fsum.tolist(),'S_fixed_hex':hx(S_fsum),
      'H_pandas':H_pd.tolist(),'H_pandas_hex':hx(H_pd),
      'H_fixed':H_fsum.tolist(),'H_fixed_hex':hx(H_fsum),
      'physical_closure':{'mass_error_m3':float(h['mass_error']),'area_partition_error_m2':float(h['area_partition_error']),'precip_partition_error_m3':float(h['precip_partition_error'])},
    }
    (OUT/'stage60b_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
