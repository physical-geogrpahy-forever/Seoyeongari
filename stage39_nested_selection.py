#!/usr/bin/env python3
"""Stage39 — nested model-selection validation for the domain-corrected EGHM.

Purpose
-------
Previous 'LOOCV' scores kept structural/ecological hyperparameters selected with
all six evaluation years and refit only Kc/Kh. That is conditional CV, not a
validation of the full selection procedure. Stage39 uses outer leave-one-year-
out validation. For each outer fold, the held-out year's observed pond area is
never used to rank structural candidates, choose the hydroperiod window, or fit
Kc/Kh. Candidate ranking inside the five-year training set uses an inner LOOCV.

The hydrologic engine is the Stage38 domain-corrected, order-neutral, exact daily
water balance. 2022 is absent from all training/selection and remains a later
separate holdout.
"""
from __future__ import annotations
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing,OBS
from stage35c_mass_balance_state_operator import A0
from stage38_domain_corrected import hydro,GRIDS
from eghm_strict_rules import (EVAL_YEARS,MASS_TOL_M3,AREA_PARTITION_TOL_M2,
    PRECIP_PARTITION_TOL_M3,NRMSE_MAX_PCT,LOOCV_NRMSE_MAX_PCT,
    NESTED_LOOCV_NRMSE_MAX_PCT,STATE_YEAR_CORR_MAX,ZERO_TOL,grid_boundary_reasons)

OUT=Path('stage39_outputs');OUT.mkdir(exist_ok=True)
YEARS=np.array(EVAL_YEARS,int)
Y=np.array([OBS[int(y)] for y in YEARS],float)
assert tuple(sorted(OBS))==EVAL_YEARS

CONTRACT={
 'lambda':0,'hard_cap':False,'freeboard':False,'explicit_time':False,
 'future_leakage':False,'2022_fit':False,'a2011_hard_max':False,
 'spring_dry_selection_requirement':False,'domain_double_count':False,
 'rainfall_partition_exact':True,'surface_loss_priority':False,
 'nested_cv_selection':True,'hyperparameter_holdout_leakage':False,
}

HKEYS=['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']
ALLKEYS=HKEYS+['r_est_yr','hydro_window_d']

def rolling_exposure_state(area,r):
    exposed=(np.asarray(area)<A0).astype(float)
    e28=pd.Series(exposed).rolling(28,min_periods=28).mean().fillna(0).to_numpy()
    # Exact vector form of x_t=x_{t-1}+a*e_t*(1-x_{t-1}), x0=0.
    return 1.0-np.cumprod(1.0-(float(r)/365.0)*e28)

def annual(dt,x,years=YEARS):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy()
    return np.array([float(np.mean(x[(yr==y)&np.isin(mo,[5,6])])) for y in years])

def annual_hydro(dt,q,w,years=YEARS):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy()
    rr=pd.Series(q,index=dt).rolling(int(w),min_periods=1).sum().to_numpy()
    ref=float(np.mean(rr[(yr==2011)&np.isin(mo,[5,6])]))
    return np.array([float(np.mean(rr[(yr==y)&np.isin(mo,[5,6])])-ref) for y in years])

def fit_constrained(S,H,y):
    S=np.asarray(S,float);H=np.asarray(H,float);y=np.asarray(y,float)
    X=np.c_[-S,H];t=y-A0;c=[]
    b=np.linalg.lstsq(X,t,rcond=None)[0]
    if 0<=b[0]<=A0 and b[1]>=0:c.append(b)
    d=np.dot(S,S);kc=np.clip(np.dot(-S,t)/d if d else 0,0,A0);c.append(np.array([kc,0.]))
    d=np.dot(H,H);kh=max(0,np.dot(H,t)/d) if d else 0.;c.append(np.array([0.,kh]))
    c.append(np.array([0.,0.]))
    bb=min(c,key=lambda z:float(np.sum((A0+X@z-y)**2)))
    return bb,A0+X@bb

