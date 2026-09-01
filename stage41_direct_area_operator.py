#!/usr/bin/env python3
"""Stage41 — direct conserved-area observation operator + bidirectional ecology.

Stage40 showed K_hydro=0 for every candidate, so the fitted return-flow anomaly
term is explicitly removed rather than silently accepting a zero coefficient.
Stage41 uses Stage38's conserved-storage-derived open-water area directly:

  A_obs(t) = A_hydro(t) * (1 - c_cover * x(t))

x(t) is the Stage40 causal bidirectional hydroperiod state. c_cover is a bounded
(0,1) maximum fraction of hydrologically wetted area rendered non-open by the
ecological occupancy state. Ecology does not change storage or fluxes.

The hydrologic parameter guards are widened so all Stage38 tested values are
interior candidates; this preserves the no-grid-edge gate while allowing the
new observation operator to select hydrologic structure. 2022 remains sealed.
"""
from __future__ import annotations
import itertools,json
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing,OBS
from stage38_domain_corrected import hydro
from stage40_bidirectional_hydroperiod import bidirectional_hydroperiod_state
from eghm_strict_rules import (EVAL_YEARS,MASS_TOL_M3,AREA_PARTITION_TOL_M2,
 PRECIP_PARTITION_TOL_M3,NRMSE_MAX_PCT,LOOCV_NRMSE_MAX_PCT,
 NESTED_LOOCV_NRMSE_MAX_PCT,STATE_YEAR_CORR_MAX,ZERO_TOL,grid_boundary_reasons)

OUT=Path('stage41_outputs');OUT.mkdir(exist_ok=True)
YEARS=np.array(EVAL_YEARS,int);Y=np.array([OBS[int(y)] for y in YEARS],float)
assert tuple(sorted(OBS))==EVAL_YEARS
GRIDS={
 'V0':[700.,1000.,1600.,2200.,3000.],
 'p_shape':[3.,6.,12.,18.,30.],
 'tau_surf':[30.,60.,120.,240.,480.],
 'local_frac':[.05,.15,.30,.45,.60],
 'tau_fast':[15.,30.,60.,120.,240.],
 'k_gw_mm_d':[.02,.05,.10,.25,1.,2.,4.],
 'r_est_yr':[.01,.025,.05,.10,.25],
 'r_flood_yr':[.05,.10,.25,.50,1.],
}
HKEYS=['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']
ALLKEYS=HKEYS+['r_est_yr','r_flood_yr']
CONTRACT={'lambda':0,'hard_cap':False,'freeboard':False,'explicit_time':False,
 'future_leakage':False,'2022_fit':False,'a2011_hard_max':False,
 'spring_dry_selection_requirement':False,'domain_double_count':False,
 'rainfall_partition_exact':True,'surface_loss_priority':False,
 'nested_cv_selection':True,'hyperparameter_holdout_leakage':False,
 'short_term_K_hydro_removed_explicitly':True,
 'observation_operator':'direct_conserved_hydrologic_area_times_ecological_open_fraction'}

def annual(dt,x,years=YEARS):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy()
    return np.array([float(np.mean(x[(yr==y)&np.isin(mo,[5,6])])) for y in years])

def fit_cover(B,C,y):
    B=np.asarray(B,float);C=np.asarray(C,float);y=np.asarray(y,float)
    d=float(np.dot(C,C));c=float(np.dot(C,B-y)/d) if d else 0.
    c=float(np.clip(c,0.,1.));return c,B-c*C

def nrmse(pred,y):
    pred=np.asarray(pred,float);y=np.asarray(y,float);rm=float(np.sqrt(np.mean((pred-y)**2)))
    return rm,100.*rm/float(np.mean(y))

def fixed_cv(cand,idx):
    idx=np.asarray(idx,int);pp=[]
    for j in range(len(idx)):
        tr=np.delete(idx,j);te=idx[j];cc,_=fit_cover(cand['B'][tr],cand['C'][tr],Y[tr])
        pp.append(float(cand['B'][te]-cc*cand['C'][te]))
    return nrmse(np.array(pp),Y[idx])

def state_corr(cand,idx):
    idx=np.asarray(idx,int);s=cand['S'][idx]
    return float(np.corrcoef(s,YEARS[idx])[0,1]) if np.std(s)>ZERO_TOL else 1.

def structural_ok(c):
    return (not grid_boundary_reasons(c,GRIDS) and c['k_gw_mm_d']>ZERO_TOL and
      c['r_flood_yr']>ZERO_TOL and c['total_reversal']>ZERO_TOL and
      c['max_reversal_daily']>ZERO_TOL and c['hydro_effect_range_m2']>ZERO_TOL and
      c['max_mass_error_m3']<=MASS_TOL_M3 and c['max_area_partition_error_m2']<=AREA_PARTITION_TOL_M2 and
      c['max_precip_partition_error_m3']<=PRECIP_PARTITION_TOL_M3)

