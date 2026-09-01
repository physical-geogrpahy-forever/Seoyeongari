#!/usr/bin/env python3
"""Stage69 — separate mapped wetland extent, hydraulic state, and visible pool.

No scientific process or fitted parameter is changed in this stage.

The original thesis defines the 2011-2023 remote-sensing series as wetland-area
change associated with terrestrial vegetation/forest encroachment and movement
of the wetland-transition boundary. It is therefore a long-term mapped wetland
extent, not a daily binary observation of open surface water.

The hydro kernel separately produces conserved surface storage V and hydraulic
wetted area A(V). A third quantity — whether a shallow seasonal pool is visibly
expressed above peat/vegetation microtopography — is not currently mapped from V
by an independently constrained observation rule. Consequently V==0 remains a
hydraulic-zero diagnostic but is not used here as a definition of visible-pool
absence.

This audit re-runs the frozen 2011-2023 model and a split-block 2024 forward run,
reports deterministic water depth, and verifies that correcting terminology does
not change the official Stage63 mapped-wetland-extent result.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_geometry import depth_v_deterministic
from eghm_deterministic_kernel import (
    A0, EVAL_YEARS, OBS_MONTHS, SELECTED_STRUCTURE,
    annual_support, build_features, hydro,
)
from eghm_deterministic_scenarios import fit_four_scenarios, peat_geomorphic_loss
from eghm_reproducibility_contract import EXPECTED_FINGERPRINTS

OUT=Path('stage69_outputs'); OUT.mkdir(exist_ok=True)
P=dict(SELECTED_STRUCTURE)
PEAT_RATE=0.38
OBS={2013:2154.430,2015:2147.678,2017:2051.218,2019:2045.159,2021:1965.256,2023:1882.700}
Y=[float(OBS[y]) for y in EVAL_YEARS]
EXPECTED_INTEGRATED_NRMSE=1.4113250129695185


def sha(a):
    return hashlib.sha256(np.asarray(a,dtype='<f8').tobytes(order='C')).hexdigest()


def forcing_contract(F,cleaned):
    got={
        'clean_tmean':sha(cleaned['tmean']),'clean_tmin':sha(cleaned['tmin']),
        'clean_tmax':sha(cleaned['tmax']),'clean_pre':sha(cleaned['pre']),
        'clean_wind':sha(cleaned['wind']),'clean_sun':sha(cleaned['sun']),
        'forcing_pre':sha(F['pre']),'forcing_pes':sha(F['pes']),
        'forcing_eto':sha(F['eto']),'forcing_ep':sha(F['ep']),'forcing_pp':sha(F['pp']),
    }
    bad={k:(EXPECTED_FINGERPRINTS[k],v) for k,v in got.items() if EXPECTED_FINGERPRINTS[k]!=v}
    if bad: raise SystemExit(f'frozen forcing contract failed: {bad!r}')
    return got


def concat_forcing(a,b):
    return {k:np.concatenate([np.asarray(a[k]),np.asarray(b[k])]) for k in ('pre','pes','eto','ep','pp','year','month','date')}


def official_stage63_check(Fhist):
    f=build_features(Fhist,P,years=EVAL_YEARS,months=OBS_MONTHS); h=f['hydro']
    Gd,_,_=peat_geomorphic_loss(h['dates'],h['V'],PEAT_RATE,P['V0'],P['p_shape'])
    G=annual_support(h['dates'],Gd,years=EVAL_YEARS,months=OBS_MONTHS)
    rows=fit_four_scenarios(f['S'],f['H'],G,Y,a0=A0)
    integ=next(r for r in rows if r['Scenario']=='Integrated Model')
    if abs(float(integ['nRMSE_pct'])-EXPECTED_INTEGRATED_NRMSE)>1e-12:
        raise SystemExit(f'Stage63 mapped-extent result moved: {integ!r}')
    return rows,h


def monthly_depth_2024(h):
    dt=pd.to_datetime(h['dates']); rows=[]
    for m in range(1,13):
        ix=[i for i,d in enumerate(dt) if int(d.year)==2024 and int(d.month)==m]
        V=[float(h['V'][i]) for i in ix]
        A=[float(h['area'][i]) for i in ix]
        D=[depth_v_deterministic(v,P['V0'],P['p_shape'],A0=A0) for v in V]
        rows.append({
            'month':m,'days':len(ix),
            'mean_surface_storage_m3':math.fsum(V)/len(V),
            'min_surface_storage_m3':min(V),'max_surface_storage_m3':max(V),
            'mean_hydraulic_wetted_area_m2':math.fsum(A)/len(A),
            'min_hydraulic_wetted_area_m2':min(A),'max_hydraulic_wetted_area_m2':max(A),
            'mean_equivalent_water_depth_m':math.fsum(D)/len(D),
            'min_equivalent_water_depth_m':min(D),'max_equivalent_water_depth_m':max(D),
            'hydraulic_zero_days':sum(1 for v in V if v<=1e-9),
        })
    return rows


def main():
    Fhist,miss_hist,annual_hist,cleaned=deterministic_forcing()
    fp=forcing_contract(Fhist,cleaned)
    scen,hist_h=official_stage63_check(Fhist)

    F24,miss24,annual24,_=deterministic_forcing(start_date=datetime(2024,1,1),end_date=datetime(2024,12,31))
    Fall=concat_forcing(Fhist,F24)
    h=hydro(Fall,P)
    monthly=monthly_depth_2024(h)
    pd.DataFrame(monthly).to_csv(OUT/'stage69_2024_hydraulic_depth_by_month.csv',index=False)
    pd.DataFrame([
        {'rank':i+1,'Scenario':r['Scenario'],'RMSE_m2':float(r['RMSE_m2']),'nRMSE_pct':float(r['nRMSE_pct']),
         'K_colonizable_m2':float(r['K_colonizable_m2']),'K_hydro_m2_per_m3':float(r['K_hydro_m2_per_m3'])}
        for i,r in enumerate(sorted(scen,key=lambda z:z['nRMSE_pct']))
    ]).to_csv(OUT/'stage69_frozen_mapped_extent_metrics.csv',index=False)

    spring=[r for r in monthly if r['month'] in (3,4)]
    june=next(r for r in monthly if r['month']==6)
    closure={'mass_error_m3':float(h['mass_error']),'area_partition_error_m2':float(h['area_partition_error']),
             'precip_partition_error_m3':float(h['precip_partition_error'])}
    if max(closure.values())>1e-8: raise SystemExit(f'closure failed: {closure!r}')

    result={
        'status':'PASS_STAGE69_OBSERVATION_SEMANTICS_AUDIT',
        'model_process_changed':False,'model_parameter_changed':False,
        'observation_contract':{
            'long_term_target':{
                'name':'mapped wetland extent','years':list(EVAL_YEARS),'process_support_months':list(OBS_MONTHS),
                'source_semantics':'satellite/aerial delineation of wetland/transition boundary under terrestrial-vegetation and forest encroachment',
                'not_equivalent_to':'daily open-water presence',
            },
            'hydraulic_state':{
                'name':'conserved daily surface storage and hydraulic wetted area','source':'mass-conserved model state',
                'zero_storage_role':'hydraulic-zero diagnostic only',
            },
            'seasonal_hydroperiod_validation':{
                'name':'visible surface-pool presence/exposure and rewetting','source':'field observations and independent remote sensing',
                'current_direct_observation_operator_available':False,
                'arbitrary_depth_or_area_threshold_forbidden':True,
            },
        },
        'reason_for_correction':'The thesis remote-sensing area series tracks wetland extent/terrestrial encroachment, while spring pool disappearance is a separate seasonal hydrologic observation.',
        'frozen_stage63_integrated_nRMSE_pct':float(next(r for r in scen if r['Scenario']=='Integrated Model')['nRMSE_pct']),
        'frozen_stage63_metrics_unchanged':True,
        'historical_forcing_contract_pass':True,'historical_forcing_fingerprints':fp,
        '2024_hydraulic_state':{
            'annual_precip_mm':float(annual24[2024]),
            'source_missing_legacy_semantics':miss24,
            'march':next(r for r in monthly if r['month']==3),
            'april':next(r for r in monthly if r['month']==4),
            'may':next(r for r in monthly if r['month']==5),
            'june':june,
            'monthly':monthly,
        },
        'interpretation':[
            'Stage68 finding of zero hydraulic-zero days in 2024 does not by itself prove that a visible surface pool persisted all year.',
            'Conversely, the model currently cannot claim successful reproduction of visible spring pool disappearance because no independently constrained V/depth-to-visible-pool mapping exists.',
            'Do not alter k_gw, tau_surf, p_shape, or other process parameters merely to force V to numerical zero in spring.',
            'Any future visible-pool surface-expression layer must be constrained independently (e.g. site microtopography/water-level or image-linked geometry), not fitted solely to desired dry timing.',
        ],
        'physical_closure':closure,
    }
    (OUT/'stage69_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
