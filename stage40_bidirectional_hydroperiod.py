#!/usr/bin/env python3
"""Stage40: Stage38 exact hydrology + bidirectional causal hydroperiod ecology.
Ecology: dx/dt=r_est*E*(1-x)-r_flood*F*x, where E and F are trailing-only
exposed/inundated fractions of the 2011 open-water footprint. No year trend,
future leakage, or ecological water source/sink is introduced. Process form is
supported by Casanova & Brock (2000), Webb et al. (2012, Aquatic Botany,
doi:10.1016/j.aquabot.2012.06.003), Slusher et al. (2014,
doi:10.2134/jeq2013.06.0227), and Bartholomew et al. (2020,
doi:10.1007/s13157-020-01383-5). Rates remain site-calibrated within broad
literature-consistent annual-to-multidecadal response scales. 2022 stays sealed
until all strict + nested-CV gates pass.
"""
from __future__ import annotations
import itertools,json
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing,OBS
from stage35c_mass_balance_state_operator import A0
from stage38_domain_corrected import hydro
from stage39_nested_selection import fit_constrained,nrmse,fixed_candidate_cv
from eghm_strict_rules import (EVAL_YEARS,MASS_TOL_M3,AREA_PARTITION_TOL_M2,
 PRECIP_PARTITION_TOL_M3,NRMSE_MAX_PCT,LOOCV_NRMSE_MAX_PCT,
 NESTED_LOOCV_NRMSE_MAX_PCT,STATE_YEAR_CORR_MAX,ZERO_TOL,grid_boundary_reasons)

OUT=Path('stage40_outputs');OUT.mkdir(exist_ok=True)
YEARS=np.array(EVAL_YEARS,int);Y=np.array([OBS[int(y)] for y in YEARS],float)
assert tuple(sorted(OBS))==EVAL_YEARS
GRIDS={
 'V0':[1000.,1600.,2200.],'p_shape':[6.,12.,18.],
 'tau_surf':[60.,120.,240.],'local_frac':[.15,.30,.45],
 'tau_fast':[30.,60.,120.],
 # expanded below prior 0.25 edge; no gate is relaxed
 'k_gw_mm_d':[.05,.10,.25,1.,2.,4.],
 'r_est_yr':[.01,.025,.05,.10,.25,.50],
 'r_flood_yr':[.05,.10,.25,.50,1.,2.],
 'hydro_window_d':[7,14,30,60,90],
}
HKEYS=['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']
ALLKEYS=HKEYS+['r_est_yr','r_flood_yr','hydro_window_d'];ECO_LAG_D=28
CONTRACT={'lambda':0,'hard_cap':False,'freeboard':False,'explicit_time':False,
 'future_leakage':False,'2022_fit':False,'a2011_hard_max':False,
 'spring_dry_selection_requirement':False,'domain_double_count':False,
 'rainfall_partition_exact':True,'surface_loss_priority':False,
 'nested_cv_selection':True,'hyperparameter_holdout_leakage':False}

def bidirectional_hydroperiod_state(area,r_est_yr,r_flood_yr,lag_d=ECO_LAG_D):
    a=np.asarray(area,float)
    E=pd.Series(np.clip((A0-a)/A0,0,1)).rolling(lag_d,min_periods=1).mean().to_numpy()
    F=pd.Series(np.clip(a/A0,0,1)).rolling(lag_d,min_periods=1).mean().to_numpy()
    x=0.;st=np.empty(len(a));upv=np.empty(len(a));dnv=np.empty(len(a))
    ae=float(r_est_yr)/365.;af=float(r_flood_yr)/365.
    for i,(e,f) in enumerate(zip(E,F)):
        up=ae*e*(1-x);dn=af*f*x;x=float(np.clip(x+up-dn,0,1))
        st[i]=x;upv[i]=up;dnv[i]=dn
    return {'state':st,'exposure':E,'flood':F,'establishment_flux':upv,
      'reversal_flux':dnv,'total_establishment':float(upv.sum()),
      'total_reversal':float(dnv.sum()),'max_reversal_daily':float(dnv.max())}

def annual(dt,x,years=YEARS):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy()
    return np.array([float(np.mean(x[(yr==y)&np.isin(mo,[5,6])])) for y in years])

def annual_hydro(dt,q,w,years=YEARS):
    yr=dt.year.to_numpy();mo=dt.month.to_numpy()
    rr=pd.Series(q,index=dt).rolling(int(w),min_periods=1).sum().to_numpy()
    ref=float(np.mean(rr[(yr==2011)&np.isin(mo,[5,6])]))
    return np.array([float(np.mean(rr[(yr==y)&np.isin(mo,[5,6])])-ref) for y in years])

def state_corr(c,idx):
    idx=np.asarray(idx,int);s=c['S'][idx]
    return float(np.corrcoef(s,YEARS[idx])[0,1]) if np.std(s)>ZERO_TOL else 1.

def coeff_ok(b):return b[0]>ZERO_TOL and b[0]<A0-ZERO_TOL and b[1]>ZERO_TOL

