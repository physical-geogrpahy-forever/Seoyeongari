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
# - linear exposure response (no fitted power transform)
# - 28 d establishment lag (drawdown colonisation is demonstrably rapid on ~weeks scale)
# - persistent colonisation over 2011-2023; no annual decay fitted because Seoyeongari evidence is terrestrialisation/peat accumulation
# - 14 d antecedent runoff anomaly for short-term response; Jeju temporary wetlands respond within hours and temporary-pond literature supports 1-15 d rainfall windows
LAG=28; RUNOFF_WINDOW=14

# Broader TOPMODEL wetness-proxy grid. These parameters shape hydrologic exposure only; output is never treated as absolute pond area.
M_AREA=[.5,.65,.8,1.0,1.2,1.5,1.8,2.2]
Q0=[32,48,64,80,96,128,160]
M_Q=[.4,.5,.6,.8,1.0,1.2,1.5]
LOCAL=[.1,.2,.3]
FAST=[.5,.75]
TAUF=[30.,60.,120.]
TAUS=[365.,730.]

def fit_sign(X,y):
    # Physical anchor fixed to 2011 observed open-water area.
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
    total=0
    for ma,q0,mq,lf,ff,tf,ts in itertools.product(M_AREA,Q0,M_Q,LOCAL,FAST,TAUF,TAUS):
        # avoid clearly redundant combinations only; no result-based pruning
        p={'m_area':ma,'q0':q0,'m_q':mq,'local_frac':lf,'fast_frac':ff,'tau_fast':tf,'tau_slow':ts}
        rr,d=sim(F,p,True); ar=d.area_m2.to_numpy(float); dt=pd.to_datetime(d.date); yr=dt.dt.year.to_numpy(); mo=dt.dt.month.to_numpy()
        deficit=np.maximum(0.0,(A0-ar)/A0)  # LINEAR, reference-constrained
        lagged=np.r_[np.zeros(LAG),deficit[:-LAG]]
        # persistent causal exposure integral; no flood-reversal coefficient is fitted because this term was unidentifiable in Stage33
        state=np.cumsum(lagged/365.0)
        S=np.array([float(state[(yr==y)&np.isin(mo,[5,6])].mean()) for y in YEARS])
        X=np.c_[S,H]
        b,pred=fit_sign(X,Y); rm=float(np.sqrt(np.mean((pred-Y)**2))); nrm=rm/Y.mean()*100
        cv_rm,cv_nrm,cvp=cv(X)
        rows.append({'nrmse':nrm,'rmse':rm,'loocv_nrmse':cv_nrm,'loocv_rmse':cv_rm,**p,
                     'k_colonization_m2_per_state':-b[0],'k_runoff_m2_per_mm':b[1],'raw_topmodel_nrmse':rr['nrmse'],
                     **{f'pred_{y}':pred[j] for j,y in enumerate(YEARS)},**{f'cv_{y}':cvp[j] for j,y in enumerate(YEARS)},
                     **{f'state_{y}':S[j] for j,y in enumerate(YEARS)},**{f'runoff_anom_{y}':H[j] for j,y in enumerate(YEARS)}})
        total+=1
    feasible=[r for r in rows if r['nrmse']<=1.2 and r['k_colonization_m2_per_state']>=0 and r['k_runoff_m2_per_mm']>=0]
    if feasible:
        chosen=sorted(feasible,key=lambda r:(r['loocv_nrmse'],r['nrmse']))[0]
    else:
        chosen=sorted(rows,key=lambda r:(r['nrmse'],r['loocv_nrmse']))[0]
    pd.DataFrame(sorted(rows,key=lambda r:r['nrmse'])[:300]).to_csv(OUT/'accuracy_top300.csv',index=False)
    pd.DataFrame(sorted(feasible,key=lambda r:(r['loocv_nrmse'],r['nrmse']))[:300]).to_csv(OUT/'feasible_cv_top300.csv',index=False)
    summary={'model':'Stage34 reference-constrained parsimonious hydro-ecology','selection':'if nRMSE<=1.2, minimize LOOCV','n_candidates':total,'n_feasible':len(feasible),'best':chosen,
             'fixed_reference_constraints':{'exposure_power':1.0,'establishment_lag_days':LAG,'annual_memory':1.0,'runoff_window_days':RUNOFF_WINDOW,'flood_reversal':'not fitted; unidentifiable in Stage33'},
             'rules':{'lambda':0,'explicit_time':False,'future_leakage':False,'hard_cap':False,'freeboard':False,'A2011_fixed_anchor_m2':A0,
                      'colonization_sign':'negative effect on open water','runoff_sign':'positive effect on open water','TOPMODEL_role':'wetness/exposure proxy, not absolute pond area'},
             'benchmarks':{'Stage33_nrmse':1.0146033059223625,'Stage33_LOOCV':1.3324610253954587,'Stage33_power1_previous_nrmse':1.1416779996167894,'Stage33_power1_previous_LOOCV':1.4893474274843717}}
    (OUT/'stage34_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
