#!/usr/bin/env python3
"""Stage37 — exact daily water balance with continuous area-proportional
surface-to-subsurface loss, plus Stage36 hydroperiod ecology.

The hydrologic balance is the Stage35C core plus one explicit outflow:
  Q_gw = min(S_surface, k_gw * A_water / 1000)
where k_gw is mm d-1. This is a water-balance flux, not an observation
correction. It is continuous, threshold-free, and becomes zero with no surface
water. Literature basis: WetMAT includes flooded-area/hydraulic-conductivity
vertical loss; Jeju Saraoreum monitoring identifies underground outflow as an
important drying pathway.

Open-water observation operator remains causal and uses only water-balance
states/fluxes:
  A_open = A2011 - Kc*C_hydroperiod + Kh*H_returnflow
No CN, TOPMODEL, lambda, hard cap, freeboard, explicit year, future leakage.
2022 is never used for fitting/selection.
"""
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing,OBS
from stage35c_mass_balance_state_operator import A0,A_EXT,A_WET,SOIL_DEPTH,C_EXT,C_WET,ET_EXT,FAST_FRAC,TAU_SLOW,area_v

OUT=Path('stage37_outputs');OUT.mkdir(exist_ok=True)
YEARS=np.array(sorted(OBS),int);Y=np.array([OBS[int(y)] for y in YEARS],float)
V0S=[1200.,1600.,2400.];PS=[8.,12.,20.];TAU_SURF=[60.,120.,240.];LOCAL=[.1,.2,.3];TAU_FAST=[30.,60.]
# Broad conceptual range; k_gw is calibrated, not claimed as measured Seoyeongari K.
KGW=[0.,.1,.25,.5,1.,2.,4.,8.]
R_EST=[.025,.05,.1,.2];WINDOWS=[14,30];LAG=28

def hydro(F,p):
    pre=np.asarray(F['pre'],float);eto=np.asarray(F['eto'],float);ep=np.asarray(F['ep'],float);dt=pd.to_datetime(F['date']);n=len(pre)
    se=.5*C_EXT;sw=.5*C_WET;fast=slow=0.;surf=p['V0'];prev=se+sw+fast+slow+surf
    area=np.empty(n);V=np.empty(n);qret=np.empty(n);sin=np.empty(n);qout=np.empty(n);qgw=np.empty(n);maxerr=0.
    for i in range(n):
        ap=area_v(surf,p['V0'],p['p_shape'])
        pext=pre[i]*A_EXT/1000.;popen=pre[i]*ap/1000.;pwet=pre[i]*(A_WET-ap)/1000.
        se+=pext;e1=min(se,ET_EXT*eto[i]*A_EXT/1000.);se-=e1;dex=max(se-C_EXT,0.);se-=dex
        sw+=pwet;e2=min(sw,eto[i]*(A_WET-ap)/1000.);sw-=e2;dw=max(sw-C_WET,0.);sw-=dw
        local=dex*p['local_frac'];deep=dex-local;fast+=local*FAST_FRAC;slow+=local*(1-FAST_FRAC)
        qf=min(fast,fast/p['tau_fast']);qs=min(slow,slow/TAU_SLOW);fast-=qf;slow-=qs;qr=qf+qs
        surface_in=popen+dw+qr;surf+=surface_in
        eo=min(surf,ep[i]*ap/1000.);surf-=eo
        qo=min(surf,surf/p['tau_surf']);surf-=qo
        # Continuous subsurface loss from current inundated surface.
        ag=area_v(surf,p['V0'],p['p_shape'])
        qg=min(surf,p['k_gw_mm_d']*ag/1000.);surf-=qg
        an=area_v(surf,p['V0'],p['p_shape'])
        total=se+sw+fast+slow+surf;inputs=pext+popen+pwet;outputs=e1+e2+eo+deep+qo+qg
        err=prev+inputs-outputs-total;maxerr=max(maxerr,abs(err));prev=total
        area[i]=an;V[i]=surf;qret[i]=qr;sin[i]=surface_in;qout[i]=qo;qgw[i]=qg
    return {'dates':dt,'area':area,'V':V,'return_flow':qret,'surface_inflow':sin,'surface_outflow':qout,'groundwater_loss':qgw,'mass_error':maxerr}

def state(area,r):
    exposed=(np.asarray(area)<A0).astype(float)
    e28=pd.Series(exposed).rolling(LAG,min_periods=LAG).mean().fillna(0).to_numpy();x=0.;st=np.empty(len(area))
    for i,e in enumerate(e28):
        x=np.clip(x+(r/365.)*e*(1-x),0,1);st[i]=x
    return st,exposed,e28

def ann(dt,x):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy();return np.array([float(np.mean(x[(yr==y)&np.isin(mo,[5,6])])) for y in YEARS])
def feature(dt,q,w):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy();rr=pd.Series(q,index=dt).rolling(w,min_periods=1).sum().to_numpy();ref=float(np.mean(rr[(yr==2011)&np.isin(mo,[5,6])]))
    return np.array([float(np.mean(rr[(yr==y)&np.isin(mo,[5,6])])-ref) for y in YEARS])
