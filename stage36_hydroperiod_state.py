#!/usr/bin/env python3
"""Stage36: exact daily water balance + hydroperiod-driven ecological state.

Hydrologic core is unchanged from Stage35C. Ecology no longer responds to the
magnitude of an empirical area deficit. It responds to exposure frequency:
  I_exposed(t)=1 when the storage-derived hydrologic area is below A2011,
  E28=mean(I_exposed) over the antecedent 28 d,
  dx/dt=(r_est/365)*E28*(1-x).
This is a bounded colonisation state driven by hydroperiod/drawdown duration.
Short-term hydrologic contribution is taken only from conserved return-flow or
surface-inflow fluxes. No CN, TOPMODEL, lambda, cap, freeboard, year term, or
future leakage; 2022 excluded from fit/selection.
"""
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing,OBS
from stage35c_mass_balance_state_operator import hydro,A0
OUT=Path('stage36_outputs');OUT.mkdir(exist_ok=True)
YEARS=np.array(sorted(OBS),int);Y=np.array([OBS[int(y)] for y in YEARS],float)
V0S=[800.,1200.,1600.,2400.];PS=[4.,8.,12.,20.];TS=[60.,120.,240.];LOCAL=[.1,.2,.3,.4];TF=[15.,30.,60.]
RE=[.025,.05,.1,.2,.5,1.0];WINDOWS=[7,14,30];FEATURES=['return_flow','surface_inflow'];LAG=28

def hydroperiod_state(area,r):
    exposed=(np.asarray(area)<A0).astype(float)
    e28=pd.Series(exposed).rolling(LAG,min_periods=LAG).mean().fillna(0).to_numpy()
    x=0.;st=np.empty(len(area))
    for i,e in enumerate(e28):
        x=np.clip(x+(r/365.)*e*(1-x),0,1);st[i]=x
    return st,exposed,e28

def ann(dt,x):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy();return np.array([float(np.mean(x[(yr==y)&np.isin(mo,[5,6])])) for y in YEARS])
def feature(dt,q,w):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy();r=pd.Series(q,index=dt).rolling(w,min_periods=1).sum().to_numpy();ref=float(np.mean(r[(yr==2011)&np.isin(mo,[5,6])]))
    return np.array([float(np.mean(r[(yr==y)&np.isin(mo,[5,6])])-ref) for y in YEARS])
def fit(S,H,y=Y):
    X=np.c_[-S,H];t=y-A0;c=[];b=np.linalg.lstsq(X,t,rcond=None)[0]
    if 0<=b[0]<=A0 and b[1]>=0:c.append(b)
    d=np.dot(S,S);kc=np.clip(np.dot(-S,t)/d if d else 0,0,A0);c.append(np.array([kc,0.]))
    d=np.dot(H,H);kh=max(0,np.dot(H,t)/d) if d else 0;c.append(np.array([0.,kh]));c.append(np.array([0.,0.]))
    bb=min(c,key=lambda z:float(np.sum((A0+X@z-y)**2)));return bb,A0+X@bb
def score(p):
    rm=float(np.sqrt(np.mean((p-Y)**2)));return rm,100*rm/Y.mean(),float(np.mean(np.abs(p-Y)))
def cv(S,H):
    pp=[]
    for i in range(6):
        k=np.arange(6)!=i;b,_=fit(S[k],H[k],Y[k]);pp.append(float(A0+np.array([-S[i],H[i]])@b))
    pp=np.array(pp);rm=float(np.sqrt(np.mean((pp-Y)**2)));return rm,100*rm/Y.mean(),pp

def main():
    F,_,_=forcing();rows=[]
    for V0,p,ts,lf,tf in itertools.product(V0S,PS,TS,LOCAL,TF):
        hp={'V0':V0,'p_shape':p,'tau_surf':ts,'local_frac':lf,'tau_fast':tf};h=hydro(F,hp)
        for re in RE:
            st,ex,e28=hydroperiod_state(h['area'],re);S=ann(h['dates'],st);corr=float(np.corrcoef(S,YEARS)[0,1]) if np.std(S)>0 else 1
            for ft,w in itertools.product(FEATURES,WINDOWS):
                H=feature(h['dates'],h[ft],w);b,pred=fit(S,H);rm,nrm,mae=score(pred);crm,cn,cp=cv(S,H);hr=float(b[1]*(H.max()-H.min()))
                rows.append({'nrmse':nrm,'rmse':rm,'mae':mae,'loocv_nrmse':cn,'loocv_rmse':crm,**hp,'r_est_yr':re,'hydro_feature':ft,'hydro_window_d':w,'K_colonizable_m2':b[0],'K_hydro':b[1],'hydro_effect_range_m2':hr,'state_year_corr':corr,'max_mass_error_m3':h['mass_error'],
                             **{f'pred_{y}':pred[j] for j,y in enumerate(YEARS)},**{f'cv_{y}':cp[j] for j,y in enumerate(YEARS)},**{f'state_{y}':S[j] for j,y in enumerate(YEARS)},**{f'hydro_anom_{y}':H[j] for j,y in enumerate(YEARS)}})
    feasible=[z for z in rows if z['nrmse']<=2 and z['max_mass_error_m3']<1e-8]
    positive=[z for z in feasible if z['K_hydro']>0]
    lowcorr=[z for z in positive if z['state_year_corr']<.99]
    key=lambda z:(z['loocv_nrmse'],z['nrmse'])
    out={'model':'Stage36 exact balance + hydroperiod-driven bounded colonisation','n_candidates':len(rows),'n_feasible':len(feasible),'n_positive_hydro':len(positive),'n_positive_hydro_corr_lt_099':len(lowcorr),
         'best_any':sorted(feasible,key=key)[0] if feasible else sorted(rows,key=lambda z:z['nrmse'])[0],
         'best_positive_hydro':sorted(positive,key=key)[0] if positive else None,
         'best_positive_hydro_corr_lt_099':sorted(lowcorr,key=key)[0] if lowcorr else None,
         'rules':{'exact_daily_water_balance':True,'CN':False,'TOPMODEL':False,'lambda':0,'hard_cap':False,'freeboard':False,'explicit_time':False,'future_leakage':False,'2022_fit':False,
                  'ecology':'bounded colonisation driven by antecedent 28-d exposure frequency/hydroperiod','hydrology':'only conserved return-flow or surface-inflow flux'}}
    pd.DataFrame(sorted(rows,key=lambda z:(z['nrmse'],z['loocv_nrmse']))[:1000]).to_csv(OUT/'top1000.csv',index=False)
    pd.DataFrame(sorted(feasible,key=key)[:1000]).to_csv(OUT/'feasible.csv',index=False)
    (OUT/'stage36_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
