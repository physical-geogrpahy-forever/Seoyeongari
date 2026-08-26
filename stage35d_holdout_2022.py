#!/usr/bin/env python3
import json
from pathlib import Path
import numpy as np
from stage31_topmodel_vsa import forcing
from stage35c_mass_balance_state_operator import hydro,A0
from stage35d_flood_reversal import state
OUT=Path('stage35d_holdout_outputs');OUT.mkdir(exist_ok=True)
P={'V0':1600.0,'p_shape':20.0,'tau_surf':60.0,'local_frac':0.2,'tau_fast':60.0}
RE=.1;RF=1.0;KC=A0;OBS=1988.560

def main():
 F,_,_=forcing();h=hydro(F,P);st,e,f=state(h['area'],RE,RF);dt=h['dates'];yr=dt.year.to_numpy();mo=dt.month.to_numpy();m=(yr==2022)&np.isin(mo,[5,6]);S=float(st[m].mean());pred=A0-KC*S
 out={'model':'Stage35D locked excluded-2022 holdout','fit_used_2022':False,'pred_2022_m2':pred,'obs_2022_m2':OBS,'error_m2':pred-OBS,'abs_pct_error':abs(pred-OBS)/OBS*100,'state_2022':S,
      'ecology_hydrology_effect_total_m2':-KC*S,'max_daily_mass_error_m3':h['mass_error'],'locked':{**P,'r_est_yr':RE,'r_flood_yr':RF,'K_colonizable_m2':KC},
      'training_metrics':{'nrmse_pct':1.72044999481259,'loocv_nrmse_pct':1.921812207413297,'state_year_corr':0.9883614144683361}}
 (OUT/'stage35d_holdout_2022.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
