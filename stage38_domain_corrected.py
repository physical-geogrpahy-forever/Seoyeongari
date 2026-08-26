#!/usr/bin/env python3
"""Stage38 — correct the spatial water-balance domain before further tuning.

Stage35-37 applied precipitation/ET to A_EXT=8483 m2 and also to the entire
A_WET=5939.5 m2 footprint. Because A_EXT is the area outside the 2011 pond,
it already contains the potential wetland margin A_WET-A0. That formulation
therefore double-counted the margin while still closing algebraic mass balance.

Stage38 partitions the domain exactly once each day:
  A_upland = A_EXT_2011 - (A_WET - A0)
  A_domain = A_upland + A_wet_nonopen(t) + A_open(t)
where A_wet_nonopen=A_WET-A_open.

The hydrologic processes otherwise remain the Stage37 family: exact daily
storage accounting, causal return flow, continuous area-proportional Qgw,
hydroperiod-driven ecology, no cap/freeboard/lambda/time trend, and 2022 absent
from fitting/selection.
"""
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing,OBS
from stage35c_mass_balance_state_operator import A0,A_WET,SOIL_DEPTH,ET_EXT,FAST_FRAC,TAU_SLOW,area_v
from eghm_strict_rules import EVAL_YEARS,candidate_reasons

OUT=Path('stage38_outputs');OUT.mkdir(exist_ok=True)
YEARS=np.array(EVAL_YEARS,int);Y=np.array([OBS[int(y)] for y in YEARS],float)
assert tuple(sorted(OBS))==EVAL_YEARS

A_EXT_2011=8483.0
A_WET_MARGIN_2011=A_WET-A0
A_UPLAND=A_EXT_2011-A_WET_MARGIN_2011
A_DOMAIN=A_UPLAND+A_WET
A_RASTER_TOTAL_REFERENCE=10720.0
C_UPLAND=SOIL_DEPTH*A_UPLAND
C_WET=SOIL_DEPTH*A_WET
LAG=28

# Broad enough to re-establish the optimum after fixing the flux footprint.
GRIDS={
 'V0':[1000.,1600.,2200.],
 'p_shape':[6.,12.,18.],
 'tau_surf':[60.,120.,240.],
 'local_frac':[.15,.30,.45],
 'tau_fast':[30.,60.,120.],
 'k_gw_mm_d':[.25,1.,2.,4.],
 'r_est_yr':[.01,.025,.05],
 'hydro_window_d':[14,30,60],
}
CONTRACT={
 'lambda':0,'hard_cap':False,'freeboard':False,'explicit_time':False,
 'future_leakage':False,'2022_fit':False,'a2011_hard_max':False,
 'spring_dry_selection_requirement':False,'domain_double_count':False,
 'rainfall_partition_exact':True,
}

