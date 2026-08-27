#!/usr/bin/env python3
"""Stage75 — couple cumulative terrestrialization exposure to evapotranspiration.

Scientific purpose
------------------
Stage74 showed that cumulative exposure dose D(t) is a simpler and more accurate
replacement for the legacy ecological state S. This stage closes the ecological
feedback loop without adding an arbitrary unitless correction constant.

Daily terrestrialized area is represented as
    A_terr(t) = min(beta_D * D(t), A_nonopen(t))
where D is cumulative fractional exposure in exposure-years and beta_D has units
m2 per exposure-year. The non-open wetland ET demand is then area-weighted:
    ET_nonopen = ETo * [A_wet + R_ET * A_terr]
with R_ET fixed to literature-bounded values.

R_ET is NOT freely optimized. Tested values are anchored by forest-wetland flux
comparisons:
- 1.00 no-feedback control
- 1.15 conservative lower sensitivity
- 1.28 Shveytser et al. 2024: 312/244 mm during Jul-Oct
- 1.33 forest/peatland annual comparison: 910/682 mm
- 1.40 upper stress value

For each fixed R_ET, only beta_D and the short-term hydrologic observation scale
Kh are calibrated against the six mapped open-water observations. beta_D is the
same coefficient that produces physical terrestrialized area and therefore also
controls the ET feedback; there is no separate Kc.

2022 pond-area observation remains absent. Scenario rank and accuracy are outputs,
not workflow acceptance gates.
"""
from __future__ import annotations

import json
from pathlib import Path
from decimal import Decimal, localcontext

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_geometry import area_v_deterministic
from eghm_deterministic_kernel import (
    A0,A_WET,A_UPLAND,A_DOMAIN,C_UPLAND,C_WET,ET_UPLAND,FAST_FRAC,TAU_SLOW_D,
    SELECTED_STRUCTURE,EVAL_YEARS,OBS_MONTHS,annual_support,hydrologic_feature,mean_fsum
)
from eghm_deterministic_scenarios import peat_geomorphic_loss, metrics_fixed, fit_one_nonnegative_fixed

OUT=Path('stage75_outputs'); OUT.mkdir(exist_ok=True)
OBS={2013:2154.430,2015:2147.678,2017:2051.218,2019:2045.159,2021:1965.256,2023:1882.700}
Y=[OBS[y] for y in EVAL_YEARS]
PEAT_RATE=0.38
ET_RATIOS=[1.00,1.15,1.28,1.33,1.40]
BETA_GRID=[float(x) for x in range(40,121,2)]


def hydro_coupled(forcing,p,beta,et_ratio):
    pre=[float(x) for x in forcing['pre']]; eto=[float(x) for x in forcing['eto']]; ep=[float(x) for x in forcing['ep']]
    dates=forcing['date']; n=len(pre)
    V0=float(p['V0']); shape=float(p['p_shape']); tau_s=float(p['tau_surf']); lf=float(p['local_frac']); tau_f=float(p['tau_fast']); kg=float(p['k_gw_mm_d'])
    su=0.5*C_UPLAND; sw=0.5*C_WET; fast=0.0; slow=0.0; surf=V0
    prev=su+sw+fast+slow+surf
    area=[]; vol=[]; ret=[]; terr=[]; dose=[]
    max_mass=max_area=max_precip=0.0
    D=0.0
    def av(v): return area_v_deterministic(v,V0,shape,A0=A0,A_WET=A_WET)
    for i in range(n):
        pi=pre[i]; etoi=eto[i]; epi=ep[i]
        ap=av(surf); aw=max(A_WET-ap,0.0)
        exposed=max(min((A0-ap)/A0,1.0),0.0)
        D += exposed/365.0
        at=min(max(float(beta)*D,0.0),aw)
        awet=max(aw-at,0.0)
        pup=pi*A_UPLAND/1000.0; pwet=pi*aw/1000.0; popen=pi*ap/1000.0
        max_area=max(max_area,abs((A_UPLAND+aw+ap)-A_DOMAIN))
        max_precip=max(max_precip,abs((pup+pwet+popen)-pi*A_DOMAIN/1000.0))
        su += pup
        e1=min(su,ET_UPLAND*etoi*A_UPLAND/1000.0); su-=e1
        dex=max(su-C_UPLAND,0.0); su-=dex
        sw += pwet
        # literature-bounded terrestrialization feedback: same reservoir, area-weighted ET demand
        e2_p=etoi*(awet + float(et_ratio)*at)/1000.0
        e2=min(sw,e2_p); sw-=e2
        dw=max(sw-C_WET,0.0); sw-=dw
        local=dex*lf; deep=dex-local
        fast += local*FAST_FRAC; slow += local*(1.0-FAST_FRAC)
        qf=min(fast,fast/tau_f); qs=min(slow,slow/TAU_SLOW_D)
        fast-=qf; slow-=qs; qr=qf+qs
        surf += popen+dw+qr
        aloss=av(surf)
        eo_p=epi*aloss/1000.0; qo_p=surf/tau_s; qg_p=kg*aloss/1000.0
        lp=eo_p+qo_p+qg_p; fac=min(1.0,surf/lp) if lp>0 else 1.0
        eo=eo_p*fac; qo=qo_p*fac; qg=qg_p*fac; surf-=eo+qo+qg
        if surf<0 and surf>-1e-12: surf=0.0
        an=av(surf)
        total=su+sw+fast+slow+surf; inputs=pup+pwet+popen; outputs=e1+e2+eo+deep+qo+qg
        err=prev+inputs-outputs-total; max_mass=max(max_mass,abs(err)); prev=total
        area.append(an); vol.append(surf); ret.append(qr); terr.append(at); dose.append(D)
    return {'dates':dates,'area':area,'V':vol,'return_flow':ret,'A_terr':terr,'D':dose,
            'mass_error':max_mass,'area_partition_error':max_area,'precip_partition_error':max_precip}


