#!/usr/bin/env python3
"""Stage68 — true 2024 forward hydroperiod validation of the official EGHM.

The mapped pond-area calibration/evaluation period ends in 2023. Raw AWS and
ASOS sunshine data both support a complete 2024 forcing year. This stage runs
2024 as a forward hydroperiod diagnostic with NO parameter refit, NO 2024 area
target, and NO use of 2024 NDWI in computation.

To ensure that extending the meteorology cannot change historical interpolation,
the frozen 2011-2023 deterministic forcing is generated exactly as before and a
separate 2024-only forcing block is appended. The Stage61d SHA contract is
checked on the historical block before the forward run.

External 2024 imagery is intentionally left outside the calculation. The model
output is intended for qualitative comparison with independently documented
recurrent spring exposure/drying and subsequent rewetting.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from eghm_deterministic_forcing import deterministic_forcing, source_missing_before_fill
from eghm_deterministic_kernel import SELECTED_STRUCTURE, hydro
from eghm_reproducibility_contract import EXPECTED_FINGERPRINTS

OUT=Path('stage68_outputs'); OUT.mkdir(exist_ok=True)
P=dict(SELECTED_STRUCTURE)
ZERO_EPS_M3=1e-9


def sha(a):
    arr=np.asarray(a,dtype='<f8')
    return hashlib.sha256(arr.tobytes(order='C')).hexdigest()


def check_historical_forcing_contract(F,cleaned):
    got={
        'clean_tmean':sha(cleaned['tmean']),'clean_tmin':sha(cleaned['tmin']),
        'clean_tmax':sha(cleaned['tmax']),'clean_pre':sha(cleaned['pre']),
        'clean_wind':sha(cleaned['wind']),'clean_sun':sha(cleaned['sun']),
        'forcing_pre':sha(F['pre']),'forcing_pes':sha(F['pes']),
        'forcing_eto':sha(F['eto']),'forcing_ep':sha(F['ep']),'forcing_pp':sha(F['pp']),
    }
    bad={k:(EXPECTED_FINGERPRINTS[k],v) for k,v in got.items() if EXPECTED_FINGERPRINTS[k]!=v}
    if bad:
        raise SystemExit(f'historical forcing contract changed: {bad!r}')
    return got


def concat_forcing(a,b):
    keys=('pre','pes','eto','ep','pp','year','month','date')
    return {k:np.concatenate([np.asarray(a[k]),np.asarray(b[k])]) for k in keys}


def dry_spells(dt,V):
    z=[float(v)<=ZERO_EPS_M3 for v in V]; out=[]; s=None
    for i,q in enumerate(z):
        if q and s is None: s=i
        if s is not None and ((not q) or i==len(z)-1):
            e=i if (q and i==len(z)-1) else i-1
            out.append({'start':str(dt[s].date()),'end':str(dt[e].date()),'days':e-s+1,
                        'start_month':int(dt[s].month),'end_month':int(dt[e].month),
                        'overlaps_mar_apr':any(int(dt[j].month) in (3,4) for j in range(s,e+1))})
            s=None
    return out


def monthly_2024(h,F):
    dt=pd.to_datetime(h['dates']); V=[float(v) for v in h['V']]; A=[float(v) for v in h['area']]
    pre=[float(v) for v in F['pre']]; qg=[float(v) for v in h['groundwater_loss']]
    qo=[float(v) for v in h['surface_outflow']]; qe=[float(v) for v in h['surface_evaporation']]
    rows=[]
    for m in range(1,13):
        ix=[i for i,d in enumerate(dt) if int(d.year)==2024 and int(d.month)==m]
        zv=[V[i]<=ZERO_EPS_M3 for i in ix]
        rows.append({
            'year':2024,'month':m,'days':len(ix),'zero_storage_days':sum(zv),
            'zero_storage_fraction':sum(zv)/len(ix),
            'mean_storage_m3':math.fsum(V[i] for i in ix)/len(ix),
            'min_storage_m3':min(V[i] for i in ix),'max_storage_m3':max(V[i] for i in ix),
            'mean_hydraulic_area_m2':math.fsum(A[i] for i in ix)/len(ix),
            'min_hydraulic_area_m2':min(A[i] for i in ix),'max_hydraulic_area_m2':max(A[i] for i in ix),
            'precip_mm':math.fsum(pre[i] for i in ix),
            'groundwater_loss_m3':math.fsum(qg[i] for i in ix),
            'surface_outflow_m3':math.fsum(qo[i] for i in ix),
            'surface_evap_m3':math.fsum(qe[i] for i in ix),
        })
    return rows


def main():
    # Frozen historical block; must remain bitwise identical to Stage61d.
    Fhist,miss_hist,annual_hist,clean_hist=deterministic_forcing()
    fp=check_historical_forcing_contract(Fhist,clean_hist)

    # Complete 2024 block generated independently so historical interpolation cannot move.
    s2024=datetime(2024,1,1); e2024=datetime(2024,12,31)
    F24,miss24,annual24,clean24=deterministic_forcing(start_date=s2024,end_date=e2024)
    source24=source_missing_before_fill(start_date=s2024,end_date=e2024)
    if len(F24['date'])!=366:
        raise SystemExit(f'2024 forcing is not a complete leap year: {len(F24["date"])} rows')
    if source24.get('sun',0)!=0:
        raise SystemExit(f'2024 ASOS sunshine is incomplete: {source24!r}')

    Fall=concat_forcing(Fhist,F24)
    h=hydro(Fall,P)
    dt=pd.to_datetime(h['dates'])
    ix24=[i for i,d in enumerate(dt) if int(d.year)==2024]
    V24=[float(h['V'][i]) for i in ix24]
    A24=[float(h['area'][i]) for i in ix24]
    d24=[dt[i] for i in ix24]
    z=[v<=ZERO_EPS_M3 for v in V24]
    spells=dry_spells(d24,V24)
    monthly=monthly_2024(h,Fall)

    spring_ix=[i for i,d in enumerate(d24) if int(d.month) in (3,4)]
    june_ix=[i for i,d in enumerate(d24) if int(d.month)==6]
    spring_zero=sum(1 for i in spring_ix if z[i])
    june_zero=sum(1 for i in june_ix if z[i])
    june_wet_days=len(june_ix)-june_zero

    # Timing: first nonzero-storage day after 30 April.
    after_apr=[i for i,d in enumerate(d24) if d>=pd.Timestamp('2024-05-01')]
    first_rewet=next((str(d24[i].date()) for i in after_apr if not z[i]),None)
    # First zero day in March-April, if any.
    first_spring_zero=next((str(d24[i].date()) for i in spring_ix if z[i]),None)

    pd.DataFrame(monthly).to_csv(OUT/'stage68_2024_monthly_hydroperiod.csv',index=False)
    pd.DataFrame(spells).to_csv(OUT/'stage68_2024_dry_spells.csv',index=False)
    pd.DataFrame({
        'date':d24,'surface_storage_m3':V24,'hydraulic_area_m2':A24,
        'zero_storage':[int(q) for q in z],
    }).to_csv(OUT/'stage68_2024_daily_hydroperiod.csv',index=False)

    closure={'mass_error_m3':float(h['mass_error']),'area_partition_error_m2':float(h['area_partition_error']),
             'precip_partition_error_m3':float(h['precip_partition_error'])}
    if max(closure.values())>1e-8:
        raise SystemExit(f'physical closure failed: {closure!r}')

    result={
        'status':'PASS_STAGE68_2024_FORWARD_HYDROPERIOD_VALIDATION',
        'model_refit_for_2024':False,'2024_mapped_area_target_used':False,'2024_NDWI_used_in_computation':False,
        'forcing_construction':'frozen 2011-2023 block + independently generated complete 2024 block',
        'historical_forcing_fingerprint_contract_pass':True,
        'historical_forcing_fingerprints':fp,
        'source_missing_2024_before_fill':source24,
        'forcing_missing_2024_legacy_semantics':miss24,
        'annual_precip_2024_mm':float(annual24[2024]),
        'selected_structure_unchanged':P,
        '2024':{
            'zero_storage_days':int(sum(z)),'zero_storage_fraction':float(sum(z)/366.0),
            'mar_apr_zero_storage_days':int(spring_zero),'mar_apr_days':len(spring_ix),
            'mar_apr_zero_fraction':float(spring_zero/len(spring_ix)),
            'june_zero_storage_days':int(june_zero),'june_wet_storage_days':int(june_wet_days),
            'first_spring_zero_date':first_spring_zero,
            'first_nonzero_storage_date_on_or_after_may1':first_rewet,
            'mean_storage_m3':float(math.fsum(V24)/len(V24)),
            'mean_hydraulic_area_m2':float(math.fsum(A24)/len(A24)),
            'longest_zero_spell_days':int(max((r['days'] for r in spells),default=0)),
            'dry_spells':spells,
            'monthly':monthly,
        },
        'external_comparison_rule':'Compare only qualitatively with independent 2024 evidence: recurrent spring exposure/drying and later rewetting. Monthly NDWI does not justify an exact dry-day-count target.',
        'physical_closure':closure,
    }
    (OUT/'stage68_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
