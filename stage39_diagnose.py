#!/usr/bin/env python3
"""Explain Stage39 rejections without changing any gate or parameter."""
import json
from pathlib import Path
import numpy as np
from stage31_topmodel_vsa import forcing
from stage35c_mass_balance_state_operator import A0
from stage39_nested_selection import (build_candidates,YEARS,Y,fit_constrained,nrmse,
    fixed_candidate_cv,structural_ok,coeff_ok,GRIDS,HKEYS,ALLKEYS)
from eghm_strict_rules import (NRMSE_MAX_PCT,LOOCV_NRMSE_MAX_PCT,
    STATE_YEAR_CORR_MAX,grid_boundary_reasons,MASS_TOL_M3,
    AREA_PARTITION_TOL_M2,PRECIP_PARTITION_TOL_M3,ZERO_TOL)
OUT=Path('stage39_outputs');OUT.mkdir(exist_ok=True)

def main():
    F,_,_=forcing();cands,internal=build_candidates(F);rows=[];idx=np.arange(len(YEARS))
    for ci,c in enumerate(cands):
        b,p=fit_constrained(c['S'],c['H'],Y);rm,nr=nrmse(p,Y);crm,cn=fixed_candidate_cv(c,idx)
        corr=float(np.corrcoef(c['S'],YEARS)[0,1]) if np.std(c['S'])>0 else 1.0
        reasons=[]
        reasons += grid_boundary_reasons(c,GRIDS)
        if c['k_gw_mm_d']<=ZERO_TOL:reasons.append('new_process_not_identified:k_gw_mm_d')
        if c['max_mass_error_m3']>MASS_TOL_M3:reasons.append('mass_balance')
        if c['max_area_partition_error_m2']>AREA_PARTITION_TOL_M2:reasons.append('area_partition')
        if c['max_precip_partition_error_m3']>PRECIP_PARTITION_TOL_M3:reasons.append('precip_partition')
        if abs(corr)>=STATE_YEAR_CORR_MAX:reasons.append('state_year_corr>=0.99')
        if not coeff_ok(b):
            if b[0]<=ZERO_TOL or b[0]>=A0-ZERO_TOL:reasons.append('K_colonizable_at_bound')
            if b[1]<=ZERO_TOL:reasons.append('K_hydro<=0')
        if nr>NRMSE_MAX_PCT:reasons.append('training_nrmse>2pct')
        if cn>LOOCV_NRMSE_MAX_PCT:reasons.append('fixed_candidate_loocv>2pct')
        rows.append({'candidate_index':ci,**{k:float(c[k]) for k in ALLKEYS},
                     'K_colonizable_m2':float(b[0]),'K_hydro':float(b[1]),
                     'rmse_m2':rm,'nrmse_pct':nr,'fixed_cv_rmse_m2':crm,'fixed_cv_nrmse_pct':cn,
                     'state_year_corr':corr,'max_mass_error_m3':c['max_mass_error_m3'],
                     'max_area_partition_error_m2':c['max_area_partition_error_m2'],
                     'max_precip_partition_error_m3':c['max_precip_partition_error_m3'],
                     'reasons':reasons,
                     **{f'state_{int(y)}':float(c['S'][j]) for j,y in enumerate(YEARS)},
                     **{f'hydro_{int(y)}':float(c['H'][j]) for j,y in enumerate(YEARS)},
                     **{f'pred_{int(y)}':float(p[j]) for j,y in enumerate(YEARS)}})
    out={'model':'Stage39 rejection diagnostics','rules_changed':False,'n_candidates':len(rows),'candidates':rows,'internal_grid_values':internal}
    (OUT/'stage39_rejection_diagnostics.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
