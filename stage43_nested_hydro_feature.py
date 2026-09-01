#!/usr/bin/env python3
"""Stage43 — nested selection among causal antecedent hydrologic wetness features.

Hydrology and ecology equations are unchanged from Stage38/Stage42. The only
new model-selection axis is which *trailing-only* wetness diagnostic from the
same forcing/conserved hydrologic trajectory enters the short-term observation
operator. Feature choice and window are selected inside every outer LOOCV fold.
2022 remains sealed unless all pre-holdout gates pass.
"""
from __future__ import annotations
import itertools,json,shutil
from pathlib import Path
import numpy as np
import pandas as pd
import stage40_bidirectional_hydroperiod as s40
from stage38_domain_corrected import hydro
from stage35c_mass_balance_state_operator import A0

OUT=Path('stage43_outputs');OUT.mkdir(exist_ok=True)
FEATURE_NAMES={0:'return_flow',1:'surface_storage',2:'hydrologic_area',3:'precip_minus_lake_evap',4:'precipitation'}
# Numeric guards surround all accepted candidates, including feature IDs.
GRIDS={
 'V0':[1000.,1600.,2200.], 'p_shape':[6.,12.,18.],
 'tau_surf':[60.,120.,240.], 'local_frac':[.15,.30,.45],
 'tau_fast':[30.,60.,120.], 'k_gw_mm_d':[.02,.05,.10,.25,1.,2.,4.],
 'r_est_yr':[.01,.025,.05,.10,.25,.50],
 'r_flood_yr':[.0002,.001,.0025,.005,.01,.025,.05,.10,.25],
 'hydro_window_d':[7,14,30,60,90,180,365],
 'hydro_feature_id':[-1,0,1,2,3,4,5],
}
HKEYS=['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']
ALLKEYS=HKEYS+['r_est_yr','r_flood_yr','hydro_window_d','hydro_feature_id']


def annual(dt,x):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy()
    return np.array([float(np.mean(x[(yr==y)&np.isin(mo,[5,6])])) for y in s40.YEARS])


def feature(dt,raw,w,mode):
    """Trailing-only anomaly vs 2011 May-Jun; positive means wetter."""
    dt=pd.to_datetime(dt);yr=dt.year.to_numpy();mo=dt.month.to_numpy();w=int(w)
    ser=pd.Series(np.asarray(raw,float),index=dt)
    if mode in (0,3,4): z=ser.rolling(w,min_periods=1).sum().to_numpy()
    else: z=ser.rolling(w,min_periods=1).mean().to_numpy()
    ref=float(np.mean(z[(yr==2011)&np.isin(mo,[5,6])]))
    return np.array([float(np.mean(z[(yr==y)&np.isin(mo,[5,6])])-ref) for y in s40.YEARS])


def build_candidates(F):
    internal={k:[v for v in vals if v!=min(vals) and v!=max(vals)] for k,vals in GRIDS.items()};out=[]
    pre=np.asarray(F['pre'],float);ep=np.asarray(F['ep'],float)
    for vals in itertools.product(*[internal[k] for k in HKEYS]):
        hp=dict(zip(HKEYS,vals));h=hydro(F,hp);dt=h['dates']
        eco={}
        for re,rf in itertools.product(internal['r_est_yr'],internal['r_flood_yr']):
            z=s40.bidirectional_hydroperiod_state(h['area'],re,rf)
            eco[(re,rf)]=(annual(dt,z['state']),z['total_establishment'],z['total_reversal'],z['max_reversal_daily'])
        raw={0:h['return_flow'],1:h['V'],2:h['area'],3:pre-ep,4:pre}
        hf={(fid,w):feature(dt,raw[int(fid)],w,int(fid)) for fid,w in itertools.product(internal['hydro_feature_id'],internal['hydro_window_d'])}
        for re,rf,fid,w in itertools.product(internal['r_est_yr'],internal['r_flood_yr'],internal['hydro_feature_id'],internal['hydro_window_d']):
            S,te,tr,mr=eco[(re,rf)]
            out.append({**hp,'r_est_yr':re,'r_flood_yr':rf,'hydro_feature_id':fid,'hydro_window_d':w,
              'S':S,'H':hf[(fid,w)],'total_establishment':te,'total_reversal':tr,'max_reversal_daily':mr,
              'max_mass_error_m3':float(h['mass_error']),'max_area_partition_error_m2':float(h['area_partition_error']),
              'max_precip_partition_error_m3':float(h['precip_partition_error'])})
    return out,internal


def relabel():
    src=OUT/'stage40_summary.json'
    if not src.exists():return
    d=json.loads(src.read_text(encoding='utf-8'))
    d['model']='Stage43 nested causal antecedent-hydrology feature selection'
    d['stage43_feature_names']=FEATURE_NAMES
    d['holdout_2022_used']=False
    if d.get('selected'):
        d['selected']['hydro_feature_name']=FEATURE_NAMES[int(round(d['selected']['hydro_feature_id']))]
    for r in d.get('best_rejected_preview',[]):
        if 'hydro_feature_id' in r:r['hydro_feature_name']=FEATURE_NAMES[int(round(r['hydro_feature_id']))]
    (OUT/'stage43_summary.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    csv=OUT/'stage40_rejection_diagnostics.csv'
    if csv.exists():shutil.copy2(csv,OUT/'stage43_rejection_diagnostics.csv')


def main():
    s40.GRIDS=GRIDS;s40.HKEYS=HKEYS;s40.ALLKEYS=ALLKEYS;s40.OUT=OUT;s40.build_candidates=build_candidates
    code=None
    try:s40.main()
    except SystemExit as e:code=e
    finally:relabel()
    if code is not None:raise code

if __name__=='__main__':main()
