#!/usr/bin/env python3
"""Stage63 — official deterministic April-May four-scenario peat comparison.

No process parameter search is performed. The Stage62 structure and
reproducibility contract are locked. Peat rates are external sensitivity values:
0.29/0.38/0.47 mm/yr are the primary persistent-net interval; 2.89/5.91/7.00
mm/yr are recent-apparent stress tests only. Scenario rank is reported, never
used as an acceptance criterion. 2022 mapped pond area is absent.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_kernel import (
    A0,EVAL_YEARS,OBS_MONTHS,SELECTED_STRUCTURE,
    annual_support,build_features,sha256_f8,
)
from eghm_deterministic_scenarios import peat_geomorphic_loss,fit_four_scenarios
from eghm_reproducibility_contract import EXPECTED_FINGERPRINTS

OUT=Path('stage63_outputs'); OUT.mkdir(exist_ok=True)
OBS={2013:2154.430,2015:2147.678,2017:2051.218,2019:2045.159,2021:1965.256,2023:1882.700}
PRIMARY=[0.29,0.38,0.47]
CENTRAL=0.38
STRESS=[2.89,5.91,7.00]


def main():
    years=tuple(EVAL_YEARS); y=[OBS[v] for v in years]
    assert tuple(sorted(OBS))==years and 2022 not in OBS and 2022 not in years
    F,_,_,cleaned=deterministic_forcing()
    run=build_features(F,SELECTED_STRUCTURE,years=years,months=OBS_MONTHS)
    h=run['hydro']; eco=run['ecology']; S=[float(v) for v in run['S']]; H=[float(v) for v in run['H']]

    # The central hydro/ecology trajectory must still be exactly the Stage61/62 contract.
    checks={
        'V':sha256_f8(h['V']),'area':sha256_f8(h['area']),'return_flow':sha256_f8(h['return_flow']),
        'exposed':sha256_f8(eco['exposed']),'E7':sha256_f8(eco['exposure_window']),
        'state':sha256_f8(eco['state']),'S':sha256_f8(S),'H':sha256_f8(H),
    }
    mismatch={k:(EXPECTED_FINGERPRINTS[k],v) for k,v in checks.items() if EXPECTED_FINGERPRINTS[k]!=v}
    if mismatch: raise SystemExit(f'central deterministic contract changed: {mismatch}')

    allrows=[]; geomrows=[]; predrows=[]
    for rate in PRIMARY+STRESS:
        Gd,h0,B=peat_geomorphic_loss(h['dates'],h['V'],rate,SELECTED_STRUCTURE['V0'],SELECTED_STRUCTURE['p_shape'])
        G=annual_support(h['dates'],Gd,years=years,months=OBS_MONTHS)
        scen=fit_four_scenarios(S,H,G,y,A0)
        ordered=sorted(scen,key=lambda z:(z['nRMSE_pct'],z['RMSE_m2'],z['Scenario']))
        rank={z['Scenario']:i+1 for i,z in enumerate(ordered)}
        for z in scen:
            row={
                'peat_rate_mm_yr':float(rate),'Scenario':z['Scenario'],
                'RMSE_m2':z['RMSE_m2'],'nRMSE_pct':z['nRMSE_pct'],'rank':rank[z['Scenario']],
                'K_colonizable_m2':z['K_colonizable_m2'],'K_hydro_m2_per_m3':z['K_hydro_m2_per_m3'],
            }
            for i,yr in enumerate(years): row[f'pred_{yr}']=float(z['pred'][i])
            allrows.append(row)
            if rate==CENTRAL:
                for i,yr in enumerate(years):
                    predrows.append({'Scenario':z['Scenario'],'year':yr,'observed_m2':y[i],
                                     'predicted_m2':float(z['pred'][i]),'error_m2':float(z['pred'][i]-y[i])})
        idx2023=max(i for i,d in enumerate(h['dates']) if int(d.year)==2023)
        gr={'peat_rate_mm_yr':float(rate),'h0_reference_depth_m':float(h0),
            'peat_rise_2023_end_m':float(B[idx2023]),
            'mean_geomorphic_loss_eval_m2':sum(G)/len(G),'G_sha256_daily':sha256_f8(Gd)}
        for i,yr in enumerate(years): gr[f'G_{yr}_m2']=float(G[i])
        geomrows.append(gr)

    # CSVs without pandas reductions.
    with (OUT/'stage63_four_scenario_peat.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
    with (OUT/'stage63_geomorphic_translation.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(geomrows[0]));w.writeheader();w.writerows(geomrows)
    with (OUT/'stage63_central_predictions.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(predrows[0]));w.writeheader();w.writerows(predrows)

    central=sorted([r for r in allrows if r['peat_rate_mm_yr']==CENTRAL],key=lambda z:z['nRMSE_pct'])
    primary_integrated=sorted([r for r in allrows if r['peat_rate_mm_yr'] in PRIMARY and r['Scenario']=='Integrated Model'],key=lambda z:z['peat_rate_mm_yr'])
    primary_hydro=sorted([r for r in allrows if r['peat_rate_mm_yr'] in PRIMARY and r['Scenario']=='Hydrosere Only Model'],key=lambda z:z['peat_rate_mm_yr'])
    result={
        'status':'PASS_STAGE63_OFFICIAL_DETERMINISTIC_FOUR_SCENARIO_PEAT',
        'observation_support':'April-May mean','eval_years':list(years),'2022_pond_area_used':False,
        'selected_structure':dict(SELECTED_STRUCTURE),'primary_persistent_net_peat_rates_mm_yr':PRIMARY,
        'central_peat_rate_mm_yr':CENTRAL,'recent_apparent_stress_rates_mm_yr':STRESS,
        'central_metrics':[{k:r[k] for k in ['Scenario','RMSE_m2','nRMSE_pct','rank','K_colonizable_m2','K_hydro_m2_per_m3']} for r in central],
        'integrated_rank1_all_primary_peat_rates':all(r['rank']==1 for r in primary_integrated),
        'integrated_primary_nrmse_pct':[r['nRMSE_pct'] for r in primary_integrated],
        'hydrosere_primary_nrmse_pct':[r['nRMSE_pct'] for r in primary_hydro],
        'geomorphic_translation':geomrows,'scenario_rank_not_acceptance_gate':True,
        'physical_closure':{'mass_error_m3':h['mass_error'],'area_partition_error_m2':h['area_partition_error'],'precip_partition_error_m3':h['precip_partition_error']},
        'central_hydroecology_contract_pass':True,
        'notes':[
            'Peat changes surface-expression geometry only; it does not remove water from conserved storage.',
            'Primary peat interval is externally motivated and is not selected to make Integrated rank first.',
            'Stress rates 2.89-7.00 mm/yr are not interpreted as persistent long-term topographic rise.',
        ],
    }
    (OUT/'stage63_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if max(result['physical_closure'].values())>1e-8: raise SystemExit('physical closure failed')

if __name__=='__main__': main()
