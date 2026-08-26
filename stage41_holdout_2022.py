#!/usr/bin/env python3
"""2022 holdout for a Stage41 model that passed every strict pre-holdout gate."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing
from stage38_domain_corrected import hydro
from stage40_bidirectional_hydroperiod import bidirectional_hydroperiod_state

SRC=Path('stage41_outputs/stage41_summary.json')
OUT=Path('stage41_holdout_outputs');OUT.mkdir(exist_ok=True)
OBS2022=1988.560

def main():
    d=json.loads(SRC.read_text(encoding='utf-8'))
    if not d.get('nested_selection_pass',False):
        raise SystemExit('Stage41 not passed; 2022 remains sealed')
    c=d['selected']
    hp={k:c[k] for k in ['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']}
    F,_,_=forcing();h=hydro(F,hp)
    dt=pd.to_datetime(h['dates']);yr=dt.year.to_numpy();mo=dt.month.to_numpy()
    m=(yr==2022)&np.isin(mo,[5,6])
    z=bidirectional_hydroperiod_state(h['area'],c['r_est_yr'],c['r_flood_yr'])
    B=float(np.mean(h['area'][m]));C=float(np.mean(h['area'][m]*z['state'][m]))
    pred=float(B-c['cover_fraction']*C)
    out={'model':'Stage41 locked 2022 holdout','fit_used_2022':False,
      'selection_changed_after_seeing_2022':False,'pred_2022_m2':pred,
      'obs_2022_m2':OBS2022,'error_m2':pred-OBS2022,
      'abs_pct_error':abs(pred-OBS2022)/OBS2022*100,
      'hydrologic_area_2022_m2':B,'ecological_occlusion_feature_2022_m2':C,
      'ecological_effect_2022_m2':-c['cover_fraction']*C,'locked_candidate':c,
      'max_daily_mass_error_m3':h['mass_error'],
      'max_area_partition_error_m2':h['area_partition_error'],
      'max_precip_partition_error_m3':h['precip_partition_error']}
    (OUT/'stage41_holdout_2022.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
