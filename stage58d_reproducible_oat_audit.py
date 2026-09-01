#!/usr/bin/env python3
"""Stage58d — reproducible April-May OAT audit with hard central regression.

Supersedes the central-summary portion of the first Stage58 artifact. The OAT is
recomputed from scratch. Central state/coefficients are computed before and after
the OAT loop and must agree exactly (1e-12 tolerance) with a direct Stage57 fit.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import stage57_aprmay_four_scenario_peat as s57
import stage58_aprmay_oat_provenance as s58

OUT=Path('stage58d_outputs'); OUT.mkdir(exist_ok=True)
TOL=1e-12


def central_snapshot():
    cc,(h,S,H,G,corr)=s58.central_coefficients()
    direct=s57.fit_scenarios(S,H,G)
    rows=[]
    for name,kc,kh,pred,rm,nr in direct:
        rows.append({'Scenario':name,'RMSE_m2':float(rm),'nRMSE_pct':float(nr),'Kc':float(kc),'Kh':float(kh),
                     'pred':[float(x) for x in pred]})
        if abs(float(kc)-cc[name]['Kc'])>TOL or abs(float(kh)-cc[name]['Kh'])>TOL:
            raise SystemExit('central coefficient mismatch')
    return cc,h,S.copy(),H.copy(),G.copy(),float(corr),rows


def mx(a,b): return float(np.max(np.abs(np.asarray(a,float)-np.asarray(b,float))))


def main():
    cc,h0,S0,H0,G0,corr0,central0=central_snapshot()
    rows=[]
    for parameter,values in s58.OAT.items():
        for value in values:
            rows += s58.rows_for(parameter,value,'fixed',cc)
            rows += s58.rows_for(parameter,value,'profile_refit',cc)
    df=pd.DataFrame(rows)
    df.to_csv(OUT/'stage58d_oat_all.csv',index=False)
    df[df['mode']=='fixed'].to_csv(OUT/'stage58d_oat_fixed.csv',index=False)
    df[df['mode']=='profile_refit'].to_csv(OUT/'stage58d_oat_profile_refit.csv',index=False)

    cc1,h1,S1,H1,G1,corr1,central1=central_snapshot()
    consistency={
        'V_max_abs_m3':mx(h0['V'],h1['V']),
        'area_max_abs_m2':mx(h0['area'],h1['area']),
        'return_flow_max_abs_m3':mx(h0['return_flow'],h1['return_flow']),
        'S_max_abs':mx(S0,S1),'H_max_abs_m3':mx(H0,H1),'G_max_abs_m2':mx(G0,G1),
        'corr_abs':abs(corr0-corr1),
        'coeff_max_abs':max(abs(cc[k][q]-cc1[k][q]) for k in cc for q in ['Kc','Kh']),
        'central_metric_max_abs_pp':max(abs(a['nRMSE_pct']-b['nRMSE_pct']) for a,b in zip(central0,central1)),
    }
    if max(consistency.values())>TOL:
        raise SystemExit(f'central state mutated: {consistency}')

    nc=df[~df['is_central_value']]
    fixed_i=nc[(nc['mode']=='fixed')&(nc['Scenario']=='Integrated Model')]
    profile_i=nc[(nc['mode']=='profile_refit')&(nc['Scenario']=='Integrated Model')]
    reversals=[]
    for mode in ['fixed','profile_refit']:
        x=nc[nc['mode']==mode]
        for (parameter,value),g in x.groupby(['parameter','value']):
            top=g.sort_values('nRMSE_pct').iloc[0]
            integ=g[g['Scenario']=='Integrated Model'].iloc[0]
            if int(integ['rank'])!=1:
                reversals.append({
                    'mode':mode,'parameter':str(parameter),'value':float(value),
                    'top_scenario':str(top['Scenario']),'top_nRMSE_pct':float(top['nRMSE_pct']),
                    'Integrated_nRMSE_pct':float(integ['nRMSE_pct']),
                    'difference_pp':float(integ['nRMSE_pct']-top['nRMSE_pct'])})
    pd.DataFrame(reversals).to_csv(OUT/'stage58d_rank_reversals.csv',index=False)

    central_sorted=sorted([{k:v for k,v in r.items() if k!='pred'} for r in central1],key=lambda z:z['nRMSE_pct'])
    summary={
        'status':'PASS_STAGE58D_REPRODUCIBLE_OAT',
        'supersedes':'Stage58 first artifact central-summary values; Stage58 OAT architecture retained',
        'observation_support':'April-May','pond_area_observation_2022':'ABSENT',
        'central_process_parameters':s58.CENTRAL,'central_peat_rate_mm_yr':s58.PEAT_RATE,
        'central_metrics':central_sorted,
        'central_consistency':consistency,
        'noncentral_setting_count':int(len(fixed_i)),
        'fixed_integrated_rank1_count':int((fixed_i['rank']==1).sum()),
        'profile_integrated_rank1_count':int((profile_i['rank']==1).sum()),
        'rank_reversals':reversals,
        'oat_values_role':'internal admissible calibration-search support; not independent physical uncertainty intervals',
        'scenario_rank_not_acceptance_gate':True,
        'physical_closure':{'mass_error_m3':float(h1['mass_error']),'area_partition_error_m2':float(h1['area_partition_error']),'precip_partition_error_m3':float(h1['precip_partition_error'])},
    }
    (OUT/'stage58d_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
