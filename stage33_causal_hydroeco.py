#!/usr/bin/env python3
import json,itertools
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing,sim,OBS

OUT=Path('stage33_outputs'); OUT.mkdir(exist_ok=True)
YEARS=np.array(sorted(OBS),int); Y=np.array([OBS[int(y)] for y in YEARS],float); A0=2241.762
CAND=[]
for ma,q0,mq in [(0.8,48,.5),(0.8,64,.6),(1.0,48,.6),(1.0,64,.6),(1.0,64,.8),(1.0,96,.8),(1.2,48,.6),(1.2,64,.8),(1.2,96,1.0),(1.5,48,.8),(1.5,64,1.0),(1.5,96,1.0)]:
 CAND.append({'m_area':ma,'q0':q0,'m_q':mq,'local_frac':.2,'fast_frac':.75,'tau_fast':60.,'tau_slow':365.})

# Ecological response: water-regime exposure accumulated causally, with 4-8 week establishment lag.
POW=[.5,1.,1.5,2.]; MEM=[.90,.95,.975,.99,1.0]; REV=[0,.1,.25,.5]; LAGS=[28,56]
# Hydrologic response: antecedent effective runoff, positive effect only.
WINDOWS=[14,30,60,90]

def fit_fixed(X,y):
    # A = A0 + X*[b_state,b_hyd]; require b_state<=0 and b_hyd>=0.
    targ=y-A0; cand=[]
    b=np.linalg.lstsq(X,targ,rcond=None)[0]
    if b[0]<=0 and b[1]>=0:cand.append(b)
    bs=np.linalg.lstsq(X[:,0,None],targ,rcond=None)[0][0]
    if bs<=0:cand.append(np.array([bs,0.]))
    bh=np.linalg.lstsq(X[:,1,None],targ,rcond=None)[0][0]
    if bh>=0:cand.append(np.array([0.,bh]))
    cand.append(np.array([0.,0.]))
    bb=min(cand,key=lambda q:float(np.sum((A0+X@q-y)**2)))
    return bb,A0+X@bb

def loocv(X):
    out=[]
    for i in range(len(Y)):
        k=np.arange(len(Y))!=i; b,_=fit_fixed(X[k],Y[k]); out.append(float(A0+X[i]@b))
    out=np.array(out); rm=float(np.sqrt(np.mean((out-Y)**2))); return rm,rm/Y.mean()*100,out

def main():
    F,missing,annual=forcing(); dt=pd.to_datetime(F['date']); pes=np.asarray(F['pes'],float)
    yr=dt.year.to_numpy(); mo=dt.month.to_numpy()
    # causal antecedent runoff index; center to 2011 May-Jun mean to keep 2011 observed area as physical anchor
    R={}
    s=pd.Series(pes,index=dt)
    for w in WINDOWS:
        roll=s.rolling(w,min_periods=1).sum().to_numpy()
        ref=float(roll[(yr==2011)&np.isin(mo,[5,6])].mean())
        R[w]=roll-ref
    rows=[]
    for p in CAND:
        rr,d=sim(F,p,True); ar=d.area_m2.to_numpy(float); ddt=pd.to_datetime(d.date); dyr=ddt.dt.year.to_numpy(); dmo=ddt.dt.month.to_numpy()
        # date alignment is identical by construction
        for power,mem,rev,lag in itertools.product(POW,MEM,REV,LAGS):
            deficit=np.maximum(0,(A0-ar)/A0)**power
            excess=np.maximum(0,(ar-A0)/A0)**power
            # causal state: today's establishment responds to exposure lagged by 4 or 8 weeks.
            de=np.r_[np.zeros(lag),deficit[:-lag]]; ex=np.r_[np.zeros(lag),excess[:-lag]]
            md=mem**(1/365.0)
            state=np.zeros(len(ar)); c=0.0
            for i in range(len(ar)):
                c=max(0.0,md*c + (de[i]-rev*ex[i])/365.0)
                state[i]=c
            # May-Jun mean state per target year
            S=np.array([float(state[(dyr==y)&np.isin(dmo,[5,6])].mean()) for y in YEARS])
            for w in WINDOWS:
                H=np.array([float(R[w][(yr==y)&np.isin(mo,[5,6])].mean()) for y in YEARS])
                X=np.c_[S,H]
                b,pred=fit_fixed(X,Y); rm=float(np.sqrt(np.mean((pred-Y)**2))); nrm=rm/Y.mean()*100
                cv_rm,cv_nrm,cv=loocv(X)
                rows.append({'nrmse':nrm,'rmse':rm,'loocv_nrmse':cv_nrm,'loocv_rmse':cv_rm,'power':power,'annual_memory':mem,'flood_reversal':rev,'establishment_lag_days':lag,'runoff_window_days':w,
                             **p,'k_colonization_m2_per_state':-b[0],'k_runoff_m2_per_mm':b[1],'raw_topmodel_nrmse':rr['nrmse'],
                             **{f'pred_{y}':pred[j] for j,y in enumerate(YEARS)},**{f'cv_{y}':cv[j] for j,y in enumerate(YEARS)},
                             **{f'state_{y}':S[j] for j,y in enumerate(YEARS)},**{f'runoff_anom_{y}':H[j] for j,y in enumerate(YEARS)}})
    # Decision rule: preserve nRMSE<=1.2 if possible, then choose lowest LOOCV; tie-break by nRMSE.
    feasible=[r for r in rows if r['nrmse']<=1.2 and r['k_colonization_m2_per_state']>=0 and r['k_runoff_m2_per_mm']>=0]
    pool=feasible if feasible else rows
    pool.sort(key=lambda r:(r['loocv_nrmse'],r['nrmse']))
    best=pool[0]
    rows.sort(key=lambda r:r['nrmse']); pd.DataFrame(rows[:200]).to_csv(OUT/'stage33_accuracy_top200.csv',index=False)
    pd.DataFrame(sorted(feasible,key=lambda r:(r['loocv_nrmse'],r['nrmse']))[:200]).to_csv(OUT/'stage33_feasible_cv_top200.csv',index=False)
    summary={'selection_rule':'among nRMSE<=1.2%, minimize LOOCV nRMSE; no future information','best':best,'n_feasible':len(feasible),
             'benchmarks':{'stage31b_time_nrmse':0.7692692574776534,'stage31c_noncausal_nrmse':1.0969697397128737,'stage31e_noncausal_nrmse':1.001791458580214},
             'rules':{'lambda':0,'explicit_time':False,'hard_cap':False,'freeboard':False,'intercept_fixed_to_2011_area_m2':A0,
                      'ecology':'causal exposure accumulation; 28/56 d lag; flooding reversal allowed','hydrology':'TOPMODEL wetness used as exposure driver plus positive antecedent SCS runoff anomaly','future_leakage':False,
                      'coefficient_signs':'colonization reduces open water; runoff increases open water'}}
    (OUT/'stage33_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