def pass_train(c,idx):
    idx=np.asarray(idx,int)
    if not structural_ok(c):return False,None
    corr=state_corr(c,idx)
    if abs(corr)>=STATE_YEAR_CORR_MAX:return False,None
    cc,p=fit_cover(c['B'][idx],c['C'][idx],Y[idx])
    if cc<=ZERO_TOL or cc>=1.-ZERO_TOL:return False,None
    rm,nr=nrmse(p,Y[idx]);crm,cn=fixed_cv(c,idx)
    if nr>NRMSE_MAX_PCT or cn>LOOCV_NRMSE_MAX_PCT:return False,None
    return True,{'cover':cc,'train_rmse':rm,'train_nrmse':nr,'inner_cv_rmse':crm,
      'inner_cv_nrmse':cn,'state_year_corr':corr}

def build_candidates(F):
    internal={k:[v for v in vals if v!=min(vals) and v!=max(vals)] for k,vals in GRIDS.items()};out=[]
    for vals in itertools.product(*[internal[k] for k in HKEYS]):
        hp=dict(zip(HKEYS,vals));h=hydro(F,hp);B=annual(h['dates'],h['area']);hr=float(B.max()-B.min())
        for re,rf in itertools.product(internal['r_est_yr'],internal['r_flood_yr']):
            z=bidirectional_hydroperiod_state(h['area'],re,rf);S=annual(h['dates'],z['state']);C=annual(h['dates'],h['area']*z['state'])
            out.append({**hp,'r_est_yr':re,'r_flood_yr':rf,'B':B,'C':C,'S':S,
              'hydro_effect_range_m2':hr,'total_establishment':z['total_establishment'],
              'total_reversal':z['total_reversal'],'max_reversal_daily':z['max_reversal_daily'],
              'max_mass_error_m3':float(h['mass_error']),'max_area_partition_error_m2':float(h['area_partition_error']),
              'max_precip_partition_error_m3':float(h['precip_partition_error'])})
    return out,internal

def reject_reasons(c,idx):
    r=list(grid_boundary_reasons(c,GRIDS));corr=state_corr(c,idx)
    if c['hydro_effect_range_m2']<=ZERO_TOL:r.append('short_hydrology_not_present')
    if c['r_flood_yr']<=ZERO_TOL or c['total_reversal']<=ZERO_TOL:r.append('flood_reversal_not_identified')
    if c['max_mass_error_m3']>MASS_TOL_M3:r.append('mass_balance')
    if c['max_area_partition_error_m2']>AREA_PARTITION_TOL_M2:r.append('area_partition')
    if c['max_precip_partition_error_m3']>PRECIP_PARTITION_TOL_M3:r.append('precip_partition')
    if abs(corr)>=STATE_YEAR_CORR_MAX:r.append('state_year_corr>=0.99')
    cc,p=fit_cover(c['B'][idx],c['C'][idx],Y[idx]);rm,nr=nrmse(p,Y[idx]);crm,cn=fixed_cv(c,idx)
    if cc<=ZERO_TOL or cc>=1.-ZERO_TOL:r.append('cover_fraction_at_bound')
    if nr>NRMSE_MAX_PCT:r.append('training_nrmse>2pct')
    if cn>LOOCV_NRMSE_MAX_PCT:r.append('fixed_candidate_loocv>2pct')
    return r,cc,rm,nr,crm,cn,corr,p

def diagnostics(cands,idx):
    rows=[]
    for i,c in enumerate(cands):
        r,cc,rm,nr,crm,cn,corr,p=reject_reasons(c,idx)
        rows.append({'candidate_index':i,**{k:float(c[k]) for k in ALLKEYS},'cover_fraction':cc,
          'rmse_m2':rm,'nrmse_pct':nr,'fixed_cv_rmse_m2':crm,'fixed_cv_nrmse_pct':cn,
          'state_year_corr':corr,'hydro_effect_range_m2':c['hydro_effect_range_m2'],
          'total_reversal':c['total_reversal'],'reasons':r,
          **{f'hydro_{int(y)}':float(c['B'][j]) for j,y in enumerate(YEARS)},
          **{f'pred_{int(y)}':float(p[j]) for j,y in enumerate(YEARS)}})
    rows.sort(key=lambda z:(len(z['reasons']),z['fixed_cv_nrmse_pct'],z['nrmse_pct']))
    return rows,dict(Counter(x for z in rows for x in z['reasons']))