def hydro(F,p):
    pre=np.asarray(F['pre'],float);eto=np.asarray(F['eto'],float);ep=np.asarray(F['ep'],float);dt=pd.to_datetime(F['date']);n=len(pre)
    su=.5*C_UPLAND;sw=.5*C_WET;fast=slow=0.;surf=p['V0'];prev=su+sw+fast+slow+surf
    area=np.empty(n);V=np.empty(n);qret=np.empty(n);qgw=np.empty(n);qout=np.empty(n)
    maxerr=max_area_err=max_p_err=0.
    for i in range(n):
        ap=area_v(surf,p['V0'],p['p_shape']);aw=max(A_WET-ap,0.)
        # Exact, non-overlapping spatial partition of rainfall footprint.
        pup=pre[i]*A_UPLAND/1000.;pwet=pre[i]*aw/1000.;popen=pre[i]*ap/1000.
        area_err=abs((A_UPLAND+aw+ap)-A_DOMAIN);max_area_err=max(max_area_err,area_err)
        p_err=abs((pup+pwet+popen)-pre[i]*A_DOMAIN/1000.);max_p_err=max(max_p_err,p_err)

        su+=pup;e1=min(su,ET_EXT*eto[i]*A_UPLAND/1000.);su-=e1;dex=max(su-C_UPLAND,0.);su-=dex
        sw+=pwet;e2=min(sw,eto[i]*aw/1000.);sw-=e2;dw=max(sw-C_WET,0.);sw-=dw
        local=dex*p['local_frac'];deep=dex-local;fast+=local*FAST_FRAC;slow+=local*(1-FAST_FRAC)
        qf=min(fast,fast/p['tau_fast']);qs=min(slow,slow/TAU_SLOW);fast-=qf;slow-=qs;qr=qf+qs
        surf+=popen+dw+qr
        # Surface evaporation uses only the current open-water footprint.
        ap2=area_v(surf,p['V0'],p['p_shape']);eo=min(surf,ep[i]*ap2/1000.);surf-=eo
        qo=min(surf,surf/p['tau_surf']);surf-=qo
        ag=area_v(surf,p['V0'],p['p_shape']);qg=min(surf,p['k_gw_mm_d']*ag/1000.);surf-=qg
        an=area_v(surf,p['V0'],p['p_shape'])
        total=su+sw+fast+slow+surf;inputs=pup+pwet+popen;outputs=e1+e2+eo+deep+qo+qg
        err=prev+inputs-outputs-total;maxerr=max(maxerr,abs(err));prev=total
        area[i]=an;V[i]=surf;qret[i]=qr;qgw[i]=qg;qout[i]=qo
    return {'dates':dt,'area':area,'V':V,'return_flow':qret,'groundwater_loss':qgw,'surface_outflow':qout,
            'mass_error':maxerr,'area_partition_error':max_area_err,'precip_partition_error':max_p_err}

def state(area,r):
    exposed=(np.asarray(area)<A0).astype(float)
    e28=pd.Series(exposed).rolling(LAG,min_periods=LAG).mean().fillna(0).to_numpy();x=0.;st=np.empty(len(area))
    for i,e in enumerate(e28):
        x=np.clip(x+(r/365.)*e*(1-x),0,1);st[i]=x
    return st

def annual(dt,x):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy()
    return np.array([float(np.mean(x[(yr==y)&np.isin(mo,[5,6])])) for y in YEARS])

def feature(dt,q,w):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy();rr=pd.Series(q,index=dt).rolling(int(w),min_periods=1).sum().to_numpy()
    ref=float(np.mean(rr[(yr==2011)&np.isin(mo,[5,6])]))
    return np.array([float(np.mean(rr[(yr==y)&np.isin(mo,[5,6])])-ref) for y in YEARS])

def fit(S,H,y=Y):
    X=np.c_[-S,H];t=y-A0;c=[];b=np.linalg.lstsq(X,t,rcond=None)[0]
    if 0<=b[0]<=A0 and b[1]>=0:c.append(b)
    d=np.dot(S,S);kc=np.clip(np.dot(-S,t)/d if d else 0,0,A0);c.append(np.array([kc,0.]))
    d=np.dot(H,H);kh=max(0,np.dot(H,t)/d) if d else 0.;c.append(np.array([0.,kh]));c.append(np.array([0.,0.]))
    bb=min(c,key=lambda z:float(np.sum((A0+X@z-y)**2)));return bb,A0+X@bb

def metrics(pred):
    rm=float(np.sqrt(np.mean((pred-Y)**2)));return rm,100*rm/Y.mean(),float(np.mean(np.abs(pred-Y)))

def loocv(S,H):
    pp=[]
    for i in range(len(YEARS)):
        keep=np.arange(len(YEARS))!=i;b,_=fit(S[keep],H[keep],Y[keep]);pp.append(float(A0+np.array([-S[i],H[i]])@b))
    pp=np.array(pp);rm=float(np.sqrt(np.mean((pp-Y)**2)));return rm,100*rm/Y.mean(),pp

def zero_diag(dt,V):
    dt=pd.to_datetime(dt);yr=dt.year.to_numpy();mo=dt.month.to_numpy();z=np.asarray(V)<=1e-9
    total=int(z.sum());spring=int(np.sum(z&np.isin(mo,[3,4])))
    return {'zero_storage_days_total':total,'mar_apr_zero_storage_days_total':spring,
            'spring_share_of_zero_days':(spring/total if total else None),
            'by_year':{str(y):{'zero_storage_days':int(np.sum(z&(yr==y))),
                               'mar_apr_zero_storage_days':int(np.sum(z&(yr==y)&np.isin(mo,[3,4])))} for y in range(2011,2024)}}

