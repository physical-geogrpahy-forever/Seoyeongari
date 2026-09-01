#!/usr/bin/env python3
"""Stage48 — nested selection of a literature-bounded continuous exposure window.

Stage46 fixed the recruitment window at 14 d and modestly improved outer-fold
feasibility. Stage48 avoids post-hoc choice by including 7, 14 and 21 d as a
structural hyperparameter selected inside every nested fold. Guard values 3 and
45 d make the three literature-bounded candidate windows interior under the
unchanged no-grid-edge rule.

Establishment uses Stage46's bidirectional state but with E_L(t), the fraction
of the 2011 open-water footprint continuously exposed throughout the trailing L
days (rolling minimum of instantaneous exposed fraction). Flood reversal keeps
the trailing 28-d inundation fraction. No new fitted correction term, calendar
trend, threshold relaxation, or 2022 information is introduced.
"""
from __future__ import annotations
import itertools,json,shutil
from pathlib import Path
import numpy as np
import pandas as pd
import stage40_bidirectional_hydroperiod as s40
from stage38_domain_corrected import hydro
from stage35c_mass_balance_state_operator import A0
from stage45_expanded_hydrology_nested import GRIDS as BASE_GRIDS,HKEYS,annual_hydro

OUT=Path('stage48_outputs'); OUT.mkdir(exist_ok=True)
FLOOD_LAG_D=28
GRIDS={**BASE_GRIDS,'est_window_d':[3,7,14,21,45]}
ALLKEYS=HKEYS+['r_est_yr','r_flood_yr','hydro_window_d','est_window_d']


def affine_grid_annual(dt,E_by_window,F,re_vals,rf_vals,win_vals):
    """Advance all (window,r_est,r_flood) states simultaneously and exactly."""
    combos=list(itertools.product(win_vals,re_vals,rf_vals))
    w_index={w:i for i,w in enumerate(win_vals)}
    wi=np.array([w_index[c[0]] for c in combos],int)
    ae=np.array([c[1] for c in combos],float)/365.0
    af=np.array([c[2] for c in combos],float)/365.0
    Emat=np.column_stack([E_by_window[w] for w in win_vals])
    c=np.zeros(len(combos),float); te=np.zeros_like(c); tr=np.zeros_like(c); mr=np.zeros_like(c)
    sums=np.zeros((len(combos),len(s40.YEARS)),float)
    dt=pd.to_datetime(dt); yr=dt.year.to_numpy(); mo=dt.month.to_numpy()
    slot=np.full(len(F),-1,int); counts=np.zeros(len(s40.YEARS),int)
    for j,y in enumerate(s40.YEARS):
        m=(yr==int(y)) & np.isin(mo,[5,6]); slot[m]=j; counts[j]=int(m.sum())
    for i in range(len(F)):
        e=Emat[i,wi]; f=float(F[i])
        up=ae*e*(1.0-c); dn=af*f*c
        c=np.clip(c+up-dn,0.,1.); te+=up; tr+=dn; mr=np.maximum(mr,dn)
        j=slot[i]
        if j>=0: sums[:,j]+=c
    S=sums/counts[None,:]
    return {combos[k]:(S[k].copy(),float(te[k]),float(tr[k]),float(mr[k])) for k in range(len(combos))}


def build_candidates(F):
    internal={k:[v for v in vals if v!=min(vals) and v!=max(vals)] for k,vals in GRIDS.items()}
    out=[]; re_vals=internal['r_est_yr']; rf_vals=internal['r_flood_yr']; win_vals=internal['est_window_d']
    for vals in itertools.product(*[internal[k] for k in HKEYS]):
        hp=dict(zip(HKEYS,vals)); h=hydro(F,hp); a=np.asarray(h['area'],float)
        exposed=np.clip((A0-a)/A0,0,1)
        E_by_window={w:pd.Series(exposed).rolling(int(w),min_periods=int(w)).min().fillna(0).to_numpy() for w in win_vals}
        Fw=pd.Series(np.clip(a/A0,0,1)).rolling(FLOOD_LAG_D,min_periods=1).mean().to_numpy()
        ec=affine_grid_annual(h['dates'],E_by_window,Fw,re_vals,rf_vals,win_vals)
        hc={w:annual_hydro(h['dates'],h['return_flow'],w) for w in internal['hydro_window_d']}
        for ew,re,rf,hw in itertools.product(win_vals,re_vals,rf_vals,internal['hydro_window_d']):
            S,te,tr,mr=ec[(ew,re,rf)]
            out.append({**hp,'r_est_yr':re,'r_flood_yr':rf,'hydro_window_d':hw,'est_window_d':ew,
              'S':S,'H':hc[hw],'total_establishment':te,'total_reversal':tr,'max_reversal_daily':mr,
              'max_mass_error_m3':float(h['mass_error']),
              'max_area_partition_error_m2':float(h['area_partition_error']),
              'max_precip_partition_error_m3':float(h['precip_partition_error'])})
    return out,internal


def relabel():
    src=OUT/'stage40_summary.json'
    if not src.exists(): return
    d=json.loads(src.read_text(encoding='utf-8'))
    d['model']='Stage48 nested 7/14/21-day continuous-exposure recruitment window'
    d['stage48_change']='establishment window is selected inside every nested fold from 7/14/21 d; strict gates unchanged'
    d['flood_reversal_trailing_window_days']=FLOOD_LAG_D
    d['holdout_2022_used']=False
    (OUT/'stage48_summary.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    for a,b in [('stage40_rejection_diagnostics.csv','stage48_rejection_diagnostics.csv'),
                ('stage40_nested_outer_predictions.csv','stage48_nested_outer_predictions.csv')]:
        p=OUT/a
        if p.exists(): shutil.copy2(p,OUT/b)


def main():
    s40.GRIDS=GRIDS; s40.HKEYS=HKEYS; s40.ALLKEYS=ALLKEYS; s40.OUT=OUT
    s40.build_candidates=build_candidates
    code=None
    try: s40.main()
    except SystemExit as e: code=e
    finally: relabel()
    if code is not None: raise code

if __name__=='__main__': main()
