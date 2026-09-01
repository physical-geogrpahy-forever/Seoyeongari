#!/usr/bin/env python3
import json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing,sim
OUT=Path('stage34_holdout_outputs');OUT.mkdir(exist_ok=True)
A0=2241.762; OBS2022=1988.560
P={'m_area':.9,'q0':192,'m_q':1.8,'local_frac':.2,'fast_frac':.75,'tau_fast':60.,'tau_slow':365.}
LAG=28; WIN=14; KCOL=29.97970644952428; KHYD=1.2655398852182516

def main():
 F,_,_=forcing(); _,d=sim(F,P,True)
 dt=pd.to_datetime(F['date']);yr=dt.year.to_numpy();mo=dt.month.to_numpy();pes=np.asarray(F['pes'],float)
 ar=d.area_m2.to_numpy(float);ddt=pd.to_datetime(d.date);dyr=ddt.dt.year.to_numpy();dmo=ddt.dt.month.to_numpy()
 deficit=np.maximum(0.,(A0-ar)/A0);lag=np.r_[np.zeros(LAG),deficit[:-LAG]];state=np.cumsum(lag/365.)
 roll=pd.Series(pes,index=dt).rolling(WIN,min_periods=1).sum().to_numpy();ref=float(roll[(yr==2011)&np.isin(mo,[5,6])].mean());anom=roll-ref
 out={}
 for y in range(2011,2024):
  S=float(state[(dyr==y)&np.isin(dmo,[5,6])].mean());H=float(anom[(yr==y)&np.isin(mo,[5,6])].mean());pred=A0-KCOL*S+KHYD*H
  out[y]={'state':S,'runoff_anom_mm':H,'colonization_effect_m2':KCOL*S,'hydrology_effect_m2':KHYD*H,'pred_open_water_m2':pred}
 e=out[2022]['pred_open_water_m2']-OBS2022
 summary={'locked_stage34':{'hydrology':P,'lag_days':LAG,'runoff_window_days':WIN,'k_col':KCOL,'k_hyd':KHYD,'exposure_power':1.0},'2022_excluded_holdout':{'observed_m2':OBS2022,**out[2022],'error_m2':e,'abs_error_m2':abs(e),'relative_error_pct':abs(e)/OBS2022*100},'all_year_predictions':out,'note':'2022 was not used in calibration or Stage34 model selection.'}
 (OUT/'stage34_holdout_2022.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
