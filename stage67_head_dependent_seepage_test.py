#!/usr/bin/env python3
"""Stage67 — parameter-free head-dependent seepage structural diagnostic.

This is a controlled structural test, NOT a replacement of the accepted kernel.
The official model uses

    q_g* = k_gw A / 1000,

so the effective groundwater-loss flux in mm d-1 is independent of pond depth.
Stage66 showed that merely changing k_gw, tau_surf, or p_shape can make annual
zero-storage days look plausible while leaving long summer-autumn dry spells.

Here we test the same water balance with one physically motivated change only:

    q_g* = k_gw A / 1000 * (h / h0),

where h0 is the depth corresponding to V0 under the same Hayashi-type
hypsometry. Thus the selected k_gw=4 mm d-1 is preserved exactly at V=V0,
seepage tends continuously to zero as hydraulic head tends to zero, and NO new
coefficient is introduced. Above h0, the same gradient assumption permits a
larger flux. This is a diagnostic Darcy-style head scaling, not a claim that the
external groundwater head is measured at zero.

Hydroperiod observations (~71-73 open-water-disappearance days, concentrated
around March-April) are external plausibility diagnostics only. They are not
used as an objective, parameter-selection rule, or acceptance gate.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, Mapping, Sequence

import pandas as pd

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_geometry import area_v_deterministic, nth_root_ieee, root_degree_from_p
from eghm_deterministic_kernel import (
    A0, A_WET, A_UPLAND, A_DOMAIN, C_UPLAND, C_WET, ET_UPLAND,
    FAST_FRAC, TAU_SLOW_D, EVAL_YEARS, OBS_MONTHS, SELECTED_STRUCTURE,
    annual_support, build_features, continuous_exposure_state, hydrologic_feature,
)
from eghm_deterministic_scenarios import fit_four_scenarios, peat_geomorphic_loss

OUT = Path('stage67_outputs')
OUT.mkdir(exist_ok=True)
P = dict(SELECTED_STRUCTURE)
PEAT_RATE = 0.38
ZERO_EPS_M3 = 1e-9
OBS = {
    2013: 2154.430, 2015: 2147.678, 2017: 2051.218,
    2019: 2045.159, 2021: 1965.256, 2023: 1882.700,
}
Y = [float(OBS[y]) for y in EVAL_YEARS]


def depth_ratio(v: float, V0: float, p_shape: float) -> float:
    """Return h/h0 from the same power-law geometry using deterministic roots."""
    v=float(v); V0=float(V0); p=float(p_shape)
    if v <= 0.0:
        return 0.0
    n=root_degree_from_p(p)
    r=nth_root_ieee(v/V0,n)  # r=(V/V0)^(2/(p+2)) = A/A0 before cap
    # h/h0 = r^(p/2); p/2 is integer for accepted p={6,12,18}.
    k=int(p/2.0)
    out=1.0
    for _ in range(k):
        out=out*r
    return out


def hydro_head_scaled(forcing: Mapping[str,Sequence[float]], p: Mapping[str,float]) -> Dict[str,object]:
    """Official daily recurrence with only qg* multiplied by deterministic h/h0."""
    pre=[float(x) for x in forcing['pre']]
    eto=[float(x) for x in forcing['eto']]
    ep=[float(x) for x in forcing['ep']]
    dates=pd.to_datetime(forcing['date'])
    n=len(pre)
    hp={k:float(p[k]) for k in ('V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d')}

    su=float(.5*C_UPLAND); sw=float(.5*C_WET); fast=0.0; slow=0.0; surf=hp['V0']
    prev=su+sw+fast+slow+surf
    area=[0.0]*n; volume=[0.0]*n; qret=[0.0]*n; qgw=[0.0]*n; qout=[0.0]*n; qev=[0.0]*n
    headratio=[0.0]*n
    max_mass=max_area=max_precip=0.0

    def av(v):
        return area_v_deterministic(v,hp['V0'],hp['p_shape'],A0=A0,A_WET=A_WET)

    for i in range(n):
        pi=pre[i]; etoi=eto[i]; epi=ep[i]
        ap=av(surf); aw=max(A_WET-ap,0.0)
        pup=pi*A_UPLAND/1000.0; pwet=pi*aw/1000.0; popen=pi*ap/1000.0
        max_area=max(max_area,abs((A_UPLAND+aw+ap)-A_DOMAIN))
        max_precip=max(max_precip,abs((pup+pwet+popen)-pi*A_DOMAIN/1000.0))

        su=su+pup
        e1=min(su,ET_UPLAND*etoi*A_UPLAND/1000.0); su=su-e1
        dex=max(su-C_UPLAND,0.0); su=su-dex

        sw=sw+pwet
        e2=min(sw,etoi*aw/1000.0); sw=sw-e2
        dw=max(sw-C_WET,0.0); sw=sw-dw

        local=dex*hp['local_frac']; deep=dex-local
        fast=fast+local*FAST_FRAC; slow=slow+local*(1.0-FAST_FRAC)
        qf=min(fast,fast/hp['tau_fast']); qs=min(slow,slow/TAU_SLOW_D)
        fast=fast-qf; slow=slow-qs; qr=qf+qs
        surf=surf+popen+dw+qr

        # Same concurrent-loss architecture; only groundwater potential is head-scaled.
        aloss=av(surf)
        hr=depth_ratio(surf,hp['V0'],hp['p_shape'])
        eo_p=epi*aloss/1000.0
        qo_p=surf/hp['tau_surf']
        qg_p=hp['k_gw_mm_d']*aloss/1000.0*hr
        loss_p=eo_p+qo_p+qg_p
        fac=min(1.0,surf/loss_p) if loss_p>0.0 else 1.0
        eo=eo_p*fac; qo=qo_p*fac; qg=qg_p*fac
        surf=surf-(eo+qo+qg)
        if surf<0.0 and surf>-1e-12: surf=0.0

        an=av(surf)
        total=su+sw+fast+slow+surf
        inputs=pup+pwet+popen; outputs=e1+e2+eo+deep+qo+qg
        err=prev+inputs-outputs-total
        max_mass=max(max_mass,abs(err)); prev=total

        area[i]=an; volume[i]=surf; qret[i]=qr; qgw[i]=qg; qout[i]=qo; qev[i]=eo; headratio[i]=hr

    return {
        'dates':dates,'area':area,'V':volume,'return_flow':qret,
        'groundwater_loss':qgw,'surface_outflow':qout,'surface_evaporation':qev,
        'preloss_head_ratio_h_over_h0':headratio,
        'mass_error':max_mass,'area_partition_error':max_area,'precip_partition_error':max_precip,
    }


def features_for_hydro(h,p):
    eco=continuous_exposure_state(h['area'],float(p['r_est_yr']),int(p['est_window_d']))
    S=annual_support(h['dates'],eco['state'],years=EVAL_YEARS,months=OBS_MONTHS)
    H=hydrologic_feature(h['dates'],h['return_flow'],int(p['hydro_window_d']),years=EVAL_YEARS,months=OBS_MONTHS)
    return eco,S,H


def dry_summary(h):
    dt=pd.to_datetime(h['dates']); z=[float(v)<=ZERO_EPS_M3 for v in h['V']]
    yy=[int(d.year) for d in dt]; mm=[int(d.month) for d in dt]
    annual=[]; spells=[]
    for y in range(2011,2024):
        idx=[i for i in range(len(dt)) if yy[i]==y]
        zy=[z[i] for i in idx]
        rr=[]; s=None
        for j,q in enumerate(zy):
            if q and s is None: s=j
            if s is not None and ((not q) or j==len(zy)-1):
                e=j if (q and j==len(zy)-1) else j-1; rr.append((s,e)); s=None
        az=sum(zy); spring=sum(1 for i in idx if z[i] and mm[i] in (3,4))
        annual.append({'year':y,'zero_days':az,'mar_apr_zero_days':spring,
                       'longest_zero_run_days':max((e-s+1 for s,e in rr),default=0)})
        for s,e in rr:
            gs=idx[s]; ge=idx[e]
            spells.append({'year':y,'start':str(dt[gs].date()),'end':str(dt[ge].date()),'days':e-s+1,
                           'overlaps_mar_apr':any(mm[idx[j]] in (3,4) for j in range(s,e+1))})
    monthly=[]
    for m in range(1,13):
        q=sum(1 for i in range(len(z)) if z[i] and mm[i]==m)
        monthly.append({'month':m,'zero_days_2011_2023':q,'mean_per_year':q/13.0})
    total=sum(r['zero_days'] for r in annual); spring=sum(r['mar_apr_zero_days'] for r in annual)
    return annual,monthly,spells,{
        'total_zero_days':total,'mean_zero_days_per_year':total/13.0,
        'mar_apr_zero_days':spring,'spring_share':spring/total if total else None,
        'outside_mar_apr_share':(total-spring)/total if total else None,
        'max_longest_zero_run_days':max(r['longest_zero_run_days'] for r in annual),
        'top_dry_months':sorted(monthly,key=lambda r:(-r['zero_days_2011_2023'],r['month']))[:5],
        'longest_spells':sorted(spells,key=lambda r:(-r['days'],r['start']))[:8],
    }


def scenario_result(h,p):
    eco,S,H=features_for_hydro(h,p)
    Gd,h0,B=peat_geomorphic_loss(h['dates'],h['V'],PEAT_RATE,p['V0'],p['p_shape'])
    G=annual_support(h['dates'],Gd,years=EVAL_YEARS,months=OBS_MONTHS)
    rows=fit_four_scenarios(S,H,G,Y,a0=A0)
    return S,H,G,rows


def compact_scenarios(rows):
    ranked=sorted(rows,key=lambda r:r['nRMSE_pct'])
    return [{
        'rank':i+1,'Scenario':r['Scenario'],'RMSE_m2':float(r['RMSE_m2']),
        'nRMSE_pct':float(r['nRMSE_pct']),'K_colonizable_m2':float(r['K_colonizable_m2']),
        'K_hydro_m2_per_m3':float(r['K_hydro_m2_per_m3']),
    } for i,r in enumerate(ranked)]


def totals(h):
    return {
        'surface_evap_m3':math.fsum(float(x) for x in h['surface_evaporation']),
        'surface_outflow_m3':math.fsum(float(x) for x in h['surface_outflow']),
        'groundwater_loss_m3':math.fsum(float(x) for x in h['groundwater_loss']),
        'return_flow_m3':math.fsum(float(x) for x in h['return_flow']),
    }


def main():
    forcing,missing,annual_precip,_=deterministic_forcing()
    official=build_features(forcing,P); ho=official['hydro']
    hs=hydro_head_scaled(forcing,P)

    ao,mo,spo,dso=dry_summary(ho); ah,mh,sph,dsh=dry_summary(hs)
    So,Ho,Go,sco=scenario_result(ho,P); Ss,Hs,Gs,scs=scenario_result(hs,P)

    pd.DataFrame([{'case':'official_head_independent',**r} for r in ao]+[{'case':'head_scaled',**r} for r in ah]).to_csv(OUT/'stage67_annual_hydroperiod.csv',index=False)
    pd.DataFrame([{'case':'official_head_independent',**r} for r in mo]+[{'case':'head_scaled',**r} for r in mh]).to_csv(OUT/'stage67_monthly_hydroperiod.csv',index=False)
    pd.DataFrame([{'case':'official_head_independent',**r} for r in spo]+[{'case':'head_scaled',**r} for r in sph]).to_csv(OUT/'stage67_dry_spells.csv',index=False)
    pd.DataFrame([{'case':'official_head_independent',**r} for r in compact_scenarios(sco)]+[{'case':'head_scaled',**r} for r in compact_scenarios(scs)]).to_csv(OUT/'stage67_four_scenario_metrics.csv',index=False)
    pd.DataFrame({'date':pd.to_datetime(hs['dates']),'V_m3':hs['V'],'area_m2':hs['area'],'h_over_h0_preloss':hs['preloss_head_ratio_h_over_h0'],'qgw_m3':hs['groundwater_loss'],'qout_m3':hs['surface_outflow'],'qevap_m3':hs['surface_evaporation'],'return_flow_m3':hs['return_flow']}).to_csv(OUT/'stage67_head_scaled_daily.csv',index=False)

    closure_off={'mass_error_m3':float(ho['mass_error']),'area_error_m2':float(ho['area_partition_error']),'precip_error_m3':float(ho['precip_partition_error'])}
    closure_new={'mass_error_m3':float(hs['mass_error']),'area_error_m2':float(hs['area_partition_error']),'precip_error_m3':float(hs['precip_partition_error'])}
    if max(closure_off.values())>1e-8 or max(closure_new.values())>1e-8:
        raise SystemExit('Stage67 closure failed')

    result={
        'status':'PASS_STAGE67_HEAD_DEPENDENT_SEEPAGE_STRUCTURAL_TEST',
        'official_kernel_modified':False,
        'new_fitted_parameter_added':False,
        'hydroperiod_used_for_calibration':False,
        'structural_change':'qg = k_gw*A/1000 -> qg = k_gw*A/1000*(h/h0); k_gw unchanged and identical flux at V=V0',
        'diagnostic_assumption':'external reference head represented by wetland-floor datum solely for structural test; not site-measured',
        'independent_hydroperiod_context':{'open_water_disappearance_days_per_year':[71,73],'drying_expected':'March-April concentrated'},
        'official':{'dryness':dso,'water_flux_totals_2011_2023':totals(ho),'scenarios_peat_0p38':compact_scenarios(sco)},
        'head_scaled':{'dryness':dsh,'water_flux_totals_2011_2023':totals(hs),'scenarios_peat_0p38':compact_scenarios(scs)},
        'differences':{
            'mean_zero_days_per_year':float(dsh['mean_zero_days_per_year']-dso['mean_zero_days_per_year']),
            'spring_share':float((dsh['spring_share'] or 0)-(dso['spring_share'] or 0)),
            'max_longest_zero_run_days':int(dsh['max_longest_zero_run_days']-dso['max_longest_zero_run_days']),
            'Integrated_nRMSE_pct':float(next(r for r in scs if r['Scenario']=='Integrated Model')['nRMSE_pct']-next(r for r in sco if r['Scenario']=='Integrated Model')['nRMSE_pct']),
        },
        'official_closure':closure_off,'head_scaled_closure':closure_new,
        'forcing_missing_before_fill':missing,'annual_precip_mm':annual_precip,
        'decision_rule':'Do not adopt because annual dry-day count improves alone. Only consider this structure further if it also reduces long out-of-season dry spells and improves March-April concentration without destroying mapped-area fit or conservation.',
    }
    (OUT/'stage67_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
