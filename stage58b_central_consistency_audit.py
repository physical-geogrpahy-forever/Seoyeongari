#!/usr/bin/env python3
"""Stage58b — exact central-state regression consistency audit.

Stage57 and Stage58 produced a very small central-metric discrepancy despite
using the same checked-in Stage57 source and unchanged data/process files.
This script computes the Stage57 central state and Stage58 central state in the
same Python process and compares every relevant array before any scenario fit.
No model parameter is changed or optimized.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

import stage57_aprmay_four_scenario_peat as s57
import stage58_aprmay_oat_provenance as s58
from stage31_topmodel_vsa import forcing
from stage38_domain_corrected import hydro
from stage49_six_observation_irreversible_recruitment import irreversible_state

OUT=Path('stage58b_outputs'); OUT.mkdir(exist_ok=True)


def direct57():
    F,_,_=forcing()
    hp={k:s57.P56[k] for k in ['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']}
    h=hydro(F,hp)
    exposed=np.clip((s57.A0-np.asarray(h['area'],float))/s57.A0,0.,1.)
    ew=int(s57.P56['est_window_d'])
    E=pd.Series(exposed).rolling(ew,min_periods=ew).min().fillna(0.).to_numpy()
    st=irreversible_state(E,s57.P56['r_est_yr'])
    S=s57.aggregate(h['dates'],st)
    H=s57.hydro_feature(h['dates'],h['return_flow'],s57.P56['hydro_window_d'])
    Gd,_,_=s57.peat_geomorphic_loss(h['dates'],h['V'],s57.CENTRAL_PEAT_RATE)
    G=s57.aggregate(h['dates'],Gd)
    return h,S,H,G


def mx(a,b): return float(np.max(np.abs(np.asarray(a,float)-np.asarray(b,float))))


def scenario_metrics(S,H,G):
    out=[]
    for name,kc,kh,pred,rm,nr in s57.fit_scenarios(S,H,G):
        out.append({'Scenario':name,'RMSE_m2':float(rm),'nRMSE_pct':float(nr),'Kc':float(kc),'Kh':float(kh),
                    'pred':[float(x) for x in pred]})
    return out


def main():
    h57,S57,H57,G57=direct57()
    h58,S58,H58,G58,c58=s58.states(dict(s58.CENTRAL))
    diffs={
      'dates_equal': bool(np.array_equal(pd.to_datetime(h57['dates']).to_numpy(),pd.to_datetime(h58['dates']).to_numpy())),
      'surface_storage_V_max_abs_m3':mx(h57['V'],h58['V']),
      'hydraulic_area_max_abs_m2':mx(h57['area'],h58['area']),
      'return_flow_max_abs_m3':mx(h57['return_flow'],h58['return_flow']),
      'S_max_abs':mx(S57,S58),'H_max_abs_m3':mx(H57,H58),'G_max_abs_m2':mx(G57,G58),
    }
    m57=scenario_metrics(S57,H57,G57); m58=scenario_metrics(S58,H58,G58)
    md=max(abs(a['nRMSE_pct']-b['nRMSE_pct']) for a,b in zip(m57,m58))
    summary={
      'status':'PASS_EXACT_CONSISTENCY' if max([v for k,v in diffs.items() if k!='dates_equal'])<=1e-12 and diffs['dates_equal'] and md<=1e-12 else 'FAIL_CENTRAL_MISMATCH',
      'stage57_source_vs_stage58_state_differences':diffs,
      'scenario_nrmse_max_abs_difference_pp_same_process':float(md),
      'stage57_direct_metrics':m57,'stage58_state_metrics':m58,
      'P56':s57.P56,'P58_CENTRAL':s58.CENTRAL,
    }
    (OUT/'stage58b_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if summary['status']!='PASS_EXACT_CONSISTENCY':
        raise SystemExit('Stage57/58 central-state computation differs within one process')

if __name__=='__main__': main()
