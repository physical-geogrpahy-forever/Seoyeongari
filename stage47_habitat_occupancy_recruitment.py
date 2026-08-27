#!/usr/bin/env python3
"""Stage47 — continuous-exposure habitat occupancy recruitment.

Stage46 showed that a fixed 14-d continuous drawdown window modestly improved
outer-fold feasibility, but the state still accumulated recruitment repeatedly
on already occupied habitat. Stage47 treats the ecological state as occupied
fraction of the 2011 open-water footprint.

Let E14(t) be the fraction continuously exposed during the trailing 14 days.
Recruitment occurs only into suitable but not-yet-occupied habitat:
    dC+ = r_est/365 * max(E14 - C, 0)
Flood reversal remains causal and acts on occupied habitat under the trailing
28-d inundation fraction:
    dC- = r_flood/365 * F28 * C
    C(t+1) = clip(C + dC+ - dC-, 0, 1)

This removes repeated recruitment on the same exposed area without adding a
new fitted correction term or calendar trend. Stage45 expanded hydrology,
strict 2% gates, exact water/area partition, no-edge rules, nested selection and
the sealed 2022 holdout are unchanged.
"""
from __future__ import annotations
import itertools,json,shutil
from pathlib import Path
import numpy as np
import pandas as pd
import stage40_bidirectional_hydroperiod as s40
from stage38_domain_corrected import hydro
from stage35c_mass_balance_state_operator import A0
from stage45_expanded_hydrology_nested import GRIDS,HKEYS,ALLKEYS,annual,annual_hydro

OUT=Path('stage47_outputs'); OUT.mkdir(exist_ok=True)
EST_WINDOW_D=14
FLOOD_LAG_D=28


def occupancy_state(E,F,re,rf):
    E=np.asarray(E,float); F=np.asarray(F,float)
    c=0.; st=np.empty(len(E)); upv=np.empty(len(E)); dnv=np.empty(len(E))
    ae=float(re)/365.; af=float(rf)/365.
    for i,(e,f) in enumerate(zip(E,F)):
        up=ae*max(float(e)-c,0.0)
        dn=af*float(f)*c
        c=float(np.clip(c+up-dn,0.,1.))
        st[i]=c; upv[i]=up; dnv[i]=dn
    return st,float(upv.sum()),float(dnv.sum()),float(dnv.max())


def build_candidates(F):
    internal={k:[v for v in vals if v!=min(vals) and v!=max(vals)] for k,vals in GRIDS.items()}
    out=[]
    for vals in itertools.product(*[internal[k] for k in HKEYS]):
        hp=dict(zip(HKEYS,vals)); h=hydro(F,hp); a=np.asarray(h['area'],float)
        exposed=np.clip((A0-a)/A0,0,1)
        E=pd.Series(exposed).rolling(EST_WINDOW_D,min_periods=EST_WINDOW_D).min().fillna(0).to_numpy()
        Fw=pd.Series(np.clip(a/A0,0,1)).rolling(FLOOD_LAG_D,min_periods=1).mean().to_numpy()
        ec={}
        for re,rf in itertools.product(internal['r_est_yr'],internal['r_flood_yr']):
            x,te,tr,mr=occupancy_state(E,Fw,re,rf)
            ec[(re,rf)]=(annual(h['dates'],x),te,tr,mr)
        hc={w:annual_hydro(h['dates'],h['return_flow'],w) for w in internal['hydro_window_d']}
        for re,rf,w in itertools.product(internal['r_est_yr'],internal['r_flood_yr'],internal['hydro_window_d']):
            S,te,tr,mr=ec[(re,rf)]
            out.append({**hp,'r_est_yr':re,'r_flood_yr':rf,'hydro_window_d':w,'S':S,'H':hc[w],
              'total_establishment':te,'total_reversal':tr,'max_reversal_daily':mr,
              'max_mass_error_m3':float(h['mass_error']),
              'max_area_partition_error_m2':float(h['area_partition_error']),
              'max_precip_partition_error_m3':float(h['precip_partition_error'])})
    return out,internal


def relabel():
    src=OUT/'stage40_summary.json'
    if not src.exists(): return
    d=json.loads(src.read_text(encoding='utf-8'))
    d['model']='Stage47 continuous-exposure habitat occupancy + slow flood reversal'
    d['stage47_change']='recruitment only into continuously exposed but unoccupied habitat; strict gates unchanged'
    d['establishment_continuous_exposure_window_days']=EST_WINDOW_D
    d['flood_reversal_trailing_window_days']=FLOOD_LAG_D
    d['holdout_2022_used']=False
    (OUT/'stage47_summary.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    for a,b in [('stage40_rejection_diagnostics.csv','stage47_rejection_diagnostics.csv'),
                ('stage40_nested_outer_predictions.csv','stage47_nested_outer_predictions.csv')]:
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
