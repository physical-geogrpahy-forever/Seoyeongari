#!/usr/bin/env python3
"""Stage66 — seasonal dryness forensics for deterministic EGHM.

No calibration or model selection is performed. We compare the accepted central
hydrology with three Stage65 diagnostic perturbations that bring mean annual
zero-storage days closer to the independent ~71-73 d site diagnostic:
  p_shape=6, k_gw=2 mm/d, tau_surf=120 d.

The purpose is to test whether those changes also repair *timing* (March-April
concentration and realistic rewetting), or merely reduce the annual total while
leaving long out-of-season dry spells.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List

import pandas as pd

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_kernel import SELECTED_STRUCTURE, build_features

OUT=Path('stage66_outputs'); OUT.mkdir(exist_ok=True)
CENTRAL=dict(SELECTED_STRUCTURE)
ZERO_EPS=1e-9

CASES={
    'central':{},
    'p_shape_6':{'p_shape':6.0},
    'k_gw_2':{'k_gw_mm_d':2.0},
    'tau_surf_120':{'tau_surf':120.0},
}


def flags(V): return [float(v)<=ZERO_EPS for v in V]


def spans(dt,z):
    out=[]; s=None
    for i,q in enumerate(z):
        if q and s is None: s=i
        if s is not None and ((not q) or i==len(z)-1):
            e=i if (q and i==len(z)-1) else i-1
            out.append((s,e)); s=None
    return out


def summarize_case(name,P,forcing):
    f=build_features(forcing,P); h=f['hydro']; dt=pd.to_datetime(h['dates']); z=flags(h['V'])
    yy=[int(d.year) for d in dt]; mm=[int(d.month) for d in dt]
    monthly=[]
    for m in range(1,13):
        n=sum(1 for i,q in enumerate(z) if q and mm[i]==m)
        monthly.append({'case':name,'month':m,'zero_days_2011_2023':n,'mean_zero_days_per_year':n/13.0})
    annual=[]; spells=[]
    for y in range(2011,2024):
        idx=[i for i in range(len(dt)) if yy[i]==y]
        zy=[z[i] for i in idx]; localsp=spans([dt[i] for i in idx],zy)
        az=sum(zy); ma=sum(1 for i in idx if z[i] and mm[i] in (3,4))
        out=sum(1 for i in idx if z[i] and mm[i] not in (3,4))
        annual.append({'case':name,'year':y,'zero_days':az,'mar_apr_zero_days':ma,'outside_mar_apr_zero_days':out,
                       'spring_share':ma/az if az else None,'longest_spell':max((e-s+1 for s,e in localsp),default=0)})
        for s,e in localsp:
            gs=idx[s]; ge=idx[e]
            spells.append({'case':name,'year':y,'start':str(dt[gs].date()),'end':str(dt[ge].date()),'days':e-s+1,
                           'start_month':int(dt[gs].month),'end_month':int(dt[ge].month),
                           'overlaps_mar_apr':any(mm[idx[j]] in (3,4) for j in range(s,e+1))})
    total=sum(r['zero_days'] for r in annual); spring=sum(r['mar_apr_zero_days'] for r in annual)
    outside=total-spring
    month_rank=sorted(monthly,key=lambda r:(-r['zero_days_2011_2023'],r['month']))
    longsp=sorted(spells,key=lambda r:(-r['days'],r['start']))[:10]
    return h,monthly,annual,spells,{
        'case':name,'parameters':P,'total_zero_days':total,'mean_zero_days_per_year':total/13.0,
        'mar_apr_zero_days':spring,'outside_mar_apr_zero_days':outside,
        'spring_share':spring/total if total else None,
        'outside_spring_share':outside/total if total else None,
        'top_dry_months':[{'month':r['month'],'zero_days':r['zero_days_2011_2023']} for r in month_rank[:5]],
        'longest_spells':longsp[:5],
        'mass_error_m3':float(h['mass_error']),'area_error_m2':float(h['area_partition_error']),
        'precip_error_m3':float(h['precip_partition_error']),
    }


def main():
    forcing,missing,annual_precip,_=deterministic_forcing()
    allm=[]; alla=[]; alls=[]; summaries=[]
    for name,delta in CASES.items():
        P=dict(CENTRAL); P.update(delta)
        h,m,a,s,summary=summarize_case(name,P,forcing)
        allm+=m; alla+=a; alls+=s; summaries.append(summary)
    pd.DataFrame(allm).to_csv(OUT/'stage66_monthly_zero_days.csv',index=False)
    pd.DataFrame(alla).to_csv(OUT/'stage66_annual_zero_days.csv',index=False)
    pd.DataFrame(alls).to_csv(OUT/'stage66_dry_spells.csv',index=False)

    # Direct month-by-month comparison table.
    md=pd.DataFrame(allm).pivot(index='month',columns='case',values='mean_zero_days_per_year').reset_index()
    md.to_csv(OUT/'stage66_monthly_case_comparison.csv',index=False)

    result={
        'status':'PASS_STAGE66_SEASONAL_DRYNESS_FORENSICS',
        'model_calibrated_to_hydroperiod':False,
        'independent_expectation':{'annual_open_water_disappearance_days':[71,73],'drying_season':'March-April concentrated'},
        'cases':summaries,
        'key_test':'A candidate that only reduces annual zero-day total but leaves most zero days outside March-April does not resolve the seasonal hydroperiod mismatch.',
        'forcing_missing_before_fill':missing,'annual_precip_mm':annual_precip,
    }
    if any(max(x['mass_error_m3'],x['area_error_m2'],x['precip_error_m3'])>1e-8 for x in summaries):
        raise SystemExit('Stage66 physical closure failed')
    (OUT/'stage66_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
