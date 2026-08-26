#!/usr/bin/env python3
"""Stage 35B: exact daily water balance + Hayashi/van der Kamp storage-area transform.

The ONLY structural change from failed Stage35A is the surface-storage-to-area
operator. Stage35A effectively assumed A proportional to V (gamma=1), which
made area hypersensitive. Hayashi & van der Kamp (2000) give
A proportional to h^(2/p), V proportional to h^(1+2/p), hence after eliminating h:
    A/A0 = (V/V0)^(2/(p+2)).
This lets us use a literature-based monotone storage-area relation without
requiring explicit bathymetry or an underwater DEM.
"""
import itertools, json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing, OBS

OUT=Path('stage35b_outputs'); OUT.mkdir(exist_ok=True)
YEARS=np.array(sorted(OBS),int); Y=np.array([OBS[int(y)] for y in YEARS],float)
A0=2241.762; A_EXT=8483.0; A_WET=5939.5
SOIL_DEPTH_M=.294*.55; C_EXT=SOIL_DEPTH_M*A_EXT; C_WET=SOIL_DEPTH_M*A_WET
ET_EXT_FACTOR=.95; EST_WINDOW=28; FAST_FRAC=.75; TAU_SLOW=365.

# V0 is the initial conserved surface storage corresponding to observed A0.
# It is not a storage cap; V may exceed it freely.
V0_GRID=[100.,200.,400.,800.,1200.,1600.]
P_SHAPE=[.5,1.,2.,4.,8.,20.]  # Hayashi depression profile p > 0
TAU_SURF=[15.,30.,60.,120.]
LOCAL_FRAC=[.10,.20,.30]
TAU_FAST=[7.,30.,60.]
R_EST=[.00025,.0005,.001,.002,.004,.008]


def score(pred):
    p=np.array([pred[int(y)] for y in YEARS]); rm=float(np.sqrt(np.mean((p-Y)**2)))
    return rm,100*rm/Y.mean(),float(np.mean(np.abs(p-Y)))

def area_from_v(v,V0,p_shape):
    if v<=0: return 0.
    gamma=2./(p_shape+2.)
    return min(A_WET,A0*(v/V0)**gamma)

def hydro(F,p):
    pre=np.asarray(F['pre'],float); eto=np.asarray(F['eto'],float); ep=np.asarray(F['ep'],float); dates=pd.to_datetime(F['date'])
    n=len(pre); se=.5*C_EXT; sw=.5*C_WET; fast=slow=0.; surf=p['V0']; prev=se+sw+fast+slow+surf
    area=np.empty(n); V=np.empty(n); qret_a=np.empty(n); qdeep_a=np.empty(n); qsurf_a=np.empty(n); maxerr=0.
    for i in range(n):
        ap=area_from_v(surf,p['V0'],p['p_shape'])
        pext=pre[i]*A_EXT/1000.; popen=pre[i]*ap/1000.; pwsoil=pre[i]*(A_WET-ap)/1000.
        se+=pext; etext=min(se,ET_EXT_FACTOR*eto[i]*A_EXT/1000.); se-=etext; de=max(se-C_EXT,0.); se-=de
        sw+=pwsoil; etwet=min(sw,eto[i]*(A_WET-ap)/1000.); sw-=etwet; dw=max(sw-C_WET,0.); sw-=dw
        local=de*p['local_frac']; deep=de-local; fast+=local*FAST_FRAC; slow+=local*(1-FAST_FRAC)
        qf=min(fast,fast/p['tau_fast']); qs=min(slow,slow/TAU_SLOW); fast-=qf; slow-=qs; qret=qf+qs
        surf+=popen+dw+qret; eopen=min(surf,ep[i]*ap/1000.); surf-=eopen; qsurf=min(surf,surf/p['tau_surf']); surf-=qsurf
        an=area_from_v(surf,p['V0'],p['p_shape'])
        total=se+sw+fast+slow+surf; inputs=pext+popen+pwsoil; outputs=etext+etwet+eopen+deep+qsurf
        err=prev+inputs-outputs-total; maxerr=max(maxerr,abs(err)); prev=total
        area[i]=an; V[i]=surf; qret_a[i]=qret; qdeep_a[i]=deep; qsurf_a[i]=qsurf
    return {'dates':dates,'area':area,'V':V,'qret':qret_a,'qdeep':qdeep_a,'qsurf':qsurf_a,'max_mass_error':maxerr}