def main():
    F,_,_=forcing();rows=[];hydros={}
    hk=['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']
    for vals in itertools.product(*[GRIDS[k] for k in hk]):
        hp=dict(zip(hk,vals));h=hydro(F,hp);hydros[tuple(vals)]=h;zd=zero_diag(h['dates'],h['V'])
        for re,w in itertools.product(GRIDS['r_est_yr'],GRIDS['hydro_window_d']):
            S=annual(h['dates'],state(h['area'],re));corr=float(np.corrcoef(S,YEARS)[0,1]) if np.std(S)>0 else 1.
            H=feature(h['dates'],h['return_flow'],w);b,pred=fit(S,H);rm,nrm,mae=metrics(pred);crm,cn,cvp=loocv(S,H)
            row={'A0_m2':A0,'nrmse':nrm,'rmse':rm,'mae':mae,'loocv_nrmse':cn,'loocv_rmse':crm,**hp,
                 'r_est_yr':re,'hydro_window_d':w,'K_colonizable_m2':float(b[0]),'K_hydro':float(b[1]),
                 'hydro_effect_range_m2':float(b[1]*(H.max()-H.min())),'state_year_corr':corr,
                 'max_mass_error_m3':float(h['mass_error']),'max_area_partition_error_m2':float(h['area_partition_error']),
                 'max_precip_partition_error_m3':float(h['precip_partition_error']),
                 'zero_storage_days_total':zd['zero_storage_days_total'],'mar_apr_zero_storage_days_total':zd['mar_apr_zero_storage_days_total'],
                 **{f'pred_{y}':float(pred[j]) for j,y in enumerate(YEARS)},**{f'cv_{y}':float(cvp[j]) for j,y in enumerate(YEARS)}}
            reasons=candidate_reasons(row,GRIDS,CONTRACT,require_new_process='k_gw_mm_d',require_short_hydro=True)
            row['strict_pass']=not reasons;row['reject_reasons']=';'.join(reasons);rows.append(row)
    passed=[r for r in rows if r['strict_pass']];key=lambda z:(z['loocv_nrmse'],z['nrmse'],z['rmse']);chosen=sorted(passed,key=key)[0] if passed else None
    diag=None
    if chosen:
        h=hydros[tuple(chosen[k] for k in hk)];diag=zero_diag(h['dates'],h['V'])
    # Also preserve best rule-rejected candidates so failure is diagnosable without relaxing gates.
    ranked=sorted(rows,key=lambda z:(len(z['reject_reasons'].split(';')) if z['reject_reasons'] else 0,z['loocv_nrmse'],z['nrmse']))
    out={'model':'Stage38 domain-corrected exact-water-balance hydro-ecology','n_candidates':len(rows),'n_strict_pass':len(passed),'selected':chosen,
         'selected_zero_storage_diagnostics':diag,
         'geometry':{'A0_m2':A0,'A_ext_outside_2011_m2':A_EXT_2011,'A_wet_footprint_m2':A_WET,'A_wet_margin_2011_m2':A_WET_MARGIN_2011,
                     'A_upland_nonoverlap_m2':A_UPLAND,'A_domain_component_sum_m2':A_DOMAIN,'raster_total_reference_m2':A_RASTER_TOTAL_REFERENCE,
                     'vector_raster_area_difference_m2':A_DOMAIN-A_RASTER_TOTAL_REFERENCE},
         'grids':GRIDS,'contract':CONTRACT,'holdout_2022_used':False,
         'best_rejected_preview':ranked[:5]}
    pd.DataFrame(rows).sort_values(['strict_pass','loocv_nrmse','nrmse'],ascending=[False,True,True]).head(3000).to_csv(OUT/'stage38_candidates.csv',index=False)
    (OUT/'stage38_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
    if not chosen:raise SystemExit('NO STRICT-PASS CANDIDATE: preserve rules; diagnose/expand structure')
if __name__=='__main__':main()
