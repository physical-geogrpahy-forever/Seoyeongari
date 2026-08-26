#!/usr/bin/env python3
"""Stage37R — strict refinement of Stage37 around the balanced solution.

No new model process is introduced here. The Stage37 water-balance equations are
kept unchanged. This run only expands/refines parameter domains that touched a
previous grid edge and applies hard acceptance gates before ranking candidates.
2022 is not imported, read, scored, or used in this script.
"""
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing,OBS
from stage35c_mass_balance_state_operator import A0
from stage37_groundwater_loss import hydro,state,fit
from eghm_strict_rules import EVAL_YEARS,candidate_reasons

OUT=Path('stage37r_outputs');OUT.mkdir(exist_ok=True)
YEARS=np.array(EVAL_YEARS,int)
Y=np.array([OBS[int(y)] for y in YEARS],float)
assert tuple(sorted(OBS))==EVAL_YEARS, 'OBS used for fitting must contain only the six evaluation years'

# Focused refinement around Stage37 best_balanced. Previous edge hits are moved
# into the interior of these ranges rather than accepted as calibrated values.
GRIDS={
 'V0':[1200.,1600.,2000.],
 'p_shape':[8.,12.,16.],
 'tau_surf':[90.,120.,180.],
 'local_frac':[.2,.3,.4],
 'tau_fast':[45.,60.,90.],
 'k_gw_mm_d':[.5,1.,1.5,2.],
 'r_est_yr':[.01,.025,.05],
 'hydro_window_d':[21,30,45],
}
CONTRACT={
 'lambda':0,'hard_cap':False,'freeboard':False,'explicit_time':False,
 'future_leakage':False,'2022_fit':False,'a2011_hard_max':False,
 'spring_dry_selection_requirement':False,
}

def annual(dt,x):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy()
    return np.array([float(np.mean(x[(yr==y)&np.isin(mo,[5,6])])) for y in YEARS])

def hydro_feature(dt,q,w):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy()
    rr=pd.Series(q,index=dt).rolling(int(w),min_periods=1).sum().to_numpy()
    ref=float(np.mean(rr[(yr==2011)&np.isin(mo,[5,6])]))
    return np.array([float(np.mean(rr[(yr==y)&np.isin(mo,[5,6])])-ref) for y in YEARS])

def fit_local(S,H,y=Y):
    X=np.c_[-S,H];t=y-A0;c=[];b=np.linalg.lstsq(X,t,rcond=None)[0]
    if 0<=b[0]<=A0 and b[1]>=0:c.append(b)
    d=np.dot(S,S);kc=np.clip(np.dot(-S,t)/d if d else 0,0,A0);c.append(np.array([kc,0.]))
    d=np.dot(H,H);kh=max(0,np.dot(H,t)/d) if d else 0.;c.append(np.array([0.,kh]));c.append(np.array([0.,0.]))
    bb=min(c,key=lambda z:float(np.sum((A0+X@z-y)**2)))
    return bb,A0+X@bb

def metrics(pred):
    rm=float(np.sqrt(np.mean((pred-Y)**2)))
    return rm,100*rm/Y.mean(),float(np.mean(np.abs(pred-Y)))

def loocv(S,H):
    pp=[]
    for i in range(len(YEARS)):
        keep=np.arange(len(YEARS))!=i
        b,_=fit_local(S[keep],H[keep],Y[keep])
        pp.append(float(A0+np.array([-S[i],H[i]])@b))
    pp=np.array(pp);rm=float(np.sqrt(np.mean((pp-Y)**2)))
    return rm,100*rm/Y.mean(),pp

