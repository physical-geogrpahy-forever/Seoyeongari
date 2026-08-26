#!/usr/bin/env python3
"""Locked holdout/diagnostics for the preselected Stage36 candidate.
Selection used only 2013/15/17/19/21/23 and required: nRMSE<=2%, exact water
balance, positive water-balance hydrology term, and state-year corr<0.99; then
minimum LOOCV. 2022 is diagnostic only and never used for fitting/selection.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing
from stage35c_mass_balance_state_operator import hydro,A0
from stage36_hydroperiod_state import hydroperiod_state

OUT=Path('stage36_holdout_outputs');OUT.mkdir(exist_ok=True)
OBS2022=1988.560
P={'V0':1600.0,'p_shape':12.0,'tau_surf':120.0,'local_frac':0.2,'tau_fast':60.0}
R_EST=.025; WINDOW=30; KC=2238.5186315026917; KH=.14535278958238484
TRAIN={'nrmse_pct':1.5307057903707684,'rmse_m2':31.24283025022331,'loocv_nrmse_pct':1.941774816517429,'state_year_corr':.9895850381090959}

def main():
    F,_,_=forcing();h=hydro(F,P);dt=h['dates'];yr=dt.year.to_numpy();mo=dt.month.to_numpy()
    st,ex,e28=hydroperiod_state(h['area'],R_EST)
    mj22=(yr==2022)&np.isin(mo,[5,6]);S22=float(np.mean(st[mj22]))
    rr=pd.Series(h['return_flow'],index=dt).rolling(WINDOW,min_periods=1).sum().to_numpy()
    ref=float(np.mean(rr[(yr==2011)&np.isin(mo,[5,6])]))
    H22=float(np.mean(rr[mj22])-ref);eco=-KC*S22;hyd=KH*H22;pred=A0+eco+hyd

    # Diagnostics from conserved storage-derived hydrologic area, not used for fitting.
    diag={}
    for y in range(2011,2024):
        m=yr==y; spr=m & np.isin(mo,[3,4]); mj=m & np.isin(mo,[5,6])
        ay=h['area'][m]; aspr=h['area'][spr]
        # exposure means hydrologic area below the 2011 reference; complete dry is area<1 m2.
        diag[str(y)]={
          'mean_hydrologic_area_m2':float(np.mean(ay)),
          'mar_apr_mean_area_m2':float(np.mean(aspr)),
          'mar_apr_exposed_fraction':float(np.mean(aspr<A0)),
          'mar_apr_complete_dry_days':int(np.sum(aspr<1.0)),
          'may_jun_mean_hydrologic_area_m2':float(np.mean(h['area'][mj])),
          'may_jun_returnflow_m3':float(np.sum(h['return_flow'][mj]))}
        }
    out={'model':'Stage36 locked balanced hydroperiod candidate','fit_used_2022':False,
         'pred_2022_m2':pred,'obs_2022_m2':OBS2022,'error_m2':pred-OBS2022,'abs_pct_error':abs(pred-OBS2022)/OBS2022*100,
         'state_2022':S22,'returnflow30_anom_2022_m3':H22,'ecology_effect_m2':eco,'hydrology_effect_m2':hyd,
         'max_daily_mass_error_m3':h['mass_error'],'locked':{**P,'r_est_yr':R_EST,'window_d':WINDOW,'K_colonizable_m2':KC,'K_hydro':KH},
         'training_metrics':TRAIN,'hydroperiod_diagnostics':diag,
         'rules':{'exact_daily_water_balance':True,'CN':False,'TOPMODEL':False,'lambda':0,'hard_cap':False,'freeboard':False,'explicit_time':False,'future_leakage':False,'2022_fit':False}}
    (OUT/'stage36_holdout_2022.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