def nrmse(pred,y):
    pred=np.asarray(pred,float);y=np.asarray(y,float)
    rm=float(np.sqrt(np.mean((pred-y)**2)))
    return rm,100.0*rm/float(np.mean(y))

def coeff_ok(b):
    return (float(b[0])>ZERO_TOL and float(b[0])<A0-ZERO_TOL and float(b[1])>ZERO_TOL)

def structural_ok(c):
    if grid_boundary_reasons(c,GRIDS): return False
    if float(c['k_gw_mm_d'])<=ZERO_TOL:return False
    if float(c['max_mass_error_m3'])>MASS_TOL_M3:return False
    if float(c['max_area_partition_error_m2'])>AREA_PARTITION_TOL_M2:return False
    if float(c['max_precip_partition_error_m3'])>PRECIP_PARTITION_TOL_M3:return False
    return True

def fixed_candidate_cv(c,idx):
    """CV of one fixed structural candidate within idx; no structure reselection."""
    idx=np.asarray(idx,int);p=[]
    for j in range(len(idx)):
        tr=np.delete(idx,j);te=idx[j]
        b,_=fit_constrained(c['S'][tr],c['H'][tr],Y[tr])
        p.append(float(A0+np.array([-c['S'][te],c['H'][te]])@b))
    return nrmse(np.array(p),Y[idx])

def candidate_pass_on_training(c,idx,inner_limit=True):
    idx=np.asarray(idx,int)
    if not structural_ok(c):return False,None
    corr=float(np.corrcoef(c['S'][idx],YEARS[idx])[0,1]) if np.std(c['S'][idx])>0 else 1.0
    if abs(corr)>=STATE_YEAR_CORR_MAX:return False,None
    b,p=fit_constrained(c['S'][idx],c['H'][idx],Y[idx])
    if not coeff_ok(b):return False,None
    rm,nr=nrmse(p,Y[idx])
    if nr>NRMSE_MAX_PCT:return False,None
    irm,inr=fixed_candidate_cv(c,idx)
    if inner_limit and inr>LOOCV_NRMSE_MAX_PCT:return False,None
    return True,{'b':b,'train_rmse':rm,'train_nrmse':nr,'inner_cv_rmse':irm,'inner_cv_nrmse':inr,'state_year_corr':corr}

def build_candidates(F):
    candidates=[]
    # Boundary candidates can never be accepted under the strict contract, so
    # they are not simulated here. This is a computational filter, not tuning.
    internal={k:[v for v in vals if v!=min(vals) and v!=max(vals)] for k,vals in GRIDS.items()}
    hgrids=[internal[k] for k in HKEYS]
    for vals in itertools.product(*hgrids):
        hp=dict(zip(HKEYS,vals));h=hydro(F,hp)
        s_cache={r:annual(h['dates'],rolling_exposure_state(h['area'],r)) for r in internal['r_est_yr']}
        h_cache={w:annual_hydro(h['dates'],h['return_flow'],w) for w in internal['hydro_window_d']}
        for r,w in itertools.product(internal['r_est_yr'],internal['hydro_window_d']):
            candidates.append({**hp,'r_est_yr':r,'hydro_window_d':w,'S':s_cache[r],'H':h_cache[w],
                'max_mass_error_m3':float(h['mass_error']),
                'max_area_partition_error_m2':float(h['area_partition_error']),
                'max_precip_partition_error_m3':float(h['precip_partition_error'])})
    return candidates,internal

