#!/usr/bin/env python3
"""Locked 2022 holdout for a fully strict-passing Stage43 model."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing
from stage35c_mass_balance_state_operator import A0
from stage38_domain_corrected import hydro
from stage40_bidirectional_hydroperiod import bidirectional_hydroperiod_state
from stage43_nested_hydro_feature import FEATURE_NAMES

SRC=Path('stage43_outputs/stage43_summary.json');OUT=Path('stage43_holdout_outputs');OUT.mkdir(exist_ok=True);OBS2022=1988.560

def feat(dt,raw,w,mode):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy();ser=pd.Series(np.asarray(raw,float),index=dt)
    z=(ser.rolling(int(w),min_periods=1).sum() if mode in (0,3,4) else ser.rolling(int(w),min_periods=1).mean()).to_numpy()
    ref=float(np.mean(z[(yr==2011)&np.isin(mo,[5,6])]))
    return z-ref

def main():
    d=json.loads(SRC.read_text(encoding='utf-8'))
    if not d.get('nested_selection_pass',False):raise SystemExit('Stage43 did not fully pass; 2022 remains sealed')
    c=d['selected'];hp={k:c[k] for k in ['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']}
    F,_,_=forcing();h=hydro(F,hp);dt=pd.to_datetime(h['dates']);yr=dt.year.to_numpy();mo=dt.month.to_numpy();m=(yr==2022)&np.isin(mo,[5,6])
    z=bidirectional_hydroperiod_state(h['area'],c['r_est_yr'],c['r_flood_yr']);S22=float(np.mean(z['state'][m]));fid=int(round(c['hydro_feature_id']))
    raw={0:h['return_flow'],1:h['V'],2:h['area'],3:np.asarray(F['pre'],float)-np.asarray(F['ep'],float),4:np.asarray(F['pre'],float)}[fid]
    H=feat(dt,raw,c['hydro_window_d'],fid);H22=float(np.mean(H[m]));pred=float(A0-c['K_colonizable_m2']*S22+c['K_hydro']*H22)
    out={'model':'Stage43 locked 2022 holdout','fit_used_2022':False,'selection_changed_after_seeing_2022':False,
      'hydro_feature_id':fid,'hydro_feature_name':FEATURE_NAMES[fid],'pred_2022_m2':pred,'obs_2022_m2':OBS2022,
      'error_m2':pred-OBS2022,'abs_pct_error':abs(pred-OBS2022)/OBS2022*100,'state_2022':S22,'hydro_anom_2022':H22,
      'ecology_effect_m2':-c['K_colonizable_m2']*S22,'hydrology_effect_m2':c['K_hydro']*H22,
      'max_daily_mass_error_m3':h['mass_error'],'max_area_partition_error_m2':h['area_partition_error'],
      'max_precip_partition_error_m3':h['precip_partition_error'],'locked_candidate':c}
    (OUT/'stage43_holdout_2022.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