def main():
    F,_,_=forcing();cands,internal=build_candidates(F);idx=np.arange(len(YEARS));rows,counts=diagnostics(cands,idx)
    pd.DataFrame(rows).to_csv(OUT/'stage41_rejection_diagnostics.csv',index=False);pool=[]
    for i,c in enumerate(cands):
        ok,s=pass_train(c,idx)
        if ok:pool.append((s['inner_cv_nrmse'],s['train_nrmse'],i,s))
    base={'model':'Stage41 direct conserved-area observation operator + bidirectional ecology',
      'n_candidates_interior_grid':len(cands),'contract':CONTRACT,'internal_grid_values':internal,
      'holdout_2022_used':False,'rejection_reason_counts':counts,'best_rejected_preview':rows[:12]}
    if not pool:
        out={**base,'n_final_rule_pass':0,'selected':None,'nested_selection_pass':False,'status':'FAIL_NO_FINAL_CANDIDATE'}
        (OUT/'stage41_summary.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2));raise SystemExit(2)
    pool.sort();_,_,ci,fs=pool[0];fc=cands[ci];cover=fs['cover'];fp=fc['B']-cover*fc['C']
    op=np.full(len(YEARS),np.nan);outer=[]
    for oi in range(len(YEARS)):
        tr=np.delete(idx,oi);pp=[]
        for j,c in enumerate(cands):
            ok,s=pass_train(c,tr)
            if ok:pp.append((s['inner_cv_nrmse'],s['train_nrmse'],j,s))
        if not pp:outer.append({'heldout_year':int(YEARS[oi]),'status':'NO_STRICT_INNER_CANDIDATE'});continue
        pp.sort();_,_,j,s=pp[0];c=cands[j];pr=float(c['B'][oi]-s['cover']*c['C'][oi]);op[oi]=pr
        outer.append({'heldout_year':int(YEARS[oi]),'status':'OK','pred_m2':pr,'obs_m2':float(Y[oi]),
          'error_m2':pr-float(Y[oi]),**{k:float(c[k]) for k in ALLKEYS},'cover_fraction':float(s['cover']),
          'inner_cv_nrmse':float(s['inner_cv_nrmse']),'train5_nrmse':float(s['train_nrmse']),
          'state_year_corr_train5':float(s['state_year_corr'])})
    nok=bool(np.all(np.isfinite(op)));nrm,nrn=nrmse(op,Y) if nok else (float('inf'),float('inf'));trm,trn=nrmse(fp,Y)
    sel={**{k:float(fc[k]) for k in ALLKEYS},'cover_fraction':float(cover),'rmse':trm,'nrmse':trn,
      'loocv_rmse':float(fs['inner_cv_rmse']),'loocv_nrmse':float(fs['inner_cv_nrmse']),
      'nested_loocv_rmse':float(nrm),'nested_loocv_nrmse':float(nrn),'state_year_corr':float(fs['state_year_corr']),
      'hydro_effect_range_m2':float(fc['hydro_effect_range_m2']),'total_establishment':float(fc['total_establishment']),
      'total_reversal':float(fc['total_reversal']),'max_reversal_daily':float(fc['max_reversal_daily']),
      'max_mass_error_m3':float(fc['max_mass_error_m3']),'max_area_partition_error_m2':float(fc['max_area_partition_error_m2']),
      'max_precip_partition_error_m3':float(fc['max_precip_partition_error_m3']),
      **{f'hydro_{int(y)}':float(fc['B'][i]) for i,y in enumerate(YEARS)},
      **{f'pred_{int(y)}':float(fp[i]) for i,y in enumerate(YEARS)}}
    passed=(nok and nrn<=NESTED_LOOCV_NRMSE_MAX_PCT and trn<=NRMSE_MAX_PCT and sel['loocv_nrmse']<=LOOCV_NRMSE_MAX_PCT and
      abs(sel['state_year_corr'])<STATE_YEAR_CORR_MAX and sel['cover_fraction']>ZERO_TOL and sel['cover_fraction']<1.-ZERO_TOL and
      sel['r_flood_yr']>ZERO_TOL and sel['total_reversal']>ZERO_TOL and sel['hydro_effect_range_m2']>ZERO_TOL and
      sel['max_mass_error_m3']<=MASS_TOL_M3 and sel['max_area_partition_error_m2']<=AREA_PARTITION_TOL_M2 and
      sel['max_precip_partition_error_m3']<=PRECIP_PARTITION_TOL_M3 and not grid_boundary_reasons(sel,GRIDS))
    out={**base,'n_final_rule_pass':len(pool),'selected':sel,'nested_outer_folds':outer,'nested_selection_pass':bool(passed),
      'status':'PASS_LOCKED_READY_FOR_2022' if passed else 'FAIL_NESTED_SELECTION'}
    (OUT/'stage41_summary.json').write_text(json.dumps(out,indent=2),encoding='utf-8');pd.DataFrame(outer).to_csv(OUT/'stage41_nested_outer_predictions.csv',index=False)
    print(json.dumps(out,indent=2))
    if not passed:raise SystemExit('Stage41 failed; 2022 remains sealed')
if __name__=='__main__':main()