def structural_ok(c):
    return (not grid_boundary_reasons(c,GRIDS) and c['k_gw_mm_d']>ZERO_TOL and
      c['r_flood_yr']>ZERO_TOL and c['total_reversal']>ZERO_TOL and
      c['max_reversal_daily']>ZERO_TOL and c['max_mass_error_m3']<=MASS_TOL_M3 and
      c['max_area_partition_error_m2']<=AREA_PARTITION_TOL_M2 and
      c['max_precip_partition_error_m3']<=PRECIP_PARTITION_TOL_M3)

def pass_train(c,idx):
    idx=np.asarray(idx,int)
    if not structural_ok(c):return False,None
    corr=state_corr(c,idx)
    if abs(corr)>=STATE_YEAR_CORR_MAX:return False,None
    b,p=fit_constrained(c['S'][idx],c['H'][idx],Y[idx])
    if not coeff_ok(b):return False,None
    rm,nr=nrmse(p,Y[idx]);crm,cn=fixed_candidate_cv(c,idx)
    if nr>NRMSE_MAX_PCT or cn>LOOCV_NRMSE_MAX_PCT:return False,None
    return True,{'b':b,'train_rmse':rm,'train_nrmse':nr,'inner_cv_rmse':crm,
      'inner_cv_nrmse':cn,'state_year_corr':corr}

def build_candidates(F):
    internal={k:[v for v in vals if v!=min(vals) and v!=max(vals)] for k,vals in GRIDS.items()}
    out=[]
    for vals in itertools.product(*[internal[k] for k in HKEYS]):
        hp=dict(zip(HKEYS,vals));h=hydro(F,hp);ec={}
        for re,rf in itertools.product(internal['r_est_yr'],internal['r_flood_yr']):
            z=bidirectional_hydroperiod_state(h['area'],re,rf)
            ec[(re,rf)]=(annual(h['dates'],z['state']),z['total_establishment'],
                         z['total_reversal'],z['max_reversal_daily'])
        hc={w:annual_hydro(h['dates'],h['return_flow'],w) for w in internal['hydro_window_d']}
        for re,rf,w in itertools.product(internal['r_est_yr'],internal['r_flood_yr'],internal['hydro_window_d']):
            S,te,tr,mr=ec[(re,rf)]
            out.append({**hp,'r_est_yr':re,'r_flood_yr':rf,'hydro_window_d':w,
              'S':S,'H':hc[w],'total_establishment':te,'total_reversal':tr,
              'max_reversal_daily':mr,'max_mass_error_m3':float(h['mass_error']),
              'max_area_partition_error_m2':float(h['area_partition_error']),
              'max_precip_partition_error_m3':float(h['precip_partition_error'])})
    return out,internal

def reasons(c,idx):
    r=list(grid_boundary_reasons(c,GRIDS));corr=state_corr(c,idx)
    if c['k_gw_mm_d']<=ZERO_TOL:r.append('new_process_not_identified:k_gw_mm_d')
    if c['r_flood_yr']<=ZERO_TOL:r.append('new_process_not_identified:r_flood_yr')
    if c['total_reversal']<=ZERO_TOL or c['max_reversal_daily']<=ZERO_TOL:r.append('flood_reversal_flux_zero')
    if c['max_mass_error_m3']>MASS_TOL_M3:r.append('mass_balance')
    if c['max_area_partition_error_m2']>AREA_PARTITION_TOL_M2:r.append('area_partition')
    if c['max_precip_partition_error_m3']>PRECIP_PARTITION_TOL_M3:r.append('precip_partition')
    if abs(corr)>=STATE_YEAR_CORR_MAX:r.append('state_year_corr>=0.99')
    b,p=fit_constrained(c['S'][idx],c['H'][idx],Y[idx]);rm,nr=nrmse(p,Y[idx]);crm,cn=fixed_candidate_cv(c,idx)
    if b[0]<=ZERO_TOL or b[0]>=A0-ZERO_TOL:r.append('K_colonizable_at_bound')
    if b[1]<=ZERO_TOL:r.append('K_hydro<=0')
    if nr>NRMSE_MAX_PCT:r.append('training_nrmse>2pct')
    if cn>LOOCV_NRMSE_MAX_PCT:r.append('fixed_candidate_loocv>2pct')
    return r,b,rm,nr,crm,cn,corr,p

def diagnostics(cands,idx):
    rows=[]
    for i,c in enumerate(cands):
        r,b,rm,nr,crm,cn,corr,p=reasons(c,idx)
        rows.append({'candidate_index':i,**{k:float(c[k]) for k in ALLKEYS},
          'K_colonizable_m2':float(b[0]),'K_hydro':float(b[1]),'rmse_m2':rm,
          'nrmse_pct':nr,'fixed_cv_rmse_m2':crm,'fixed_cv_nrmse_pct':cn,
          'state_year_corr':corr,'total_reversal':c['total_reversal'],'reasons':r,
          **{f'pred_{int(y)}':float(p[j]) for j,y in enumerate(YEARS)}})
    rows.sort(key=lambda z:(len(z['reasons']),z['fixed_cv_nrmse_pct'],z['nrmse_pct']))
    return rows,dict(Counter(x for z in rows for x in z['reasons']))