def zero_storage_diagnostics(dt,V):
    dates=pd.to_datetime(dt);yr=dates.year.to_numpy();mo=dates.month.to_numpy()
    zero=np.asarray(V)<=1e-9  # numerical zero only; not a calibrated hydrologic threshold
    total=int(zero.sum());spring=int(np.sum(zero & np.isin(mo,[3,4])))
    per={}
    for y in range(2011,2024):
        m=yr==y;sp=m & np.isin(mo,[3,4]);z=np.where(zero&m)[0]
        first=str(dates[z[0]].date()) if len(z) else None
        # first positive-storage day after the first zero day, diagnostic only
        rewet=None
        if len(z):
            later=np.where((np.arange(len(V))>z[0]) & m & (~zero))[0]
            if len(later):rewet=str(dates[later[0]].date())
        per[str(y)]={'zero_storage_days':int(np.sum(zero&m)),
                     'mar_apr_zero_storage_days':int(np.sum(zero&sp)),
                     'first_zero_storage_date':first,'first_rewet_date':rewet}
    return {'zero_storage_days_total':total,'mar_apr_zero_storage_days_total':spring,
            'spring_share_of_zero_days':(spring/total if total else None),'by_year':per}

def main():
    F,_,_=forcing();rows=[];hydro_cache={}
    hydro_keys=['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']
    for vals in itertools.product(*[GRIDS[k] for k in hydro_keys]):
        hp=dict(zip(hydro_keys,vals));h=hydro(F,hp);hydro_cache[tuple(vals)]=h
        zd=zero_storage_diagnostics(h['dates'],h['V'])
        for re,w in itertools.product(GRIDS['r_est_yr'],GRIDS['hydro_window_d']):
            st,_,_=state(h['area'],re);S=annual(h['dates'],st)
            corr=float(np.corrcoef(S,YEARS)[0,1]) if np.std(S)>0 else 1.0
            H=hydro_feature(h['dates'],h['return_flow'],w)
            b,pred=fit_local(S,H);rm,nrm,mae=metrics(pred);crm,cn,cvp=loocv(S,H)
            row={'A0_m2':A0,'nrmse':nrm,'rmse':rm,'mae':mae,'loocv_nrmse':cn,'loocv_rmse':crm,
                 **hp,'r_est_yr':re,'hydro_window_d':w,'K_colonizable_m2':float(b[0]),'K_hydro':float(b[1]),
                 'hydro_effect_range_m2':float(b[1]*(H.max()-H.min())),'state_year_corr':corr,
                 'max_mass_error_m3':float(h['mass_error']),
                 'zero_storage_days_total':zd['zero_storage_days_total'],
                 'mar_apr_zero_storage_days_total':zd['mar_apr_zero_storage_days_total'],
                 **{f'pred_{y}':float(pred[j]) for j,y in enumerate(YEARS)},
                 **{f'cv_{y}':float(cvp[j]) for j,y in enumerate(YEARS)}}
            reasons=candidate_reasons(row,GRIDS,CONTRACT,require_new_process='k_gw_mm_d',require_short_hydro=True)
            row['strict_pass']=not reasons;row['reject_reasons']=';'.join(reasons)
            rows.append(row)
    passed=[r for r in rows if r['strict_pass']]
    key=lambda z:(z['loocv_nrmse'],z['nrmse'],z['rmse'])
    chosen=sorted(passed,key=key)[0] if passed else None
    diag=None
    if chosen:
        hk=tuple(chosen[k] for k in hydro_keys);diag=zero_storage_diagnostics(hydro_cache[hk]['dates'],hydro_cache[hk]['V'])
    out={'model':'Stage37R strict refined exact-water-balance hydro-ecology',
         'selection':'hard rules first; among strict-pass candidates minimize LOOCV then nRMSE',
         'n_candidates':len(rows),'n_strict_pass':len(passed),'selected':chosen,
         'selected_zero_storage_diagnostics':diag,'grids':GRIDS,'contract':CONTRACT,
         'holdout_2022_used':False}
    pd.DataFrame(rows).sort_values(['strict_pass','loocv_nrmse','nrmse'],ascending=[False,True,True]).head(2500).to_csv(OUT/'stage37r_candidates.csv',index=False)
    (OUT/'stage37r_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    if not chosen:
        raise SystemExit('NO STRICT-PASS CANDIDATE: expand/refine structure; do not relax rules')
if __name__=='__main__':main()
