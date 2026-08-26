#!/usr/bin/env python3
"""Non-negotiable acceptance gates for Seoyeongari EGHM experiments.

These gates are intentionally stricter than ranking by accuracy. A candidate
that violates the physical/validation contract is rejected even if its RMSE is
lower. Spring drying is diagnostic only and is never a fitting/selection gate.
"""
from __future__ import annotations

EVAL_YEARS=(2013,2015,2017,2019,2021,2023)
HOLDOUT_YEAR=2022
MASS_TOL_M3=1e-8
NRMSE_MAX_PCT=2.0
LOOCV_NRMSE_MAX_PCT=2.0
STATE_YEAR_CORR_MAX=0.99
ZERO_TOL=1e-12

REQUIRED_CONTRACT={
    'lambda':0,
    'hard_cap':False,
    'freeboard':False,
    'explicit_time':False,
    'future_leakage':False,
    '2022_fit':False,
    'a2011_hard_max':False,
    'spring_dry_selection_requirement':False,
}

def contract_reasons(contract:dict)->list[str]:
    r=[]
    for k,v in REQUIRED_CONTRACT.items():
        if contract.get(k)!=v:
            r.append(f'contract:{k}={contract.get(k)!r}, required={v!r}')
    return r

def grid_boundary_reasons(candidate:dict, grids:dict[str,list[float]])->list[str]:
    """Reject calibrated search parameters at a tested grid edge.

    Edge hits are evidence that the optimum may lie outside the tested domain;
    the correct response is to expand/refine the domain, not accept the value.
    """
    r=[]
    for k,vals in grids.items():
        if k not in candidate or len(vals)<3:
            continue
        x=float(candidate[k]);lo=float(min(vals));hi=float(max(vals))
        if abs(x-lo)<=ZERO_TOL or abs(x-hi)<=ZERO_TOL:
            r.append(f'grid_boundary:{k}={x} on [{lo},{hi}]')
    return r

def candidate_reasons(candidate:dict, grids:dict[str,list[float]], contract:dict,
                      *, require_new_process:str|None=None,
                      require_short_hydro:bool=True)->list[str]:
    r=contract_reasons(contract)
    if float(candidate.get('max_mass_error_m3',float('inf')))>MASS_TOL_M3:
        r.append('mass_balance')
    if float(candidate.get('nrmse',float('inf')))>NRMSE_MAX_PCT:
        r.append('nrmse>2pct')
    if float(candidate.get('loocv_nrmse',float('inf')))>LOOCV_NRMSE_MAX_PCT:
        r.append('loocv_nrmse>2pct')
    if abs(float(candidate.get('state_year_corr',1.0)))>=STATE_YEAR_CORR_MAX:
        r.append('state_year_corr>=0.99')
    kc=float(candidate.get('K_colonizable_m2',0.0))
    a0=float(candidate.get('A0_m2',2241.762))
    if kc<=ZERO_TOL or kc>=a0-ZERO_TOL:
        r.append('K_colonizable_at_bound')
    if require_short_hydro and float(candidate.get('K_hydro',0.0))<=ZERO_TOL:
        r.append('short_hydrology_not_identified')
    if require_new_process and float(candidate.get(require_new_process,0.0))<=ZERO_TOL:
        r.append(f'new_process_not_identified:{require_new_process}')
    r.extend(grid_boundary_reasons(candidate,grids))
    return r

def accepted(*args,**kwargs)->bool:
    return not candidate_reasons(*args,**kwargs)
