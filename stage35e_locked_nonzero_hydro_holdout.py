#!/usr/bin/env python3
"""Locked holdout for the best Stage35C candidate with a strictly positive
water-balance-derived hydrologic contribution. 2022 was not used in fitting or
selection. Hydrologic core is unchanged and closes exactly each day."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing
from stage35c_mass_balance_state_operator import hydro, colon_state, A0

OUT=Path('stage35e_holdout_outputs'); OUT.mkdir(exist_ok=True)
OBS2022=1988.560
# Selected only from 2013/15/17/19/21/23 by:
# nRMSE<=2%, exact closure, state-year corr<0.995, K_hydro>0; then min LOOCV.
P={'V0':1600.0,'p_shape':4.0,'tau_surf':60.0,'local_frac':0.2,'tau_fast':60.0}
R=0.05; WINDOW=30
KC=2042.7464625876405
KH=0.0389261465014742
TRAIN={'nrmse_pct':1.504640166677745,'rmse_m2':30.71081171241528,'loocv_nrmse_pct':1.859050434379264,'state_year_corr':0.994271924969001}

def main():
    F,_,_=forcing(); h=hydro(F,P); state,exp,e28=colon_state(h['area'],R)
    dt=h['dates']; yr=dt.year.to_numpy(); mo=dt.month.to_numpy()
    mj22=(yr==2022)&np.isin(mo,[5,6])
    S22=float(np.mean(state[mj22]))
    roll=pd.Series(h['return_flow'],index=dt).rolling(WINDOW,min_periods=1).sum().to_numpy()
    ref=float(np.mean(roll[(yr==2011)&np.isin(mo,[5,6])]))
    H22=float(np.mean(roll[mj22])-ref)
    eco=-KC*S22; hyd=KH*H22; pred=A0+eco+hyd
    out={'model':'Stage35E locked nonzero-hydrology holdout','fit_used_2022':False,
         'pred_2022_m2':pred,'obs_2022_m2':OBS2022,'error_m2':pred-OBS2022,
         'abs_pct_error':abs(pred-OBS2022)/OBS2022*100,
         'state_2022':S22,'returnflow30_anom_2022_m3':H22,
         'ecology_effect_m2':eco,'hydrology_effect_m2':hyd,
         'max_daily_mass_error_m3':h['mass_error'],
         'locked':{**P,'r_exposure_yr':R,'window_d':WINDOW,'K_colonizable_m2':KC,'K_hydro':KH},
         'training_metrics':TRAIN,
         'rules':{'exact_daily_water_balance':True,'CN':False,'TOPMODEL':False,'lambda':0,'hard_cap':False,'freeboard':False,'explicit_time':False,'future_leakage':False,'2022_fit':False}}
    (OUT/'stage35e_holdout_2022.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
