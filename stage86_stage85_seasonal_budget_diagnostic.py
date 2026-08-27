#!/usr/bin/env python3
"""Stage86 — flux-by-flux seasonal audit of the Stage85 Baseline trajectory.

This is diagnostic only. It changes no scientific parameter and verifies that
its daily storage/area path is numerically identical to Stage85 Baseline before
interpreting any flux decomposition.
"""
from __future__ import annotations

import json, math
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

import stage85_exact_tlmm_integrated as s85

OUT=Path('stage86_outputs'); OUT.mkdir(exist_ok=True)


def baseline_flux_audit(df: pd.DataFrame) -> pd.DataFrame:
    su=0.5*s85.C_UPLAND; sw=0.5*s85.C_WET
    fast=0.0; slow=0.0; surf=s85.V0
    prev=su+sw+fast+slow+surf
    rows=[]; maxerr=0.0
    for r in df.itertuples(index=False):
        dt=pd.Timestamp(r.DATE); pi=float(r.PRE); etoi=float(r.ETo); epi=float(r.E_P)
        ap=s85.area_v(surf); ah0=min(ap,s85.A0); aw=max(s85.A_WET-ap,0.0)
        pup=pi*s85.A_UPLAND/1000.0
        pwet=pi*aw/1000.0
        popen=pi*ap/1000.0

        su0=su; sw0=sw; fast0=fast; slow0=slow; surf0=surf

        su += pup
        e1=min(su,s85.ET_UPLAND*etoi*s85.A_UPLAND/1000.0); su-=e1
        dex=max(su-s85.C_UPLAND,0.0); su-=dex

        sw += pwet
        exposed=max(s85.A0-ah0,0.0)
        bg=max(aw-exposed,0.0)
        e2d=etoi*(s85.K_BG*bg+s85.K_BARE*exposed)/1000.0
        e2=min(sw,e2d); sw-=e2
        dw=max(sw-s85.C_WET,0.0); sw-=dw

        local=dex*s85.LOCAL_FRAC; deep=dex-local
        fast += local*s85.FAST_FRAC; slow += local*(1.0-s85.FAST_FRAC)
        qf=min(fast,fast/s85.TAU_FAST); qs=min(slow,slow/s85.TAU_SLOW_D)
        fast-=qf; slow-=qs; qr=qf+qs

        surf += popen+dw+qr
        aloss=s85.area_v(surf)
        eo_p=epi*aloss/1000.0; qo_p=surf/s85.TAU_SURF; qg_p=s85.K_GW_MM_D*aloss/1000.0
        lp=eo_p+qo_p+qg_p; fac=min(1.0,surf/lp) if lp>0 else 1.0
        eo=eo_p*fac; qo=qo_p*fac; qg=qg_p*fac
        surf -= eo+qo+qg
        if surf<0 and surf>-1e-12: surf=0.0

        total=su+sw+fast+slow+surf; inputs=pup+pwet+popen; outputs=e1+e2+eo+deep+qo+qg
        err=prev+inputs-outputs-total; maxerr=max(maxerr,abs(err)); prev=total

        rows.append({
          'DATE':dt,'YEAR':dt.year,'MONTH':dt.month,
          'PRE_mm':pi,'ETo_mm':etoi,'EP_mm':epi,
          'P_upland_m3':pup,'P_wetsoil_m3':pwet,'P_open_m3':popen,'P_total_m3':inputs,
          'ET_upland_m3':e1,'ET_wetland_m3':e2,'E_open_m3':eo,
          'upland_excess_m3':dex,'upland_local_recharge_m3':local,'deep_loss_m3':deep,
          'wetland_excess_to_pond_m3':dw,'return_fast_m3':qf,'return_slow_m3':qs,'return_total_m3':qr,
          'pond_outflow_m3':qo,'pond_groundwater_loss_m3':qg,
          'su_start_m3':su0,'sw_start_m3':sw0,'fast_start_m3':fast0,'slow_start_m3':slow0,'pond_start_m3':surf0,
          'su_end_m3':su,'sw_end_m3':sw,'fast_end_m3':fast,'slow_end_m3':slow,'pond_end_m3':surf,
          'pond_area_end_m2':s85.area_v(surf),'pond_depth_end_m':s85.depth_v(surf),
          'zero_surface':int(surf<=1e-9),'mass_error_m3':err,
        })
    out=pd.DataFrame(rows)
    out.attrs['max_mass_error_m3']=maxerr
    return out


def season(month:int)->str:
    if month in (10,11,12): return 'Oct-Dec'
    if month in (1,2): return 'Jan-Feb'
    if month in (3,4): return 'Mar-Apr'
    if month in (5,6): return 'May-Jun'
    return 'Jul-Sep'