def main():
    F,_,_=forcing();cands,internal=build_candidates(F)
    if not cands:raise SystemExit('No interior-grid candidates; expand grid before evaluation')

    # Final model selection on all six years, using conditional candidate CV as
    # an internal selection score. This is NOT the reported nested validation.
    all_idx=np.arange(len(YEARS));final_pool=[]
    for ci,c in enumerate(cands):
        ok,s=candidate_pass_on_training(c,all_idx,inner_limit=True)
        if ok:final_pool.append((s['inner_cv_nrmse'],s['train_nrmse'],ci,s))
    if not final_pool:
        out={'model':'Stage39 nested selection','n_candidates':len(cands),'n_final_rule_pass':0,'contract':CONTRACT,
             'nested_loocv':None,'selected':None,'status':'FAIL_NO_FINAL_CANDIDATE'}
        (OUT/'stage39_summary.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2));raise SystemExit(2)
    final_pool.sort();_,_,final_ci,final_stats=final_pool[0];final_c=cands[final_ci]
    final_b=final_stats['b'];final_pred=A0-final_b[0]*final_c['S']+final_b[1]*final_c['H']

    # OUTER LOOCV: each observed year is hidden from candidate ranking and fits.
    outer_pred=np.full(len(YEARS),np.nan);outer=[]
    for oi in range(len(YEARS)):
        tr=np.delete(all_idx,oi);pool=[]
        for ci,c in enumerate(cands):
            ok,s=candidate_pass_on_training(c,tr,inner_limit=True)
            if ok:pool.append((s['inner_cv_nrmse'],s['train_nrmse'],ci,s))
        if not pool:
            outer.append({'heldout_year':int(YEARS[oi]),'status':'NO_STRICT_INNER_CANDIDATE'})
            continue
        pool.sort();_,_,ci,s=pool[0];c=cands[ci];b=s['b']
        pr=float(A0-c['S'][oi]*b[0]+c['H'][oi]*b[1]);outer_pred[oi]=pr
        outer.append({'heldout_year':int(YEARS[oi]),'status':'OK','pred_m2':pr,'obs_m2':float(Y[oi]),
            'error_m2':pr-float(Y[oi]),'selected_candidate_index':int(ci),
            **{k:float(c[k]) for k in ALLKEYS},'K_colonizable_m2':float(b[0]),'K_hydro':float(b[1]),
            'inner_cv_nrmse':float(s['inner_cv_nrmse']),'train5_nrmse':float(s['train_nrmse'])})

    nested_ok=bool(np.all(np.isfinite(outer_pred)))
    if nested_ok:nrm,nrn=nrmse(outer_pred,Y)
    else:nrm=nrn=float('inf')

    selected={**{k:float(final_c[k]) for k in ALLKEYS},'K_colonizable_m2':float(final_b[0]),'K_hydro':float(final_b[1]),
        'rmse':float(nrmse(final_pred,Y)[0]),'nrmse':float(nrmse(final_pred,Y)[1]),
        'loocv_rmse':float(final_stats['inner_cv_rmse']),'loocv_nrmse':float(final_stats['inner_cv_nrmse']),
        'nested_loocv_rmse':float(nrm),'nested_loocv_nrmse':float(nrn),
        'state_year_corr':float(final_stats['state_year_corr']),
        'max_mass_error_m3':float(final_c['max_mass_error_m3']),
        'max_area_partition_error_m2':float(final_c['max_area_partition_error_m2']),
        'max_precip_partition_error_m3':float(final_c['max_precip_partition_error_m3']),
        **{f'pred_{int(y)}':float(final_pred[i]) for i,y in enumerate(YEARS)}}

    strict_nested_pass=(nested_ok and nrn<=NESTED_LOOCV_NRMSE_MAX_PCT)
    out={'model':'Stage39 nested selection, domain-corrected exact water balance',
         'n_candidates_interior_grid':len(cands),'n_final_rule_pass':len(final_pool),
         'selected':selected,'nested_outer_folds':outer,
         'nested_selection_pass':strict_nested_pass,
         'selection_order':'physical gates -> inner CV candidate selection -> outer hidden-year prediction; 2022 unopened',
         'contract':CONTRACT,'internal_grid_values':internal,'holdout_2022_used':False}
    (OUT/'stage39_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    pd.DataFrame(outer).to_csv(OUT/'stage39_nested_outer_predictions.csv',index=False)
    print(json.dumps(out,ensure_ascii=False,indent=2))
    if not strict_nested_pass:raise SystemExit('NESTED VALIDATION FAILED: do not open 2022 and do not relax rules')
if __name__=='__main__':main()
