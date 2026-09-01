#!/usr/bin/env python3
"""Stage46 — event-like recruitment from a continuous drawdown window.

Stage45 restored genuine hydrologic structural search and produced 27 candidates
that passed the six-year training + fixed-candidate LOOCV gates, but outer
nested selection remained unstable. Stage46 changes only the establishment
forcing of the bidirectional ecological state.

Instead of a 28-d rolling mean of exposure, establishment pressure is the
fraction of the 2011 open-water footprint that has remained continuously
exposed for the previous 14 days. With a nested-area interpretation this is the
14-d rolling minimum of instantaneous exposed fraction. The 14-d window is
fixed a priori as a representative recruitment window within published 7-21 d
low-flow/drawdown opportunity ranges; it is NOT selected from the six area
observations. Flood reversal retains Stage45's 28-d trailing inundation mean.

No new observation correction term is introduced. Hydrology, exact mass and
area partition, coefficient constraints, 2% gates, nested selection, no-edge
rules and the sealed 2022 holdout are unchanged.
"""
from __future__ import annotations
import itertools,json,shutil
from pathlib import Path
import numpy as np
import pandas as pd
import stage40_bidirectional_hydroperiod as s40
from stage38_domain_corrected import hydro
from stage35c_mass_balance_state_operator import A0
from stage45_expanded_hydrology_nested import GRIDS,HKEYS,ALLKEYS,state_from_cached,annual,annual_hydro

OUT=Path('stage46_outputs'); OUT.mkdir(exist_ok=True)
EST_WINDOW_D=14
FLOOD_LAG_D=28


def build_candidates(F):
    internal={k:[v for v in vals if v!=min(vals) and v!=max(vals)] for k,vals in GRIDS.items()}
    out=[]
    for vals in itertools.product(*[internal[k] for k in HKEYS]):
        hp=dict(zip(HKEYS,vals)); h=hydro(F,hp); a=np.asarray(h['area'],float)
        exposed=np.clip((A0-a)/A0,0,1)
        # Fraction continuously exposed throughout the trailing 14-day window.
        E=pd.Series(exposed).rolling(EST_WINDOW_D,min_periods=EST_WINDOW_D).min().fillna(0).to_numpy()
        Fw=pd.Series(np.clip(a/A0,0,1)).rolling(FLOOD_LAG_D,min_periods=1).mean().to_numpy()
        ec={}
        for re,rf in itertools.product(internal['r_est_yr'],internal['r_flood_yr']):
            x,te,tr,mr=state_from_cached(E,Fw,re,rf)
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
    d['model']='Stage46 continuous-exposure recruitment + slow bidirectional ecology'
    d['stage46_change']='establishment forcing = trailing 14-day rolling minimum of exposed fraction; all strict gates unchanged'
    d['establishment_continuous_exposure_window_days']=EST_WINDOW_D
    d['flood_reversal_trailing_window_days']=FLOOD_LAG_D
    d['holdout_2022_used']=False
    (OUT/'stage46_summary.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    for a,b in [('stage40_rejection_diagnostics.csv','stage46_rejection_diagnostics.csv'),
                ('stage40_nested_outer_predictions.csv','stage46_nested_outer_predictions.csv')]:
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
