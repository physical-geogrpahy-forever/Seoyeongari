#!/usr/bin/env python3
"""Stage79 — apply the published TLMM process to the accepted EGHM hydrology.

This stage is deliberately a process diagnostic before ET/peat coupling. It
replaces the Stage78 cumulative-exposure ecology with Keddy & Campbell's TLMM
rules, but does not yet alter the conserved daily hydrologic kernel.

TLMM is driven exactly as in the published Great Lakes examples by one annual
growing-season water-level statistic: September mean water level. The spatial
integration is performed exactly over the existing EGHM power-law hypsometry
inside the mapped 2011 pond footprint A0; interval edges are the annual water
levels themselves, so no arbitrary raster/band width is introduced.

No pond-area observations are used to select f, s, cmin or wmin. Two published
parameterizations are reported: general temperate f=4,s=30 and the published
Great Lakes example f=4,s=15. The site-specific s remains unresolved until the
TLMM-prescribed dendrochronology/historic-aerial ground-truthing can map the
Seoyeongari evidence to time-to-closed-canopy (not merely first-tree arrival).
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_geometry import area_h_deterministic, depth_v_deterministic, reference_depth
from eghm_deterministic_kernel import A0, SELECTED_STRUCTURE, hydro, mean_fsum
from tlmm_core import (
    C_MIN_DEFAULT,W_MIN_DEFAULT,F_TEMPERATE_YR,S_TEMPERATE_YR,S_GREAT_LAKES_EXAMPLE_YR,
    band_history,assert_partition,
)

OUT=Path('stage79_outputs');OUT.mkdir(exist_ok=True)
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


def exact_hypsometric_intervals(water_levels: Sequence[float], h0: float, p_shape: float) -> List[Tuple[float,float,float,float]]:
    """Return (zlo,zhi,zmid,planform_area) using WL values as exact breakpoints."""
    edges={0.0,float(h0)}
    for w in water_levels:
        edges.add(min(max(float(w),0.0),float(h0)))
    e=sorted(edges); out=[]
    for lo,hi in zip(e[:-1],e[1:]):
        if hi-lo <= 1e-15: continue
        mid=0.5*(lo+hi)
        alo=area_h_deterministic(lo,h0,p_shape,A0=A0,A_WET=A0)
        ahi=area_h_deterministic(hi,h0,p_shape,A0=A0,A_WET=A0)
        a=max(ahi-alo,0.0)
        if a>1e-12: out.append((lo,hi,mid,a))
    return out


def run_one(name: str, f_yr: float, s_yr: float, sep_wl: Dict[int,float], h0: float, p_shape: float):
    wls=[sep_wl[y] for y in YEARS]
    bands=exact_hypsometric_intervals(wls,h0,p_shape)
    agg={y:{'aquatic':0.0,'marsh':0.0,'woody':0.0,'flooded_planform':0.0,'dewatered_planform':0.0} for y in YEARS}
    band_rows=[]
    for lo,hi,mid,a in bands:
        hist=band_history(YEARS,wls,mid,f_yr=f_yr,s_yr=s_yr,
                          cmin=C_MIN_DEFAULT,wmin=W_MIN_DEFAULT,initially_open_water=True)
        assert_partition(hist)
        for r in hist:
            q=agg[r.year]
            q['aquatic'] += a*r.aquatic_fraction
            q['marsh'] += a*r.marsh_fraction
            q['woody'] += a*r.woody_fraction
            q['flooded_planform'] += a if r.flooded else 0.0
            q['dewatered_planform'] += 0.0 if r.flooded else a
            band_rows.append({'parameterization':name,'f_yr':f_yr,'s_yr':s_yr,'year':r.year,
                              'z_lo_m':lo,'z_hi_m':hi,'z_mid_m':mid,'band_area_m2':a,
                              'flooded':int(r.flooded),'dt_flood_yr':r.dt_flood_yr,'xt_dewater_yr':r.xt_dewater_yr,
                              'marsh_fraction':r.marsh_fraction,'aquatic_fraction':r.aquatic_fraction,'woody_fraction':r.woody_fraction})
    annual=[]
    max_partition=0.0; max_hydraulic=0.0
    for y in YEARS:
        q=agg[y]; total=q['aquatic']+q['marsh']+q['woody']
        max_partition=max(max_partition,abs(total-A0))
        hydraulic_sep=area_h_deterministic(min(max(sep_wl[y],0.0),h0),h0,p_shape,A0=A0,A_WET=A0)
        max_hydraulic=max(max_hydraulic,abs((q['flooded_planform'])-hydraulic_sep))
        annual.append({'parameterization':name,'f_yr':f_yr,'s_yr':s_yr,'year':y,
                       'september_mean_water_level_m':sep_wl[y],
                       'hydraulic_flooded_planform_m2':q['flooded_planform'],
                       'hydraulic_dewatered_planform_m2':q['dewatered_planform'],
                       'tlmm_aquatic_m2':q['aquatic'],'tlmm_marsh_m2':q['marsh'],'tlmm_woody_m2':q['woody'],
                       'cover_partition_m2':total})
    return annual,band_rows,{'max_cover_partition_error_m2':max_partition,'max_hydraulic_band_integration_error_m2':max_hydraulic,'n_exact_hypsometric_intervals':len(bands)}


def main():
    F,_,_,_=deterministic_forcing(); P=dict(SELECTED_STRUCTURE); h=hydro(F,P)
    p=float(P['p_shape']); v0=float(P['V0']); h0=reference_depth(v0,p,A0=A0)
    depths=[depth_v_deterministic(v,v0,p,A0=A0) for v in h['V']]
    sep_wl=annual_month_mean(h['dates'],depths,9)

    annual_all=[]; bands_all=[]; audits={}
    for name,f,s in PARAMS:
        annual,bands,audit=run_one(name,f,s,sep_wl,h0,p)
        annual_all.extend(annual);bands_all.extend(bands);audits[name]=audit

    with (OUT/'stage79_tlmm_annual_states.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(annual_all[0].keys()));w.writeheader();w.writerows(annual_all)
    with (OUT/'stage79_tlmm_exact_band_states.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(bands_all[0].keys()));w.writeheader();w.writerows(bands_all)

    result={
      'status':'PASS_STAGE79_PUBLISHED_TLMM_PROCESS_DIAGNOSTIC',
      'model_source':{'citation':'Keddy PA, Campbell D (2020) Wetlands 40:667-680','doi':'10.1007/s13157-019-01229-9'},
      'tlmm_process':{
        'annual_driver':'September mean water level, matching the published Lake Erie/Ontario examples',
        'newly_exposed_to_marsh':'one growing season of dewatering/drawdown',
        'lower_limit':'published exponential flooding decline with f and cmin',
        'upper_limit':'published exponential woody-encroachment decline with s and wmin',
        'cmin':C_MIN_DEFAULT,'wmin':W_MIN_DEFAULT,
        'winter_fractional_exposure_accumulation':False,
      },
      'parameterizations':[{'name':n,'f_yr':f,'s_yr':s,'parameter_source':'published, not fitted to Seoyeongari pond area'} for n,f,s in PARAMS],
      'site_specific_s_status':'UNRESOLVED: TLMM s is time from dewatering to closed-canopy woody vegetation. Existing ~5.3 yr tree-ring evidence cannot be inserted as s until its ecological endpoint is shown to match closed-canopy takeover.',
      'spatial_domain':'mapped 2011 pond footprint only (A0); no extrapolation of the EGHM hypsometry into the 5939.5 m2 wetland/transition footprint',
      'spatial_integration':'exact intervals defined by annual September water levels; no arbitrary elevation-band width',
      'initial_condition':'2011 mapped pond footprint initialized as open water; newly dewatered portions thereafter follow the published one-growing-season marsh establishment rule',
      'eghm_hydrology_changed':False,
      'vegetation_et_feedback_added':False,
      'peat_feedback_added':False,
      'stage78_beta_D_used':False,
      'pond_area_fit_used_to_select_tlmm_parameters':False,
      'reference_depth_m':h0,
      'september_mean_water_levels_m':{str(y):sep_wl[y] for y in YEARS},
      'audits':audits,
      'physical_hydrology_closure':{'mass_error_m3':h['mass_error'],'area_partition_error_m2':h['area_partition_error'],'precip_partition_error_m3':h['precip_partition_error']},
    }
    (OUT/'stage79_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
