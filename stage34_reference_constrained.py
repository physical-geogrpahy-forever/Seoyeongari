#!/usr/bin/env python3
import json,itertools
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing,sim,OBS

OUT=Path('stage34_outputs'); OUT.mkdir(exist_ok=True)
YEARS=np.array(sorted(OBS),int); Y=np.array([OBS[int(y)] for y in YEARS],float)
A0=2241.762
# Literature-constrained constants:
# (1) linear exposure response: no fitted power transform;
# (2) 28 d establishment lag: drawdown colonisation occurs on weeks scale;
# (3) persistent exposure/colonisation state: consistent with observed Seoyeongari terrestrialisation/peat accumulation;
# (4) 14 d antecedent runoff anomaly: Jeju temporary wetlands respond to rainfall within hours,
#     while temporary-pond studies explicitly support a 1-15 d rainfall response component.
LAG=28; RUNOFF_WINDOW=14
# Process settings retained from Stage33. They are NOT re-tuned here, to avoid using extra hydrologic degrees of freedom.
LOCAL_FRAC=.20; FAST_FRAC=.75; TAU_FAST=60.; TAU_SLOW=365.
# Only the three TOPMODEL wetness-response parameters are screened.
M_AREA=[.4,.5,.6,.7,.8,.9,1.0,1.1,1.2,1.35,1.5,1.7,2.0,2.3]
Q0=[24,32,40,48,56,64,80,96,112,128,160,192]
M_Q=[.3,.4,.5,.6,.7,.8,.9,1.0,1.2,1.5,1.8]

def fit_sign(X,y):
    target=y-A0; cand=[]
    b=np.linalg.lstsq(X,target,rcond=None)[0]
    if b[0]<=0 and b[1]>=0: cand.append(b)
    bc=np.linalg.lstsq(X[:,0,None],target,rcond=None)[0][0]
    if bc<=0: cand.append(np.array([bc,0.]))
    bh=np.linalg.lstsq(X[:,1,None],target,rcond=None)[0][0]
    if bh>=0: cand.append(np.array([0.,bh]))
    cand.append(np.array([0.,0.]))
    bb=min(cand,key=lambda z:float(np.sum((A0+X@z-y)**2)))
    return bb,A0+X@bb

def cv(X):
    p=[]
    for i in range(6):
        keep=np.arange(6)!=i; b,_=fit_sign(X[keep],Y[keep]); p.append(float(A0+X[i]@b))
    p=np.array(p); rm=float(np.sqrt(np.mean((p-Y)**2))); return rm,rm/Y.mean()*100,p

def main():
    F,missing,annual=forcing(); fdt=pd.to_datetime(F['date']); fyr=fdt.year.to_numpy(); fmo=fdt.month.to_numpy(); pes=np.asarray(F['pes'],float)
    roll=pd.Series(pes,index=fdt).rolling(RUNOFF_WINDOW,min_periods=1).sum().to_numpy()
    ref=float(roll[(fyr==2011)&np.isin(fmo,[5,6])].mean())
    H=np.array([float((roll-ref)[(fyr==y)&np.isin(fmo,[5,6])].mean()) for y in YEARS])
    rows=[]
    for ma,q0,mq in itertools.product(M_AREA,Q0,M_Q):
        p={'m_area':ma,'q0':q0,'m_q':mq,'local_frac':LOCAL_FRAC,'fast_frac':FAST_FRAC,'tau_fast':TAU_FAST,'tau_slow':TAU_SLOW}
        rr,d=sim(F,p,True); ar=d.area_m2.to_numpy(float); dt=pd.to_datetime(d.date); yr=dt.dt.year.to_numpy(); mo=dt.dt.month.to_numpy()
        deficit=np.maximum(0.0,(A0-ar)/A0)
        lagged=np.r_[np.zeros(LAG),deficit[:-LAG]]
        state=np.cumsum(lagged/365.0)
        S=np.array([float(state[(yr==y)&np.isin(mo,[5,6])].mean()) for y in YEARS])
        X=np.c_[S,H]
        b,pred=fit_sign(X,Y); rm=float(np.sqrt(np.mean((pred-Y)**2))); nrm=rm/Y.mean()*100
        cv_rm,cv_nrm,cvp=cv(X)
        rows.append({'nrmse':nrm,'rmse':rm,'loocv_nrmse':cv_nrm,'loocv_rmse':cv_rm,**p,
                     'k_colonization_m2_per_state':-b[0],'k_runoff_m2_per_mm':b[1],'raw_topmodel_nrmse':rr['nrmse'],
                     **{f'pred_{y}':pred[j] for j,y in enumerate(YEARS)},**{f'cv_{y}':cvp[j] for j,y in enumerate(YEARS)},
                     **{f'state_{y}':S[j] for j,y in enumerate(YEARS)},**{f'runoff_anom_{y}':H[j] for j,y in enumerate(YEARS)}})
    feasible=[r for r in rows if r['nrmse']<=1.2 and r['k_colonization_m2_per_state']>=0 and r['k_runoff_m2_per_mm']>=0]
    chosen=sorted(feasible,key=lambda r:(r['loocv_nrmse'],r['nrmse']))[0] if feasible else sorted(rows,key=lambda r:(r['nrmse'],r['loocv_nrmse']))[0]
    pd.DataFrame(sorted(rows,key=lambda r:r['nrmse'])[:300]).to_csv(OUT/'accuracy_top300.csv',index=False)
    pd.DataFrame(sorted(feasible,key=lambda r:(r['loocv_nrmse'],r['nrmse']))[:300]).to_csv(OUT/'feasible_cv_top300.csv',index=False)
    summary={'model':'Stage34 reference-constrained parsimonious hydro-ecology','selection':'among nRMSE<=1.2%, minimize LOOCV nRMSE','n_candidates':len(rows),'n_feasible':len(feasible),'best':chosen,
             'fixed_reference_constraints':{'exposure_power':1.0,'establishment_lag_days':LAG,'annual_memory':1.0,'runoff_window_days':RUNOFF_WINDOW,'local_frac':LOCAL_FRAC,'fast_frac':FAST_FRAC,'tau_fast_d':TAU_FAST,'tau_slow_d':TAU_SLOW,'flood_reversal':'not fitted because unidentifiable in Stage33'},
             'rules':{'lambda':0,'explicit_time':False,'future_leakage':False,'hard_cap':False,'freeboard':False,'A2011_fixed_anchor_m2':A0,'colonization_sign':'reduces open water','runoff_sign':'increases open water','TOPMODEL_role':'wetness/exposure proxy only'},
             'benchmarks':{'Stage33_nrmse':1.0146033059223625,'Stage33_LOOCV':1.3324610253954587,'Stage33_power1_previous_nrmse':1.1416779996167894,'Stage33_power1_previous_LOOCV':1.4893474274843717}}
    (OUT/'stage34_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