def ecology(h,r):
    a=h['area']; exp=np.clip((A0-a)/A0,0,1); e28=pd.Series(exp).rolling(EST_WINDOW,min_periods=EST_WINDOW).mean().fillna(0).to_numpy()
    C=0.; cc=np.empty(len(a)); opena=np.empty(len(a))
    for i in range(len(a)):
        exposed=max(0.,A0-min(A0,a[i])); eligible=max(0.,exposed-C); C=min(A0,C+r*eligible*e28[i]); cc[i]=C; opena[i]=max(0.,a[i]-C)
    return opena,cc,exp,e28

def mj(dates,a):
    yr=dates.year.to_numpy(); mo=dates.month.to_numpy(); return {int(y):float(np.mean(a[(yr==y)&np.isin(mo,[5,6])])) for y in YEARS}

def main():
    F,missing,annual=forcing(); rows=[]
    for V0,ps,tau,lf,tf in itertools.product(V0_GRID,P_SHAPE,TAU_SURF,LOCAL_FRAC,TAU_FAST):
        hp={'V0':V0,'p_shape':ps,'tau_surf':tau,'local_frac':lf,'tau_fast':tf}
        h=hydro(F,hp); hyd=mj(h['dates'],h['area']); hrm,hnrm,hmae=score(hyd)
        for re in R_EST:
            op,c,ex,e28=ecology(h,re); pred=mj(h['dates'],op); rm,nrm,mae=score(pred)
            rows.append({'nrmse':nrm,'rmse':rm,'mae':mae,'hydrology_only_nrmse':hnrm,**hp,'r_est_d':re,
                         'gamma_area_volume':2/(ps+2),'max_daily_mass_error_m3':h['max_mass_error'],'colonized_2023_m2':float(c[-1]),
                         **{f'pred_{y}':pred[int(y)] for y in YEARS},**{f'hydro_{y}':hyd[int(y)] for y in YEARS}})
    rows.sort(key=lambda z:(z['nrmse'],z['rmse'])); feasible=[z for z in rows if z['nrmse']<=2 and z['max_daily_mass_error_m3']<1e-8]
    chosen=feasible[0] if feasible else rows[0]
    hp={k:chosen[k] for k in ['V0','p_shape','tau_surf','local_frac','tau_fast']}; h=hydro(F,hp); op,c,ex,e28=ecology(h,chosen['r_est_d'])
    pd.DataFrame({'date':h['dates'],'hydrologic_area_m2':h['area'],'surface_storage_m3':h['V'],'open_water_m2':op,'colonized_m2':c,
                  'exposure_fraction':ex,'exposure_28d':e28,'return_flow_m3':h['qret'],'deep_loss_m3':h['qdeep'],'surface_drain_m3':h['qsurf']}).to_csv(OUT/'stage35b_best_daily.csv',index=False)
    pd.DataFrame(rows[:500]).to_csv(OUT/'stage35b_top500.csv',index=False); pd.DataFrame(feasible[:500]).to_csv(OUT/'stage35b_feasible_top500.csv',index=False)
    summary={'model':'Stage35B exact water balance + Hayashi storage-area + bounded colonisation','selection':'nRMSE<=2% gate; within gate minimize nRMSE',
             'n_candidates':len(rows),'n_feasible_2pct':len(feasible),'best':chosen,
             'rules':{'daily_mass_balance':'exact','lambda':0,'CN':False,'hard_cap':False,'freeboard':False,'explicit_time':False,'future_leakage':False,
                      'storage_area':'A/A0=(V/V0)^(2/(p+2)), Hayashi & van der Kamp 2000; A_wet only physical footprint ceiling','V0_role':'initial storage only, no cap'},
             'fixed':{'A0_m2':A0,'A_wet_m2':A_WET,'soil_storage_depth_m':SOIL_DEPTH_M,'fast_fraction':FAST_FRAC,'tau_slow_d':TAU_SLOW,'establishment_window_d':EST_WINDOW},
             'benchmarks':{'Stage34_nrmse':.9568720534166563,'Stage35A_failed_nrmse':62.489114980763084}}
    (OUT/'stage35b_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
