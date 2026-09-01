#!/usr/bin/env python3
"""Locked 2022 holdout for a fully strict-passing Stage42 model."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing
from stage35c_mass_balance_state_operator import A0
from stage38_domain_corrected import hydro
from stage40_bidirectional_hydroperiod import bidirectional_hydroperiod_state

SRC=Path('stage42_outputs/stage42_summary.json')
OUT=Path('stage42_holdout_outputs');OUT.mkdir(exist_ok=True)
OBS2022=1988.560

def main():
    d=json.loads(SRC.read_text(encoding='utf-8'))
    if not d.get('nested_selection_pass',False):
        raise SystemExit('Stage42 did not fully pass; 2022 remains sealed')
    c=d['selected'];hp={k:c[k] for k in ['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']}
    F,_,_=forcing();h=hydro(F,hp);dt=pd.to_datetime(h['dates']);yr=dt.year.to_numpy();mo=dt.month.to_numpy();m=(yr==2022)&np.isin(mo,[5,6])
    z=bidirectional_hydroperiod_state(h['area'],c['r_est_yr'],c['r_flood_yr']);S22=float(np.mean(z['state'][m]))
    w=int(c['hydro_window_d']);rr=pd.Series(h['return_flow'],index=dt).rolling(w,min_periods=1).sum().to_numpy();ref=float(np.mean(rr[(yr==2011)&np.isin(mo,[5,6])]))
    H22=float(np.mean(rr[m])-ref);pred=float(A0-c['K_colonizable_m2']*S22+c['K_hydro']*H22)
    out={'model':'Stage42 locked 2022 holdout','fit_used_2022':False,'selection_changed_after_seeing_2022':False,
      'pred_2022_m2':pred,'obs_2022_m2':OBS2022,'error_m2':pred-OBS2022,'abs_pct_error':abs(pred-OBS2022)/OBS2022*100,
      'state_2022':S22,'hydro_anom_2022':H22,'ecology_effect_m2':-c['K_colonizable_m2']*S22,'hydrology_effect_m2':c['K_hydro']*H22,
      'max_daily_mass_error_m3':h['mass_error'],'max_area_partition_error_m2':h['area_partition_error'],
      'max_precip_partition_error_m3':h['precip_partition_error'],'locked_candidate':c}
    (OUT/'stage42_holdout_2022.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
