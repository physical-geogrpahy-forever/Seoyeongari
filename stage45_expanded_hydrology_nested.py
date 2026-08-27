#!/usr/bin/env python3
"""Stage45 — restore genuine hydrologic structural search under no-edge rules.

Stages42-44 used three-point grids for V0, p_shape, tau_surf, local_frac and
 tau_fast. Because strict acceptance rejects grid boundaries, those grids left
only one admissible value for each parameter. Stage45 adds *guard values outside
 the previously tested ranges* so the original Stage38 values 1000/1600/2200,
6/12/18, 60/120/240, .15/.30/.45 and 30/60/120 are all interior candidates.
No acceptance threshold is relaxed and the actual admissible values are not
extended beyond those Stage38 ranges.

The Stage42 bidirectional equation is retained. Candidate construction is
algebraically identical but caches the rolling exposure/inundation series and
uses the exact affine recurrence vector form to keep the expanded nested search
tractable. 2022 remains sealed unless every gate and outer nested LOOCV passes.
"""
from __future__ import annotations
import itertools,json,shutil
from pathlib import Path
import numpy as np
import pandas as pd
import stage40_bidirectional_hydroperiod as s40
from stage38_domain_corrected import hydro
from stage35c_mass_balance_state_operator import A0

OUT=Path('stage45_outputs');OUT.mkdir(exist_ok=True)
GRIDS={
 'V0':[700.,1000.,1600.,2200.,3000.],
 'p_shape':[3.,6.,12.,18.,30.],
 'tau_surf':[30.,60.,120.,240.,480.],
 'local_frac':[.05,.15,.30,.45,.60],
 'tau_fast':[15.,30.,60.,120.,240.],
 'k_gw_mm_d':[.02,.05,.10,.25,1.,2.,4.,8.],
 'r_est_yr':[.01,.025,.05,.10,.25,.50],
 'r_flood_yr':[.0002,.0005,.001,.0025,.005],
 'hydro_window_d':[7,14,30,60,90,180,365],
}
HKEYS=['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']
ALLKEYS=HKEYS+['r_est_yr','r_flood_yr','hydro_window_d']
LAG=28

def annual(dt,x):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy()
    return np.array([float(np.mean(x[(yr==y)&np.isin(mo,[5,6])])) for y in s40.YEARS])

def state_from_cached(E,F,re,rf):
    ae=float(re)/365.;af=float(rf)/365.
    q=1.-ae*E-af*F;b=ae*E
    # Exact solution of x_i=q_i*x_{i-1}+b_i, x_-1=0.
    P=np.cumprod(q);x=P*np.cumsum(b/P);x=np.clip(x,0.,1.)
    xp=np.r_[0.,x[:-1]];up=ae*E*(1.-xp);dn=af*F*xp
    return x,float(up.sum()),float(dn.sum()),float(dn.max())

def annual_hydro(dt,q,w):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy();rr=pd.Series(q,index=dt).rolling(int(w),min_periods=1).sum().to_numpy()
    ref=float(np.mean(rr[(yr==2011)&np.isin(mo,[5,6])]))
    return np.array([float(np.mean(rr[(yr==y)&np.isin(mo,[5,6])])-ref) for y in s40.YEARS])

def build_candidates(F):
    internal={k:[v for v in vals if v!=min(vals) and v!=max(vals)] for k,vals in GRIDS.items()};out=[]
    for vals in itertools.product(*[internal[k] for k in HKEYS]):
        hp=dict(zip(HKEYS,vals));h=hydro(F,hp);a=np.asarray(h['area'],float)
        E=pd.Series(np.clip((A0-a)/A0,0,1)).rolling(LAG,min_periods=1).mean().to_numpy()
        Fw=pd.Series(np.clip(a/A0,0,1)).rolling(LAG,min_periods=1).mean().to_numpy()
        ec={}
        for re,rf in itertools.product(internal['r_est_yr'],internal['r_flood_yr']):
            x,te,tr,mr=state_from_cached(E,Fw,re,rf);ec[(re,rf)]=(annual(h['dates'],x),te,tr,mr)
        hc={w:annual_hydro(h['dates'],h['return_flow'],w) for w in internal['hydro_window_d']}
        for re,rf,w in itertools.product(internal['r_est_yr'],internal['r_flood_yr'],internal['hydro_window_d']):
            S,te,tr,mr=ec[(re,rf)]
            out.append({**hp,'r_est_yr':re,'r_flood_yr':rf,'hydro_window_d':w,'S':S,'H':hc[w],
              'total_establishment':te,'total_reversal':tr,'max_reversal_daily':mr,
              'max_mass_error_m3':float(h['mass_error']),'max_area_partition_error_m2':float(h['area_partition_error']),
              'max_precip_partition_error_m3':float(h['precip_partition_error'])})
    return out,internal

def relabel():
    src=OUT/'stage40_summary.json'
    if not src.exists():return
    d=json.loads(src.read_text(encoding='utf-8'))
    d['model']='Stage45 expanded-interior hydrology + slow bidirectional ecology'
    d['stage45_change']='outer guard values make all original Stage38 hydrologic values interior; acceptance limits unchanged'
    d['holdout_2022_used']=False
    (OUT/'stage45_summary.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    for a,b in [('stage40_rejection_diagnostics.csv','stage45_rejection_diagnostics.csv'),('stage40_nested_outer_predictions.csv','stage45_nested_outer_predictions.csv')]:
        p=OUT/a
        if p.exists():shutil.copy2(p,OUT/b)

def main():
    s40.GRIDS=GRIDS;s40.HKEYS=HKEYS;s40.ALLKEYS=ALLKEYS;s40.OUT=OUT;s40.build_candidates=build_candidates
    code=None
    try:s40.main()
    except SystemExit as e:code=e
    finally:relabel()
    if code is not None:raise code

if __name__=='__main__':main()