def fit(S,H,y=Y):
    X=np.c_[-S,H];t=y-A0;c=[];b=np.linalg.lstsq(X,t,rcond=None)[0]
    if 0<=b[0]<=A0 and b[1]>=0:c.append(b)
    d=np.dot(S,S);kc=np.clip(np.dot(-S,t)/d if d else 0,0,A0);c.append(np.array([kc,0.]))
    d=np.dot(H,H);kh=max(0,np.dot(H,t)/d) if d else 0.;c.append(np.array([0.,kh]));c.append(np.array([0.,0.]))
    bb=min(c,key=lambda z:float(np.sum((A0+X@z-y)**2)));return bb,A0+X@bb
def score(p):
    rm=float(np.sqrt(np.mean((p-Y)**2)));return rm,100*rm/Y.mean(),float(np.mean(np.abs(p-Y)))
def cv(S,H):
    pp=[]
    for i in range(6):
        k=np.arange(6)!=i;b,_=fit(S[k],H[k],Y[k]);pp.append(float(A0+np.array([-S[i],H[i]])@b))
    pp=np.array(pp);rm=float(np.sqrt(np.mean((pp-Y)**2)));return rm,100*rm/Y.mean(),pp

def spring_diag(dt,a):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy();spr=np.isin(mo,[3,4]);
    return int(np.sum(a[spr]<1.0)),float(np.mean(a[spr]<A0))

def main():
    F,_,_=forcing();rows=[]
    for V0,ps,ts,lf,tf,kg in itertools.product(V0S,PS,TAU_SURF,LOCAL,TAU_FAST,KGW):
        hp={'V0':V0,'p_shape':ps,'tau_surf':ts,'local_frac':lf,'tau_fast':tf,'k_gw_mm_d':kg};h=hydro(F,hp);dry,exfrac=spring_diag(h['dates'],h['area'])
        for re,w in itertools.product(R_EST,WINDOWS):
            st,ex,e28=state(h['area'],re);S=ann(h['dates'],st);corr=float(np.corrcoef(S,YEARS)[0,1]) if np.std(S)>0 else 1.;H=feature(h['dates'],h['return_flow'],w)
            b,pred=fit(S,H);rm,nrm,mae=score(pred);crm,cn,cp=cv(S,H);hr=float(b[1]*(H.max()-H.min()))
            rows.append({'nrmse':nrm,'rmse':rm,'mae':mae,'loocv_nrmse':cn,'loocv_rmse':crm,**hp,'r_est_yr':re,'hydro_window_d':w,'K_colonizable_m2':b[0],'K_hydro':b[1],
                         'hydro_effect_range_m2':hr,'state_year_corr':corr,'max_mass_error_m3':h['mass_error'],'spring_complete_dry_days_total':dry,'spring_exposed_fraction_all_years':exfrac,
                         **{f'pred_{y}':pred[j] for j,y in enumerate(YEARS)},**{f'cv_{y}':cp[j] for j,y in enumerate(YEARS)},**{f'state_{y}':S[j] for j,y in enumerate(YEARS)},**{f'hydro_anom_{y}':H[j] for j,y in enumerate(YEARS)}})
    feasible=[z for z in rows if z['nrmse']<=2 and z['max_mass_error_m3']<1e-8]
    balanced=[z for z in feasible if z['K_hydro']>0 and z['state_year_corr']<.99]
    balanced_dry=[z for z in balanced if z['spring_complete_dry_days_total']>0]
    key=lambda z:(z['loocv_nrmse'],z['nrmse'])
    out={'model':'Stage37 exact balance + continuous subsurface loss + hydroperiod ecology','n_candidates':len(rows),'n_feasible':len(feasible),'n_balanced':len(balanced),'n_balanced_with_spring_dry':len(balanced_dry),
         'best_feasible':sorted(feasible,key=key)[0] if feasible else None,'best_balanced':sorted(balanced,key=key)[0] if balanced else None,'best_balanced_with_spring_dry':sorted(balanced_dry,key=key)[0] if balanced_dry else None,
         'equations':{'surface_balance':'dS=Popen+Qwet+Qreturn-Eopen-Qout-Qgw','groundwater_loss':'Qgw=min(S,k_gw*Awater/1000)'},
         'rules':{'exact_daily_water_balance':True,'CN':False,'TOPMODEL':False,'lambda':0,'hard_cap':False,'freeboard':False,'explicit_time':False,'future_leakage':False,'2022_fit':False,'spring_dry_not_selection_requirement':True}}
    pd.DataFrame(sorted(rows,key=lambda z:(z['nrmse'],z['loocv_nrmse']))[:1500]).to_csv(OUT/'top1500.csv',index=False)
    pd.DataFrame(sorted(balanced,key=key)[:1500]).to_csv(OUT/'balanced.csv',index=False)
    (OUT/'stage37_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