def main():
    df=s85.forcing_frame()
    audit=baseline_flux_audit(df)
    ref,_,me=s85.simulate(df,False,False)
    da=np.max(np.abs(audit.pond_area_end_m2.to_numpy()-ref.hydraulic_area_m2.to_numpy()))
    dv=np.max(np.abs(audit.pond_end_m3.to_numpy()-ref.V_m3.to_numpy()))
    if da>1e-10 or dv>1e-10:
        raise AssertionError(f'baseline diagnostic drift: area={da}, V={dv}')

    audit['SEASON']=audit.MONTH.map(season)
    order=['Oct-Dec','Jan-Feb','Mar-Apr','May-Jun','Jul-Sep']
    metrics=[
      'P_total_m3','P_upland_m3','P_wetsoil_m3','P_open_m3',
      'ET_upland_m3','ET_wetland_m3','E_open_m3','deep_loss_m3',
      'wetland_excess_to_pond_m3','return_fast_m3','return_slow_m3','return_total_m3',
      'pond_outflow_m3','pond_groundwater_loss_m3'
    ]
    agg=audit.groupby(['YEAR','SEASON'],sort=False)[metrics].sum().reset_index()
    agg['SEASON']=pd.Categorical(agg.SEASON,categories=order,ordered=True)
    agg=agg.sort_values(['YEAR','SEASON'])

    state=audit.groupby(['YEAR','SEASON'],sort=False).agg(
      days=('DATE','size'),zero_surface_days=('zero_surface','sum'),
      mean_pond_area_m2=('pond_area_end_m2','mean'),min_pond_area_m2=('pond_area_end_m2','min'),max_pond_area_m2=('pond_area_end_m2','max'),
      start_pond_m3=('pond_start_m3','first'),end_pond_m3=('pond_end_m3','last'),
      start_upland_soil_m3=('su_start_m3','first'),end_upland_soil_m3=('su_end_m3','last'),
      start_wetland_soil_m3=('sw_start_m3','first'),end_wetland_soil_m3=('sw_end_m3','last'),
      start_fast_m3=('fast_start_m3','first'),end_fast_m3=('fast_end_m3','last'),
      start_slow_m3=('slow_start_m3','first'),end_slow_m3=('slow_end_m3','last'),
    ).reset_index()
    state['SEASON']=pd.Categorical(state.SEASON,categories=order,ordered=True); state=state.sort_values(['YEAR','SEASON'])
    seasonal=agg.merge(state,on=['YEAR','SEASON'])
    seasonal['pond_delta_m3']=seasonal.end_pond_m3-seasonal.start_pond_m3
    seasonal['soil_plus_return_store_delta_m3']=(
      (seasonal.end_upland_soil_m3+seasonal.end_wetland_soil_m3+seasonal.end_fast_m3+seasonal.end_slow_m3)
      -(seasonal.start_upland_soil_m3+seasonal.start_wetland_soil_m3+seasonal.start_fast_m3+seasonal.start_slow_m3)
    )
    seasonal.to_csv(OUT/'stage86_seasonal_flux_budget.csv',index=False)
    audit.to_csv(OUT/'stage86_daily_flux_budget.csv',index=False)

    focus=seasonal[(seasonal.YEAR.isin([2013,2015,2017,2019,2021,2023])) & (seasonal.SEASON.isin(['Oct-Dec','Jan-Feb','Mar-Apr','May-Jun']))].copy()
    focus.to_csv(OUT/'stage86_focus_years.csv',index=False)

    # Pre-observation hydrologic support: Oct-Dec of previous year + Jan-Apr current year.
    pre=[]
    for y in [2013,2015,2017,2019,2021,2023]:
        gprev=audit[(audit.YEAR==y-1)&(audit.MONTH.isin([10,11,12]))]
        gcur=audit[(audit.YEAR==y)&(audit.MONTH.isin([1,2,3,4]))]
        g=pd.concat([gprev,gcur])
        row={'YEAR':y}
        for m in metrics: row[m]=float(g[m].sum())
        row.update({
          'start_pond_m3':float(g.pond_start_m3.iloc[0]),'end_Apr_pond_m3':float(g.pond_end_m3.iloc[-1]),
          'end_Apr_area_m2':float(g.pond_area_end_m2.iloc[-1]),'zero_surface_days':int(g.zero_surface.sum()),
          'net_direct_pond_supply_m3':float((g.P_open_m3+g.wetland_excess_to_pond_m3+g.return_total_m3).sum()),
          'pond_direct_losses_m3':float((g.E_open_m3+g.pond_outflow_m3+g.pond_groundwater_loss_m3).sum()),
        })
        pre.append(row)
    pre=pd.DataFrame(pre); pre.to_csv(OUT/'stage86_pre_observation_support.csv',index=False)

    cols=['YEAR','start_pond_m3','end_Apr_pond_m3','end_Apr_area_m2','zero_surface_days','P_total_m3','wetland_excess_to_pond_m3','return_total_m3','deep_loss_m3','net_direct_pond_supply_m3','pond_direct_losses_m3']
    print(pre[cols].to_string(index=False))
    status={
      'status':'PASS_STAGE86_STAGE85_BASELINE_SEASONAL_AUDIT',
      'max_area_difference_vs_stage85_m2':float(da),'max_volume_difference_vs_stage85_m3':float(dv),
      'max_mass_error_m3':float(audit.attrs['max_mass_error_m3']),
      'parameters_changed':False,
    }
    (OUT/'stage86_audit.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    print(json.dumps(status,indent=2))

if __name__=='__main__': main()