def main():
    F,_,_=forcing();cands,internal=build_candidates(F);idx=np.arange(len(YEARS))
    rows,counts=diagnostics(cands,idx);pd.DataFrame(rows).to_csv(OUT/'stage40_rejection_diagnostics.csv',index=False)
    pool=[]
    for i,c in enumerate(cands):
        ok,s=pass_train(c,idx)
        if ok:pool.append((s['inner_cv_nrmse'],s['train_nrmse'],i,s))
    base={'model':'Stage40 bidirectional hydroperiod ecology','n_candidates_interior_grid':len(cands),
      'contract':CONTRACT,'internal_grid_values':internal,'ecology_lag_days':ECO_LAG_D,
      'holdout_2022_used':False,'rejection_reason_counts':counts,'best_rejected_preview':rows[:12]}
    if not pool:
        out={**base,'n_final_rule_pass':0,'selected':None,'nested_loocv':None,
          'nested_selection_pass':False,'status':'FAIL_NO_FINAL_CANDIDATE'}
        (OUT/'stage40_summary.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2));raise SystemExit(2)
    pool.sort();_,_,ci,fs=pool[0];fc=cands[ci];fb=fs['b'];fp=A0-fb[0]*fc['S']+fb[1]*fc['H']
    outer_pred=np.full(len(YEARS),np.nan);outer=[]
    for oi in range(len(YEARS)):
        tr=np.delete(idx,oi);pp=[]
        for j,c in enumerate(cands):
            ok,s=pass_train(c,tr)
            if ok:pp.append((s['inner_cv_nrmse'],s['train_nrmse'],j,s))
        if not pp:
            outer.append({'heldout_year':int(YEARS[oi]),'status':'NO_STRICT_INNER_CANDIDATE'});continue
        pp.sort();_,_,j,s=pp[0];c=cands[j];b=s['b'];pr=float(A0-c['S'][oi]*b[0]+c['H'][oi]*b[1]);outer_pred[oi]=pr
        outer.append({'heldout_year':int(YEARS[oi]),'status':'OK','pred_m2':pr,'obs_m2':float(Y[oi]),
          'error_m2':pr-float(Y[oi]),**{k:float(c[k]) for k in ALLKEYS},
          'K_colonizable_m2':float(b[0]),'K_hydro':float(b[1]),'inner_cv_nrmse':float(s['inner_cv_nrmse']),
          'train5_nrmse':float(s['train_nrmse']),'state_year_corr_train5':float(s['state_year_corr'])})
    nested_ok=bool(np.all(np.isfinite(outer_pred)));nrm,nrn=nrmse(outer_pred,Y) if nested_ok else (float('inf'),float('inf'))
    trm,trn=nrmse(fp,Y)
    sel={**{k:float(fc[k]) for k in ALLKEYS},'K_colonizable_m2':float(fb[0]),'K_hydro':float(fb[1]),
      'rmse':trm,'nrmse':trn,'loocv_rmse':float(fs['inner_cv_rmse']),'loocv_nrmse':float(fs['inner_cv_nrmse']),
      'nested_loocv_rmse':float(nrm),'nested_loocv_nrmse':float(nrn),'state_year_corr':float(fs['state_year_corr']),
      'total_establishment':float(fc['total_establishment']),'total_reversal':float(fc['total_reversal']),
      'max_reversal_daily':float(fc['max_reversal_daily']),'max_mass_error_m3':float(fc['max_mass_error_m3']),
      'max_area_partition_error_m2':float(fc['max_area_partition_error_m2']),
      'max_precip_partition_error_m3':float(fc['max_precip_partition_error_m3']),
      **{f'pred_{int(y)}':float(fp[i]) for i,y in enumerate(YEARS)}}
    passed=(nested_ok and nrn<=NESTED_LOOCV_NRMSE_MAX_PCT and trn<=NRMSE_MAX_PCT and
      sel['loocv_nrmse']<=LOOCV_NRMSE_MAX_PCT and abs(sel['state_year_corr'])<STATE_YEAR_CORR_MAX and
      sel['r_flood_yr']>ZERO_TOL and sel['total_reversal']>ZERO_TOL and
      sel['max_mass_error_m3']<=MASS_TOL_M3 and sel['max_area_partition_error_m2']<=AREA_PARTITION_TOL_M2 and
      sel['max_precip_partition_error_m3']<=PRECIP_PARTITION_TOL_M3 and not grid_boundary_reasons(sel,GRIDS))
    out={**base,'n_final_rule_pass':len(pool),'selected':sel,'nested_outer_folds':outer,
      'nested_selection_pass':bool(passed),'status':'PASS_LOCKED_READY_FOR_2022' if passed else 'FAIL_NESTED_SELECTION'}
    (OUT/'stage40_summary.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    pd.DataFrame(outer).to_csv(OUT/'stage40_nested_outer_predictions.csv',index=False);print(json.dumps(out,indent=2))
    if not passed:raise SystemExit('Stage40 failed; 2022 remains sealed')
if __name__=='__main__':main()
