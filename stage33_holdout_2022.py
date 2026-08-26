#!/usr/bin/env python3
import json
import numpy as np
import pandas as pd
from pathlib import Path
from stage31_topmodel_vsa import forcing,sim

OUT=Path('stage33_holdout_outputs'); OUT.mkdir(exist_ok=True)
A0=2241.762
# Locked Stage 33 selected structure/parameters; 2022 is NOT used to calibrate any value here.
P={'m_area':1.2,'q0':96,'m_q':1.0,'local_frac':.2,'fast_frac':.75,'tau_fast':60.,'tau_slow':365.}
POWER=.5; MEM=1.0; REV=0.; LAG=28; WIN=14
KCOL=40.22838515463677; KHYD=1.2859145002309402
OBS2022=1988.560

def main():
 F,_,_=forcing(); rr,d=sim(F,P,True)
 dt=pd.to_datetime(F['date']); yr=dt.year.to_numpy(); mo=dt.month.to_numpy(); pes=np.asarray(F['pes'],float)
 ar=d.area_m2.to_numpy(float); ddt=pd.to_datetime(d.date); dyr=ddt.dt.year.to_numpy(); dmo=ddt.dt.month.to_numpy()
 deficit=np.maximum(0,(A0-ar)/A0)**POWER; excess=np.maximum(0,(ar-A0)/A0)**POWER
 de=np.r_[np.zeros(LAG),deficit[:-LAG]]; ex=np.r_[np.zeros(LAG),excess[:-LAG]]
 md=MEM**(1/365.0); state=np.zeros(len(ar)); c=0.
 for i in range(len(ar)):
  c=max(0.,md*c+(de[i]-REV*ex[i])/365.); state[i]=c
 roll=pd.Series(pes,index=dt).rolling(WIN,min_periods=1).sum().to_numpy(); ref=float(roll[(yr==2011)&np.isin(mo,[5,6])].mean()); Ranom=roll-ref
 out={}
 for y in range(2011,2024):
  m=(yr==y)&np.isin(mo,[5,6]); md2=(dyr==y)&np.isin(dmo,[5,6])
  S=float(state[md2].mean()); H=float(Ranom[m].mean()); pred=A0-KCOL*S+KHYD*H
  out[y]={'state':S,'runoff_anom_mm':H,'colonization_effect_m2':KCOL*S,'hydrology_effect_m2':KHYD*H,'pred_open_water_m2':pred}
 err=out[2022]['pred_open_water_m2']-OBS2022
 summary={'locked_from_stage33':{'hydrology':P,'power':POWER,'memory':MEM,'reversal':REV,'lag_days':LAG,'runoff_window_days':WIN,'k_col':KCOL,'k_hyd':KHYD},
          '2022_excluded_holdout':{'observed_m2':OBS2022,**out[2022],'error_m2':err,'abs_error_m2':abs(err),'relative_error_pct':abs(err)/OBS2022*100},
          'all_year_predictions':out,'note':'2022 observation was not used in Stage33 fitting or selection.'}
 (OUT/'stage33_holdout_2022.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
