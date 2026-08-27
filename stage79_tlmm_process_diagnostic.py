#!/usr/bin/env python3
"""Stage79 — exact published TLMM boundary-recursion diagnostic for EGHM.

The official Keddy & Campbell supplementary workbook was audited before this
implementation.  TLMM does not simulate independent elevation-band scores; it
recursively evolves Marsh Lower Limit (MLL) and Marsh Upper Limit (MUL)
elevations from the annual growing-season water-level history.  This script
uses those exact recurrences and converts the resulting elevation zones to
planform area with the existing EGHM hypsometry.

This remains a pre-coupling process diagnostic: hydrologic mass balance is not
changed; vegetation-specific ET and peat feedback are not yet activated.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Sequence

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_geometry import area_h_deterministic, depth_v_deterministic, reference_depth
from eghm_deterministic_kernel import A0, SELECTED_STRUCTURE, hydro, mean_fsum
from tlmm_core import (
    C_MIN_DEFAULT,W_MIN_DEFAULT,F_TEMPERATE_YR,S_TEMPERATE_YR,S_GREAT_LAKES_EXAMPLE_YR,
    boundary_history,
)

OUT=Path('stage79_outputs'); OUT.mkdir(exist_ok=True)
YEARS=tuple(range(2011,2024))
PARAMS=(
    ('general_temperate',F_TEMPERATE_YR,S_TEMPERATE_YR),
    ('great_lakes_published_example',F_TEMPERATE_YR,S_GREAT_LAKES_EXAMPLE_YR),
)


def annual_month_mean(dates: Sequence[object], values: Sequence[float], month: int) -> Dict[int,float]:
    out={}
    for y in YEARS:
        vals=[float(v) for d,v in zip(dates,values) if int(d.year)==y and int(d.month)==int(month)]
        if not vals: raise ValueError(f'no month {month} values in {y}')
        out[y]=mean_fsum(vals)
    return out


def area_at_boundary(z: float, h0: float, p_shape: float) -> float:
    """Convert a TLMM elevation boundary to area inside the mapped 2011 pond."""
    zc=min(max(float(z),0.0),float(h0))
    return area_h_deterministic(zc,h0,p_shape,A0=A0,A_WET=A0)


def run_one(name: str, f_yr: float, s_yr: float, sep_wl: Dict[int,float],
            h0: float, p_shape: float):
    wls=[sep_wl[y] for y in YEARS]

    # Site initialization, not a fitted transition parameter: the model starts
    # from the mapped 2011 pond footprint.  Within that footprint no persistent
    # marsh/woody zone is imposed at t0, so MLL=MUL at its mapped upper edge h0.
    hist=boundary_history(
        YEARS,wls,f_yr=f_yr,s_yr=s_yr,cmin=C_MIN_DEFAULT,wmin=W_MIN_DEFAULT,
        initial_lower_limit=h0,initial_upper_limit=h0,
    )

    rows=[]; max_partition=0.0; max_order_error=0.0
    for r in hist:
        order_error=max(float(r.marsh_lower_limit)-float(r.marsh_upper_limit),0.0)
        max_order_error=max(max_order_error,order_error)
        if order_error>1e-10:
            raise AssertionError(f'MLL>MUL in {r.year}: {r.marsh_lower_limit}>{r.marsh_upper_limit}')

        a_lower=area_at_boundary(r.marsh_lower_limit,h0,p_shape)
        a_upper=area_at_boundary(r.marsh_upper_limit,h0,p_shape)
        aquatic=a_lower
        marsh=a_upper-a_lower
        woody=A0-a_upper
        total=aquatic+marsh+woody
        max_partition=max(max_partition,abs(total-A0))
        hydraulic_sep=area_at_boundary(r.water_level,h0,p_shape)
        rows.append({
            'parameterization':name,'f_yr':f_yr,'s_yr':s_yr,'year':r.year,
            'september_mean_water_level_m':r.water_level,
            'dt_flood_yr':r.dt_flood_yr,'lower_response_F':r.lower_response,
            'marsh_lower_limit_m':r.marsh_lower_limit,
            'xt_dewater_yr':r.xt_dewater_yr,'upper_response_K':r.upper_response,
            'marsh_upper_limit_m':r.marsh_upper_limit,
            'hydraulic_surface_planform_at_september_m2':hydraulic_sep,
            'tlmm_aquatic_zone_m2':aquatic,'tlmm_marsh_zone_m2':marsh,
            'tlmm_woody_zone_m2':woody,'cover_partition_m2':total,
        })
    return rows,{
        'max_cover_partition_error_m2':max_partition,
        'max_boundary_order_error_m':max_order_error,
        'initial_MLL_m':h0,'initial_MUL_m':h0,
    }


def main():
    F,_,_,_=deterministic_forcing(); P=dict(SELECTED_STRUCTURE); h=hydro(F,P)
    p=float(P['p_shape']); v0=float(P['V0']); h0=reference_depth(v0,p,A0=A0)
    depths=[depth_v_deterministic(v,v0,p,A0=A0) for v in h['V']]
    sep_wl=annual_month_mean(h['dates'],depths,9)

    rows=[]; audits={}
    for name,f,s in PARAMS:
        rr,audit=run_one(name,f,s,sep_wl,h0,p)
        rows.extend(rr); audits[name]=audit

    with (OUT/'stage79_tlmm_boundary_states.csv').open('w',newline='',encoding='utf-8') as fp:
        w=csv.DictWriter(fp,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    compact={}
    for name,_,_ in PARAMS:
        compact[name]=[
            {k:r[k] for k in ('year','september_mean_water_level_m','marsh_lower_limit_m','marsh_upper_limit_m',
                              'tlmm_aquatic_zone_m2','tlmm_marsh_zone_m2','tlmm_woody_zone_m2')}
            for r in rows if r['parameterization']==name
        ]

    result={
      'status':'PASS_STAGE79_EXACT_TLMM_ESM_BOUNDARY_DIAGNOSTIC',
      'model_source':{
        'citation':'Keddy PA, Campbell D (2020) Wetlands 40:667-680',
        'doi':'10.1007/s13157-019-01229-9',
        'official_esm':'13157_2019_1229_MOESM1_ESM.xlsx',
        'official_esm_bytes':207380,
      },
      'verified_esm_contract':{
        'MLL_duration':'IF(WL_t > MLL_prev, dt_prev+1, 0)',
        'MLL_update':'IF(WL_t <= MLL_prev, WL_t, WL_t-F_t*(WL_t-MLL_prev))',
        'MUL_duration':'IF(WL_t >= MUL_prev, 0, xt_prev+1)',
        'MUL_update':'IF(WL_t >= MUL_prev, WL_t, WL_t-K_t*(WL_t-MUL_prev))',
        'lower_cached_check':'dt=2,f=4,cmin=.01 -> F=0.90909090909090917',
        'upper_cached_check':'xt=4,s=15,wmin=.001 -> K=0.99468511166686502',
      },
      'annual_driver':'September mean water level, as in the published Lake Erie/Ontario applications',
      'parameterizations':[{'name':n,'f_yr':f,'s_yr':s,'source':'published; not fitted to Seoyeongari pond area'} for n,f,s in PARAMS],
      'cmin':C_MIN_DEFAULT,'wmin':W_MIN_DEFAULT,
      'site_specific_s_status':'UNRESOLVED: TLMM s is dewatering-to-closed-canopy woody takeover. The existing ~5.3 yr tree-ring lag cannot be equated to s unless the endpoint is shown to represent closed-canopy takeover.',
      'initialization':{
        'year':2011,'basis':'observed mapped 2011 pond footprint used as model initialization, not calibration',
        'MLL_equals_MUL_at_mapped_pond_edge_m':h0,
        'prehistory_assumed':False,
      },
      'area_mapping':{
        'domain':'mapped 2011 pond footprint only',
        'aquatic':'A(MLL)','marsh':'A(MUL)-A(MLL)','woody':'A0-A(MUL)',
        'hypsometry_extrapolated_to_5939_5_m2_transition_footprint':False,
      },
      'winter_fractional_exposure_accumulation':False,
      'stage78_beta_D_used':False,
      'pond_area_fit_used_to_select_tlmm_parameters':False,
      'eghm_hydrology_changed':False,
      'vegetation_et_feedback_added':False,
      'peat_feedback_added':False,
      'reference_depth_m':h0,
      'september_mean_water_levels_m':{str(y):sep_wl[y] for y in YEARS},
      'audits':audits,
      'states':compact,
      'physical_hydrology_closure':{
        'mass_error_m3':h['mass_error'],'area_partition_error_m2':h['area_partition_error'],
        'precip_partition_error_m3':h['precip_partition_error']},
    }
    (OUT/'stage79_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
