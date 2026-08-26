#!/usr/bin/env python3
"""Stage 35C — exact daily water balance; both ecology and short-term hydro signal
are derived only from conserved water-balance states/fluxes.

Final observation model (A0 fixed; no intercept/time term):
    A_open,y = A0 - Kc * C_y + Kh * H_y
where
    C: bounded first-order colonisation state driven by 28-d antecedent exposure
       computed from the Hayashi storage-area state;
    H: antecedent anomaly of a water-balance flux/state (return flow or total
       surface inflow), relative to the same May-Jun window in 2011.
Kc>=0, Kh>=0, Kc<=A0.  Both drivers come from the exact daily water balance.

No CN, TOPMODEL, lambda, hard cap, freeboard, explicit year, or future leakage.
2022 is absent from fit/selection.
"""
import itertools, json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing, OBS

OUT=Path('stage35c_outputs'); OUT.mkdir(exist_ok=True)
YEARS=np.array(sorted(OBS),int); Y=np.array([OBS[int(y)] for y in YEARS],float)
A0=2241.762; A_EXT=8483.0; A_WET=5939.5
SOIL_DEPTH=.294*.55; C_EXT=SOIL_DEPTH*A_EXT; C_WET=SOIL_DEPTH*A_WET
ET_EXT=.95; FAST_FRAC=.75; TAU_SLOW=365.; EST_LAG=28

# Modest reference-constrained hydrologic screen around the Stage35B family.
V0S=[800.,1200.,1600.,2400.]
PS=[4.,8.,12.,20.]
TAU_SURF=[60.,120.,240.]
LOCAL=[.10,.20,.30,.40]
TAU_FAST=[15.,30.,60.]
# Bounded first-order colonisation rate per exposure-year.
R_E=[.05,.10,.20,.50,1.0,2.0]
# Fast response windows. Jeju temporary wetlands respond within hours; multi-day
# windows integrate event/recharge effects without using future information.
WINDOWS=[7,14,30]
FEATURES=['return_flow','surface_inflow']

def area_v(v,V0,p):
    if v<=0:return 0.
    return min(A_WET,A0*(v/V0)**(2./(p+2.)))

def hydro(F,p):
    pre=np.asarray(F['pre'],float); eto=np.asarray(F['eto'],float); ep=np.asarray(F['ep'],float); dt=pd.to_datetime(F['date']); n=len(pre)
    se=.5*C_EXT; sw=.5*C_WET; fast=slow=0.; surf=p['V0']; prev=se+sw+fast+slow+surf
    area=np.empty(n); V=np.empty(n); qret=np.empty(n); sin=np.empty(n); qout=np.empty(n); maxerr=0.
    for i in range(n):
        ap=area_v(surf,p['V0'],p['p_shape'])
        pext=pre[i]*A_EXT/1000.; popen=pre[i]*ap/1000.; pwet=pre[i]*(A_WET-ap)/1000.
        se+=pext; e1=min(se,ET_EXT*eto[i]*A_EXT/1000.);se-=e1; dex=max(se-C_EXT,0.);se-=dex
        sw+=pwet; e2=min(sw,eto[i]*(A_WET-ap)/1000.);sw-=e2; dw=max(sw-C_WET,0.);sw-=dw
        local=dex*p['local_frac']; deep=dex-local; fast+=local*FAST_FRAC; slow+=local*(1-FAST_FRAC)
        qf=min(fast,fast/p['tau_fast']); qs=min(slow,slow/TAU_SLOW);fast-=qf;slow-=qs; qr=qf+qs
        surface_in=popen+dw+qr; surf+=surface_in
        eo=min(surf,ep[i]*ap/1000.);surf-=eo; qo=min(surf,surf/p['tau_surf']);surf-=qo
        an=area_v(surf,p['V0'],p['p_shape'])
        total=se+sw+fast+slow+surf; inputs=pext+popen+pwet; outputs=e1+e2+eo+deep+qo
        err=prev+inputs-outputs-total;maxerr=max(maxerr,abs(err));prev=total
        area[i]=an;V[i]=surf;qret[i]=qr;sin[i]=surface_in;qout[i]=qo
    return {'dates':dt,'area':area,'V':V,'return_flow':qret,'surface_inflow':sin,'surface_outflow':qout,'mass_error':maxerr}

def colon_state(area,r):
    exp=np.clip((A0-area)/A0,0,1)
    e28=pd.Series(exp).rolling(EST_LAG,min_periods=EST_LAG).mean().fillna(0).to_numpy()
    x=0.; state=np.empty(len(area))
    # dx/dt = r * exposure * (1-x), with r in yr^-1.
    for i,e in enumerate(e28):
        x=min(1.,max(0.,x+(r/365.)*e*(1-x)));state[i]=x
    return state,exp,e28

def annual_mj(dt,x):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy();return np.array([float(np.mean(x[(yr==y)&np.isin(mo,[5,6])])) for y in YEARS])

def annual_feature(dt,x,w):
    roll=pd.Series(x,index=dt).rolling(w,min_periods=1).sum().to_numpy();yr=dt.year.to_numpy();mo=dt.month.to_numpy()
    ref=float(np.mean(roll[(yr==2011)&np.isin(mo,[5,6])]))
    return np.array([float(np.mean(roll[(yr==y)&np.isin(mo,[5,6])])-ref) for y in YEARS])

