#!/usr/bin/env python3
"""Stage65 — hydroperiod/process diagnosis of the deterministic EGHM model.

Purpose
-------
The central Stage62/63 model fits mapped April-May pond area well but produces
more complete zero-storage days than independent site observations suggest.
This stage does NOT recalibrate to hydroperiod observations. Instead it:

1. decomposes the central daily surface-water budget;
2. reports monthly and annual zero-storage timing, longest continuous dry runs,
   first drying and subsequent rewetting dates;
3. scans the pre-existing hydrologic OAT support one parameter at a time and
   reports how dry-day behavior changes alongside profile-refit Integrated nRMSE.

Independent field/site diagnostics (about 71-73 open-water-disappearance days
per year and spring drying concentrated around March-April) are used only for
external plausibility comparison, never as an optimization objective or gate.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import pandas as pd

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_kernel import (
    A0, EVAL_YEARS, OBS_MONTHS, SELECTED_STRUCTURE,
    annual_support, build_features,
)
from eghm_deterministic_scenarios import fit_four_scenarios, peat_geomorphic_loss

OUT = Path('stage65_outputs')
OUT.mkdir(exist_ok=True)
PEAT_RATE = 0.38
OBS = {
    2013: 2154.430, 2015: 2147.678, 2017: 2051.218,
    2019: 2045.159, 2021: 1965.256, 2023: 1882.700,
}
Y = [float(OBS[y]) for y in EVAL_YEARS]
CENTRAL = dict(SELECTED_STRUCTURE)
ZERO_EPS_M3 = 1e-9
INDEPENDENT_DRY_BAND_DAYS = (71.0, 73.0)
INDEPENDENT_DRY_MID_DAYS = 72.0

HYDRO_OAT = {
    'V0': [1000.0, 1600.0, 2200.0],
    'p_shape': [6.0, 12.0, 18.0],
    'tau_surf': [60.0, 120.0, 240.0],
    'local_frac': [0.15, 0.30, 0.45],
    'tau_fast': [30.0, 60.0, 120.0],
    'k_gw_mm_d': [0.05, 0.10, 0.25, 1.0, 2.0, 4.0],
}


def fsum(xs):
    return float(math.fsum(float(x) for x in xs))


def zero_flags(V: Sequence[float]) -> List[bool]:
    return [float(v) <= ZERO_EPS_M3 for v in V]


def runs(flags: Sequence[bool]) -> List[Tuple[int,int]]:
    out=[]; start=None
    for i,q in enumerate(flags):
        if q and start is None:
            start=i
        if start is not None and ((not q) or i==len(flags)-1):
            end=i if (q and i==len(flags)-1) else i-1
            out.append((start,end)); start=None
    return out


def annual_hydroperiod(dates, V):
    dt=pd.to_datetime(dates); flags=zero_flags(V)
    yy=[int(x) for x in dt.year]; mm=[int(x) for x in dt.month]
    rows=[]
    for y in range(2011,2024):
        idx=[i for i in range(len(dt)) if yy[i]==y]
        fy=[flags[i] for i in idx]; rr=runs(fy)
        z=sum(fy); spring=sum(1 for i in idx if flags[i] and mm[i] in (3,4))
        longest=max((b-a+1 for a,b in rr),default=0)
        first_zero=next((str(dt[idx[i]].date()) for i,q in enumerate(fy) if q),None)
        # First rewet after the first zero spell, if present.
        first_rewet=None
        if rr:
            local_end=rr[0][1]
            if local_end+1 < len(idx):
                first_rewet=str(dt[idx[local_end+1]].date())
        rows.append({
            'year':y,'zero_storage_days':int(z),'mar_apr_zero_days':int(spring),
            'spring_share_of_zero_days':(float(spring/z) if z else None),
            'dry_spell_count':len(rr),'longest_zero_run_days':int(longest),
            'first_zero_date':first_zero,'first_rewet_date_after_first_spell':first_rewet,
        })
    return rows


def monthly_hydroperiod(dates,V):
    dt=pd.to_datetime(dates); flags=zero_flags(V)
    rows=[]
    for y in range(2011,2024):
        for m in range(1,13):
            idx=[i for i in range(len(dt)) if int(dt[i].year)==y and int(dt[i].month)==m]
            rows.append({'year':y,'month':m,'zero_storage_days':sum(1 for i in idx if flags[i]),'days_in_series':len(idx)})
    return rows


def surface_budget(h, forcing):
    """Reconstruct surface inflow from storage change + explicitly returned losses."""
    dt=pd.to_datetime(h['dates']); V=[float(v) for v in h['V']]
    qret=[float(v) for v in h['return_flow']]
    qev=[float(v) for v in h['surface_evaporation']]
    qout=[float(v) for v in h['surface_outflow']]
    qgw=[float(v) for v in h['groundwater_loss']]
    pre=[float(v) for v in forcing['pre']]
    rows=[]; prev=float(CENTRAL['V0'])
    for i in range(len(V)):
        losses=qev[i]+qout[i]+qgw[i]
        total_inflow=V[i]-prev+losses
        nonreturn=total_inflow-qret[i]
        rows.append({
            'date':str(dt[i].date()),'year':int(dt[i].year),'month':int(dt[i].month),
            'precip_mm':pre[i],'surface_storage_m3':V[i],
            'return_flow_m3':qret[i],'other_surface_inflow_m3':nonreturn,
            'total_surface_inflow_m3':total_inflow,'surface_evap_m3':qev[i],
            'surface_outflow_m3':qout[i],'groundwater_loss_m3':qgw[i],
            'total_surface_loss_m3':losses,
        })
        prev=V[i]
    return rows


def budget_by_year(rows):
    out=[]
    for y in range(2011,2024):
        g=[r for r in rows if r['year']==y]
        ev=fsum(r['surface_evap_m3'] for r in g); qo=fsum(r['surface_outflow_m3'] for r in g); qg=fsum(r['groundwater_loss_m3'] for r in g)
        loss=ev+qo+qg
        ret=fsum(r['return_flow_m3'] for r in g); other=fsum(r['other_surface_inflow_m3'] for r in g); inflow=ret+other
        out.append({
            'year':y,'surface_inflow_m3':inflow,'return_flow_m3':ret,'other_surface_inflow_m3':other,
            'surface_loss_m3':loss,'surface_evap_m3':ev,'surface_outflow_m3':qo,'groundwater_loss_m3':qg,
            'evap_loss_fraction':(ev/loss if loss else None),'outflow_loss_fraction':(qo/loss if loss else None),
            'groundwater_loss_fraction':(qg/loss if loss else None),
        })
    return out


def drying_events(dates,h,budget_rows,antecedent_days=30):
    dt=pd.to_datetime(dates); flags=zero_flags(h['V']); ev=[]
    transitions=[i for i in range(len(flags)) if flags[i] and (i==0 or not flags[i-1])]
    for i in transitions:
        a=max(0,i-int(antecedent_days)+1); g=budget_rows[a:i+1]
        ev.append({
            'drying_date':str(dt[i].date()),'year':int(dt[i].year),'month':int(dt[i].month),
            'antecedent_days':i-a+1,
            'antecedent_precip_mm':fsum(r['precip_mm'] for r in g),
            'antecedent_return_flow_m3':fsum(r['return_flow_m3'] for r in g),
            'antecedent_other_surface_inflow_m3':fsum(r['other_surface_inflow_m3'] for r in g),
            'antecedent_evap_m3':fsum(r['surface_evap_m3'] for r in g),
            'antecedent_outflow_m3':fsum(r['surface_outflow_m3'] for r in g),
            'antecedent_groundwater_loss_m3':fsum(r['groundwater_loss_m3'] for r in g),
        })
    return ev


def profile_integrated(forcing,P):
    f=build_features(forcing,P,years=EVAL_YEARS,months=OBS_MONTHS); h=f['hydro']
    Gd,_,_=peat_geomorphic_loss(h['dates'],h['V'],PEAT_RATE,P['V0'],P['p_shape'])
    G=annual_support(h['dates'],Gd,years=EVAL_YEARS,months=OBS_MONTHS)
    sc=fit_four_scenarios(f['S'],f['H'],G,Y,a0=A0)
    integ=next(r for r in sc if r['Scenario']=='Integrated Model')
    ann=annual_hydroperiod(h['dates'],h['V'])
    mean_zero=fsum(r['zero_storage_days'] for r in ann)/len(ann)
    total_zero=sum(r['zero_storage_days'] for r in ann)
    spring=sum(r['mar_apr_zero_days'] for r in ann)
    return h,integ,ann,mean_zero,(spring/total_zero if total_zero else None)


def oat_hydroperiod_scan(forcing):
    rows=[]; seen=set()
    # include central exactly once
    settings=[('central',None,None,dict(CENTRAL))]
    for p,vals in HYDRO_OAT.items():
        for v in vals:
            if abs(float(v)-float(CENTRAL[p]))<1e-12:
                continue
            P=dict(CENTRAL); P[p]=v
            settings.append(('oat',p,float(v),P))
    for role,p,v,P in settings:
        h,integ,ann,mean_zero,spring_share=profile_integrated(forcing,P)
        maxrun=max(r['longest_zero_run_days'] for r in ann)
        rows.append({
            'role':role,'parameter':p,'value':v,
            'Integrated_profile_RMSE_m2':float(integ['RMSE_m2']),
            'Integrated_profile_nRMSE_pct':float(integ['nRMSE_pct']),
            'mean_zero_storage_days_per_year':float(mean_zero),
            'difference_from_independent_72d_diagnostic':float(mean_zero-INDEPENDENT_DRY_MID_DAYS),
            'spring_share_of_zero_days':spring_share,'max_annual_longest_zero_run_days':int(maxrun),
            'mass_error_m3':float(h['mass_error']),'area_partition_error_m2':float(h['area_partition_error']),
            'precip_partition_error_m3':float(h['precip_partition_error']),
        })
    return rows


def main():
    forcing,missing,annual,_=deterministic_forcing()
    f=build_features(forcing,CENTRAL,years=EVAL_YEARS,months=OBS_MONTHS); h=f['hydro']
    ann=annual_hydroperiod(h['dates'],h['V']); mon=monthly_hydroperiod(h['dates'],h['V'])
    bud=surface_budget(h,forcing); by=budget_by_year(bud); events=drying_events(h['dates'],h,bud,30)
    scan=oat_hydroperiod_scan(forcing)

    pd.DataFrame(ann).to_csv(OUT/'stage65_central_annual_hydroperiod.csv',index=False)
    pd.DataFrame(mon).to_csv(OUT/'stage65_central_monthly_hydroperiod.csv',index=False)
    pd.DataFrame(bud).to_csv(OUT/'stage65_central_daily_surface_budget.csv',index=False)
    pd.DataFrame(by).to_csv(OUT/'stage65_central_annual_surface_budget.csv',index=False)
    pd.DataFrame(events).to_csv(OUT/'stage65_drying_transition_30d_budget.csv',index=False)
    sdf=pd.DataFrame(scan).sort_values(['mean_zero_storage_days_per_year','Integrated_profile_nRMSE_pct'])
    sdf.to_csv(OUT/'stage65_hydrologic_oat_hydroperiod.csv',index=False)

    total_zero=sum(r['zero_storage_days'] for r in ann); spring=sum(r['mar_apr_zero_days'] for r in ann)
    mean_zero=total_zero/len(ann)
    viable=sdf[sdf['Integrated_profile_nRMSE_pct']<=2.0].copy()
    viable['abs_diff_72d']=abs(viable['mean_zero_storage_days_per_year']-INDEPENDENT_DRY_MID_DAYS)
    closer=viable.sort_values(['abs_diff_72d','Integrated_profile_nRMSE_pct']).head(8)

    loss_tot={
        'surface_evap_m3':fsum(r['surface_evap_m3'] for r in bud),
        'surface_outflow_m3':fsum(r['surface_outflow_m3'] for r in bud),
        'groundwater_loss_m3':fsum(r['groundwater_loss_m3'] for r in bud),
    }
    tl=sum(loss_tot.values())
    summary={
        'status':'PASS_STAGE65_HYDROPERIOD_PROCESS_DIAGNOSIS',
        'model_changed':False,'hydroperiod_used_for_calibration':False,
        'independent_diagnostic':{
            'open_water_disappearance_days_per_year':[71,73],
            'seasonal_expectation':'drying concentrated around March-April',
            'role':'external plausibility diagnostic only; not objective/gate',
        },
        'central':{
            'total_zero_storage_days_2011_2023':int(total_zero),
            'mean_zero_storage_days_per_year':float(mean_zero),
            'difference_from_72d_midpoint_days':float(mean_zero-INDEPENDENT_DRY_MID_DAYS),
            'mar_apr_zero_days_total':int(spring),
            'spring_share_of_zero_days':float(spring/total_zero if total_zero else 0.0),
            'maximum_longest_zero_run_days':int(max(r['longest_zero_run_days'] for r in ann)),
        },
        'central_surface_loss_totals_2011_2023_m3':loss_tot,
        'central_surface_loss_fractions':{k.replace('_m3','_fraction'):float(v/tl if tl else 0.0) for k,v in loss_tot.items()},
        'drying_transition_count':len(events),
        'hydrologic_oat_noncentral_setting_count':len(scan)-1,
        'nrmse_le_2pct_settings_closest_to_independent_72d_diagnostic':closer.drop(columns=['abs_diff_72d']).to_dict('records'),
        'forcing_source_missing_before_fill':missing,'annual_precip_mm':annual,
        'physical_closure':{
            'mass_error_m3':float(h['mass_error']),'area_partition_error_m2':float(h['area_partition_error']),
            'precip_partition_error_m3':float(h['precip_partition_error']),
        },
        'interpretation_rule':'Do not select a parameter from closeness to 71-73 d alone; use this table to identify which process terms cause excessive drying and then seek independent physical constraints.',
    }
    if max(summary['physical_closure'].values())>1e-8:
        raise SystemExit('Stage65 physical closure failed')
    (OUT/'stage65_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
