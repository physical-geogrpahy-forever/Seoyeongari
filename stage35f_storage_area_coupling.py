#!/usr/bin/env python3
"""Stage35F: exact-water-balance model with hydrologic-area anomaly coupling.

Hydrology is unchanged from Stage35C and closes exactly each day.
The only hydrologic predictor of mapped open water is the May-Jun anomaly of
Hayashi-van der Kamp storage-derived hydrologic area itself:

 A_open = A2011 - Kc*C + kA*(A_hydro - A_hydro,2011)

C is bounded colonisation driven by 28-d antecedent exposure from the same
storage-area state. 0<=kA<=1 is a physical attenuation constraint: a change in
hydrologically inundated area cannot create a larger open-water area change.
No CN, TOPMODEL, lambda, hard cap, freeboard, time trend, future leakage.
2022 is excluded from fitting and selection.
"""
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing,OBS
from stage35c_mass_balance_state_operator import hydro,colon_state,A0,A_WET

OUT=Path('stage35f_outputs');OUT.mkdir(exist_ok=True)
YEARS=np.array(sorted(OBS),int); Y=np.array([OBS[int(y)] for y in YEARS],float)
V0S=[800.,1200.,1600.,2400.];PS=[4.,8.,12.,20.];TS=[60.,120.,240.];LOCAL=[.1,.2,.3,.4];TF=[15.,30.,60.];RE=[.05,.1,.2,.5,1.0]

def ann(dt,x,years=YEARS):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy()
    return np.array([float(np.mean(x[(yr==y)&np.isin(mo,[5,6])])) for y in years])

def area_anom(dt,a,years=YEARS):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy();ref=float(np.mean(a[(yr==2011)&np.isin(mo,[5,6])]))
    return np.array([float(np.mean(a[(yr==y)&np.isin(mo,[5,6])])-ref) for y in years]),ref

def fit(S,H,y=Y):
    # y=A0-Kc*S+kA*H; 0<=Kc<=A0, 0<=kA<=1.
    X=np.c_[-S,H];t=y-A0;c=[]
    b=np.linalg.lstsq(X,t,rcond=None)[0]
    if 0<=b[0]<=A0 and 0<=b[1]<=1:c.append(b)
    d=np.dot(S,S);kc=np.clip(np.dot(-S,t)/d if d else 0,0,A0);c.append(np.array([kc,0.]))
    d=np.dot(H,H);ka=np.clip(np.dot(H,t)/d if d else 0,0,1);c.append(np.array([0.,ka]));c.append(np.array([0.,0.]))
    # boundary kA=1 with fitted Kc can be optimum under box constraint
    t1=t-H; d=np.dot(S,S);kc1=np.clip(np.dot(-S,t1)/d if d else 0,0,A0);c.append(np.array([kc1,1.]))
    bb=min(c,key=lambda z:float(np.sum((A0+X@z-y)**2)));return bb,A0+X@bb

def score(p,y=Y):
    rm=float(np.sqrt(np.mean((p-y)**2)));return rm,100*rm/y.mean(),float(np.mean(np.abs(p-y)))
def cv(S,H):
    pp=[]
    for i in range(6):
        k=np.arange(6)!=i;b,_=fit(S[k],H[k],Y[k]);pp.append(float(A0+np.array([-S[i],H[i]])@b))
    pp=np.array(pp);rm=float(np.sqrt(np.mean((pp-Y)**2)));return rm,100*rm/Y.mean(),pp

def main():
    F,_,_=forcing();rows=[]
    for V0,p,ts,lf,tf in itertools.product(V0S,PS,TS,LOCAL,TF):
        hp={'V0':V0,'p_shape':p,'tau_surf':ts,'local_frac':lf,'tau_fast':tf};h=hydro(F,hp);H,refA=area_anom(h['dates'],h['area'])
        for re in RE:
            st,ex,e28=colon_state(h['area'],re);S=ann(h['dates'],st);corr=float(np.corrcoef(S,YEARS)[0,1]) if np.std(S)>0 else 1.
            b,pred=fit(S,H);rm,nrm,mae=score(pred);crm,cn,cp=cv(S,H);hrange=float(b[1]*(H.max()-H.min()))
            rows.append({'nrmse':nrm,'rmse':rm,'mae':mae,'loocv_nrmse':cn,'loocv_rmse':crm,**hp,'r_exposure_yr':re,'K_colonizable_m2':b[0],'k_hydrologic_area':b[1],
                         'hydro_effect_range_m2':hrange,'hydro_ref2011_m2':refA,'state_year_corr':corr,'max_mass_error_m3':h['mass_error'],
                         **{f'pred_{y}':pred[j] for j,y in enumerate(YEARS)},**{f'cv_{y}':cp[j] for j,y in enumerate(YEARS)},
                         **{f'state_{y}':S[j] for j,y in enumerate(YEARS)},**{f'hydro_area_anom_{y}':H[j] for j,y in enumerate(YEARS)}})
    feasible=[z for z in rows if z['nrmse']<=2 and z['max_mass_error_m3']<1e-8 and z['state_year_corr']<.995]
    positive=[z for z in feasible if z['k_hydrologic_area']>0]
    best=sorted(feasible,key=lambda z:(z['loocv_nrmse'],z['nrmse']))[0] if feasible else sorted(rows,key=lambda z:(z['nrmse'],z['loocv_nrmse']))[0]
    bestpos=sorted(positive,key=lambda z:(z['loocv_nrmse'],z['nrmse']))[0] if positive else None
    pd.DataFrame(sorted(rows,key=lambda z:(z['nrmse'],z['loocv_nrmse']))[:1000]).to_csv(OUT/'top1000.csv',index=False)
    pd.DataFrame(sorted(feasible,key=lambda z:(z['loocv_nrmse'],z['nrmse']))[:1000]).to_csv(OUT/'feasible.csv',index=False)
    out={'model':'Stage35F exact balance + storage-derived hydrologic-area coupling','n_candidates':len(rows),'n_feasible':len(feasible),'n_positive_hydro':len(positive),'best_any':best,'best_positive_hydro':bestpos,
         'equation':'Aopen=A2011-Kc*C+kA*(Ahydro-Ahydro2011), 0<=kA<=1',
         'rules':{'exact_daily_water_balance':True,'CN':False,'TOPMODEL':False,'lambda':0,'hard_cap':False,'freeboard':False,'explicit_time':False,'future_leakage':False,'2022_fit':False,
                  'storage_area':'Hayashi & van der Kamp power-law relation applied to conserved surface storage','hydro_area_transmission':'0<=kA<=1'}}
    (OUT/'stage35f_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