def fit_signed(S,H,y=Y):
    # y=A0-Kc*S+Kh*H; 0<=Kc<=A0 and Kh>=0.
    X=np.c_[-S,H];target=y-A0;cand=[]
    b=np.linalg.lstsq(X,target,rcond=None)[0]
    if b[0]>=0 and b[0]<=A0 and b[1]>=0:cand.append(b)
    d=np.dot(S,S);kc=max(0.,np.dot(-S,target)/d) if d>0 else 0.;kc=min(A0,kc);cand.append(np.array([kc,0.]))
    d=np.dot(H,H);kh=max(0.,np.dot(H,target)/d) if d>0 else 0.;cand.append(np.array([0.,kh]));cand.append(np.array([0.,0.]))
    bb=min(cand,key=lambda z:float(np.sum((A0+X@z-y)**2)));pred=A0+X@bb
    return bb,pred

def scores(pred):
    rm=float(np.sqrt(np.mean((pred-Y)**2)));return rm,100*rm/Y.mean(),float(np.mean(np.abs(pred-Y)))

def loocv(S,H):
    p=[]
    for i in range(6):
        k=np.arange(6)!=i;b,_=fit_signed(S[k],H[k],Y[k]);p.append(float(A0+np.array([-S[i],H[i]])@b))
    p=np.array(p);rm=float(np.sqrt(np.mean((p-Y)**2)));return rm,100*rm/Y.mean(),p

def main():
    F,missing,annual=forcing();rows=[]; hydro_cache=[]
    for V0,ps,ts,lf,tf in itertools.product(V0S,PS,TAU_SURF,LOCAL,TAU_FAST):
        hp={'V0':V0,'p_shape':ps,'tau_surf':ts,'local_frac':lf,'tau_fast':tf};h=hydro(F,hp)
        for r in R_E:
            state,exp,e28=colon_state(h['area'],r);S=annual_mj(h['dates'],state)
            corr=float(np.corrcoef(S,YEARS)[0,1]) if np.std(S)>0 else 1.
            for feature,w in itertools.product(FEATURES,WINDOWS):
                H=annual_feature(h['dates'],h[feature],w);b,pred=fit_signed(S,H);rm,nrm,mae=scores(pred);cv_rm,cv_nrm,cvp=loocv(S,H)
                rows.append({'nrmse':nrm,'rmse':rm,'mae':mae,'loocv_nrmse':cv_nrm,'loocv_rmse':cv_rm,
                             **hp,'r_exposure_yr':r,'hydro_feature':feature,'hydro_window_d':w,
                             'K_colonizable_m2':b[0],'K_hydro':b[1],'state_year_corr':corr,'max_mass_error_m3':h['mass_error'],
                             **{f'pred_{y}':pred[j] for j,y in enumerate(YEARS)},**{f'cv_{y}':cvp[j] for j,y in enumerate(YEARS)},
                             **{f'state_{y}':S[j] for j,y in enumerate(YEARS)},**{f'hydro_anom_{y}':H[j] for j,y in enumerate(YEARS)}})
    feasible=[z for z in rows if z['nrmse']<=2.0 and z['max_mass_error_m3']<1e-8 and z['state_year_corr']<.995]
    chosen=sorted(feasible,key=lambda z:(z['loocv_nrmse'],z['nrmse']))[0] if feasible else sorted(rows,key=lambda z:(z['nrmse'],z['loocv_nrmse']))[0]
    pd.DataFrame(sorted(rows,key=lambda z:(z['nrmse'],z['loocv_nrmse']))[:1000]).to_csv(OUT/'accuracy_top1000.csv',index=False)
    pd.DataFrame(sorted(feasible,key=lambda z:(z['loocv_nrmse'],z['nrmse']))[:1000]).to_csv(OUT/'feasible_cv_top1000.csv',index=False)
    # daily series for chosen hydrology/ecology
    hp={k:chosen[k] for k in ['V0','p_shape','tau_surf','local_frac','tau_fast']};h=hydro(F,hp);state,exp,e28=colon_state(h['area'],chosen['r_exposure_yr'])
    pd.DataFrame({'date':h['dates'],'surface_storage_m3':h['V'],'hydrologic_area_m2':h['area'],'return_flow_m3':h['return_flow'],
                  'surface_inflow_m3':h['surface_inflow'],'surface_outflow_m3':h['surface_outflow'],'exposure_fraction':exp,'exposure28':e28,'colonisation_state':state}).to_csv(OUT/'stage35c_best_daily.csv',index=False)
    summary={'model':'Stage35C exact-water-balance-derived hydro-ecology','selection':'nRMSE<=2%, exact closure, state-year corr<0.995; then minimize LOOCV',
             'n_candidates':len(rows),'n_feasible_2pct':len(feasible),'best':chosen,
             'equation':'A_open=A2011-Kc*C_exposure+Kh*H_waterbalance',
             'rules':{'daily_mass_balance':'exact','CN':False,'TOPMODEL':False,'lambda':0,'hard_cap':False,'freeboard':False,'explicit_time':False,'future_leakage':False,'2022_fit':False,
                      'ecology':'bounded first-order colonisation state, 28-d antecedent exposure','hydro_signal':'antecedent return-flow or total surface-inflow anomaly from water balance'},
             'benchmarks':{'Stage34_nrmse':.9568720534166563,'Stage34_loocv':1.2766706907049148,'Stage35B_nrmse':9.404598458304172}}
    (OUT/'stage35c_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