def fit_for_fixed_beta(F,p,beta,ratio):
    h=hydro_coupled(F,p,beta,ratio)
    H=hydrologic_feature(h['dates'],h['return_flow'],int(p['hydro_window_d']),years=EVAL_YEARS,months=OBS_MONTHS)
    Aterr=annual_support(h['dates'],h['A_terr'],years=EVAL_YEARS,months=OBS_MONTHS)
    Gd,_,_=peat_geomorphic_loss(h['dates'],h['V'],PEAT_RATE,p['V0'],p['p_shape'])
    G=annual_support(h['dates'],Gd,years=EVAL_YEARS,months=OBS_MONTHS)
    offset=[A0-Aterr[i]-G[i] for i in range(len(Y))]
    kh=fit_one_nonnegative_fixed(H,[Y[i]-offset[i] for i in range(len(Y))])
    pred=[offset[i]+kh*H[i] for i in range(len(Y))]
    met=metrics_fixed(pred,Y)
    return h,H,Aterr,G,kh,pred,met


def loocv_fixed_ratio(F,p,ratio):
    errs=[]; choices=[]
    for hold in range(len(Y)):
        best=None
        for beta in BETA_GRID:
            h,H,Aterr,G,kh,pred,met=fit_for_fixed_beta(F,p,beta,ratio)
            train=[i for i in range(len(Y)) if i!=hold]
            off=[A0-Aterr[i]-G[i] for i in train]; Htr=[H[i] for i in train]; ytr=[Y[i] for i in train]
            khtr=fit_one_nonnegative_fixed(Htr,[ytr[j]-off[j] for j in range(len(train))])
            ptr=[off[j]+khtr*Htr[j] for j in range(len(train))]
            mtr=metrics_fixed(ptr,ytr)
            key=(mtr['RMSE_m2'],beta)
            if best is None or key<best[0]: best=(key,beta,h,H,Aterr,G,khtr)
        _,beta,h,H,Aterr,G,khtr=best
        ph=A0-Aterr[hold]-G[hold]+khtr*H[hold]
        errs.append(ph-Y[hold]); choices.append({'held_out_year':EVAL_YEARS[hold],'beta_D':beta})
    with localcontext() as ctx:
        ctx.prec=80
        vals=[Decimal(str(e)) for e in errs]; rm=(sum((e*e for e in vals),Decimal(0))/Decimal(len(vals))).sqrt()
        mean=sum((Decimal(str(v)) for v in Y),Decimal(0))/Decimal(len(Y))
        return float(rm),float(Decimal(100)*rm/mean),choices


def main():
    F,_,_,_=deterministic_forcing(); P=dict(SELECTED_STRUCTURE)
    rows=[]; best_by_ratio={}
    for ratio in ET_RATIOS:
        candidates=[]
        for beta in BETA_GRID:
            h,H,Aterr,G,kh,pred,met=fit_for_fixed_beta(F,P,beta,ratio)
            row={'ET_ratio':ratio,'beta_D_m2_per_exposure_yr':beta,'K_hydro_m2_per_m3':kh,**met,
                 'Aterr_2023_m2':Aterr[-1],'D_2023_exposure_yr':annual_support(h['dates'],h['D'])[-1],
                 'mass_error_m3':h['mass_error'],'area_partition_error_m2':h['area_partition_error'],'precip_partition_error_m3':h['precip_partition_error'],
                 **{f'pred_{y}':pred[i] for i,y in enumerate(EVAL_YEARS)}}
            rows.append(row); candidates.append(row)
        best=min(candidates,key=lambda z:(z['RMSE_m2'],z['beta_D_m2_per_exposure_yr']))
        lrm,lnr,choices=loocv_fixed_ratio(F,P,ratio)
        best_by_ratio[str(ratio)]={**best,'LOOCV_RMSE_m2':lrm,'LOOCV_nRMSE_pct':lnr,'LOOCV_choices':choices}
    best_overall=min((v for v in best_by_ratio.values()),key=lambda z:(z['RMSE_m2'],z['ET_ratio']))
    import csv
    with (OUT/'stage75_all.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    summary={'status':'PASS_STAGE75_COUPLED_ET_FEEDBACK_SEARCH','pond_area_observation_2022':'ABSENT','observation_support':'April-May',
             'peat_rate_mm_yr':PEAT_RATE,'ET_ratio_values':ET_RATIOS,
             'ET_ratio_role':'literature-bounded fixed sensitivity values; not freely optimized continuous parameter',
             'beta_role':'site-calibrated terrestrialization area gain, m2 per cumulative exposure-year; same area drives ET feedback and mapped-area loss',
             'best_by_ratio':best_by_ratio,'best_overall':best_overall,
             'references':[{'citation':'Shveytser et al. 2024','doi':'10.1029/2022WR033757','forest_mm':312,'wetland_mm':244,'ratio':312/244},
                           {'citation':'temperate rainforest vs peatland flux comparison 2024','forest_mm_yr':910,'peatland_mm_yr':682,'ratio':910/682}],
             'selection_is_acceptance_gate':False}
    (OUT/'stage75_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
