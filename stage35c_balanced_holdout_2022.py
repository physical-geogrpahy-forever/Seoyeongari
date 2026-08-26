#!/usr/bin/env python3
import json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing
from stage35c_mass_balance_state_operator import hydro, colon_state, A0
OUT=Path('stage35c_holdout_outputs');OUT.mkdir(exist_ok=True)
# Locked from Stage35C feasible set: requires non-zero hydrologic contribution,
# nRMSE<2%, LOOCV<2%, state-year corr<0.99. 2022 was not used to select it.
P={'V0':1600.0,'p_shape':12.0,'tau_surf':60.0,'local_frac':0.4,'tau_fast':60.0}
R=0.1; WINDOW=30; KC=2235.435784987224; KH=0.0244566772355811
OBS2022=1988.560

def main():
 F,_,_=forcing();h=hydro(F,P);state,exp,e28=colon_state(h['area'],R);dt=h['dates'];yr=dt.year.to_numpy();mo=dt.month.to_numpy()
 S2022=float(state[(yr==2022)&np.isin(mo,[5,6])].mean())
 roll=pd.Series(h['return_flow'],index=dt).rolling(WINDOW,min_periods=1).sum().to_numpy()
 ref=float(roll[(yr==2011)&np.isin(mo,[5,6])].mean())
 H2022=float(roll[(yr==2022)&np.isin(mo,[5,6])].mean()-ref)
 pred=A0-KC*S2022+KH*H2022
 out={'model':'Stage35C balanced locked 2022 holdout','fit_used_2022':False,'pred_2022_m2':pred,'obs_2022_m2':OBS2022,'error_m2':pred-OBS2022,'abs_pct_error':abs(pred-OBS2022)/OBS2022*100,
      'state_2022':S2022,'returnflow30_anom_2022_m3':H2022,'ecology_effect_m2':-KC*S2022,'hydrology_effect_m2':KH*H2022,
      'max_daily_mass_error_m3':h['mass_error'],'locked':{**P,'r_exposure_yr':R,'window_d':WINDOW,'K_colonizable_m2':KC,'K_hydro':KH},
      'training_metrics':{'nrmse_pct':1.6727834950024372,'loocv_nrmse_pct':1.99897134390346,'state_year_corr':0.9895220694252324}}
 (OUT/'stage35c_balanced_holdout_2022.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
