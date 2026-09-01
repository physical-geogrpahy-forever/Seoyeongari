#!/usr/bin/env python3
"""Stage75 — close the ecology -> ET -> hydrology feedback using cumulative exposure.

Scientific purpose
------------------
Stage74 found that a parameter-free cumulative hydrologic exposure dose D(t),
converted directly to persistent terrestrialized area A_terr = beta_D * D,
was more parsimonious and more accurate than the legacy abstract establishment
state S. Stage75 asks whether that terrestrialized area should alter vegetation
ET and feed back into the conserved daily water balance.

The ET formulation is reference bounded rather than direction-forced. The 2024
review by Pereira, Paredes & Espirito-Santo (Irrigation Science,
DOI 10.1007/s00271-024-00923-9) reports FAO-PM grass-reference crop
coefficients around 1 for many wetland grasses/meadows, emergent wetland plants
commonly around 1.10-1.20, woody deciduous/shrub values around 0.75/0.85 in one
humid European case, and values up to 1.23 for well-watered Populus. Therefore
we test literature anchor K_terr values on BOTH sides of the current wetland
K_wet=1.0 rather than assuming that terrestrialization must raise ET.

No new dimensionless fit coefficient is introduced. beta_D has physical units
m2 per exposure-year and directly maps cumulative exposure to terrestrialized
area. K_terr is selected only from literature anchor values. Peat remains the
field-derived 0.38 mm/yr central estimate. 2022 pond-area observation is absent.

This stage is diagnostic. Accuracy ranking is output, not a CI acceptance gate.
"""
from __future__ import annotations

import csv, json, math
from pathlib import Path
from typing import Dict, List, Mapping, Sequence

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_geometry import area_v_deterministic
from eghm_deterministic_kernel import (
    A0,A_WET,A_UPLAND,A_DOMAIN,C_UPLAND,C_WET,ET_UPLAND,FAST_FRAC,TAU_SLOW_D,
    EVAL_YEARS,OBS_MONTHS,SELECTED_STRUCTURE,annual_support,hydrologic_feature,
    mean_fsum,
)
from eghm_deterministic_scenarios import (
    fit_one_nonnegative_fixed,metrics_fixed,peat_geomorphic_loss,predict_fixed,
)

OUT=Path('stage75_outputs');OUT.mkdir(exist_ok=True)
OBS={2013:2154.430,2015:2147.678,2017:2051.218,2019:2045.159,2021:1965.256,2023:1882.700}
Y=[OBS[y] for y in EVAL_YEARS]
PEAT=0.38
KWET=1.0
KTERR_ANCHORS=[0.75,0.85,1.00,1.18,1.23]
# Broad site-specific beta search around the Stage74 no-feedback estimate (77.67).
# Coarse coverage is deliberately wide; final local refinement is 1 m2/exposure-yr.
BETA_COARSE=[float(x) for x in range(0,301,10)]


def hydro_feedback(forcing:Mapping[str,Sequence[float]],p:Mapping[str,float],beta:float,kterr:float)->Dict[str,object]:
    pre=[float(x) for x in forcing['pre']];eto=[float(x) for x in forcing['eto']];ep=[float(x) for x in forcing['ep']]
    import pandas as pd
    dates=pd.to_datetime(forcing['date']);n=len(pre)
    hp={k:float(p[k]) for k in ('V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d')}
    su=0.5*C_UPLAND;sw=0.5*C_WET;fast=0.0;slow=0.0;surf=hp['V0'];prev=su+sw+surf
    area=[0.0]*n;V=[0.0]*n;qret=[0.0]*n;aterr=[0.0]*n;dose=[0.0]*n;wet_et=[0.0]*n
    dacc=0.0;aterr_persistent=0.0
    max_mass=max_area=max_precip=0.0
    def av(v):return area_v_deterministic(v,hp['V0'],hp['p_shape'],A0=A0,A_WET=A_WET)
    for i in range(n):
        pi=pre[i];etoi=eto[i];epi=ep[i]
        ap=av(surf);aw=max(A_WET-ap,0.0)
        # Persistent terrestrialized area is a subset of the non-open wetland
        # footprint for ET partitioning on that day. If temporarily inundated,
        # the excess persistent area does not double-count the open-water area.
        ater_eff=min(max(aterr_persistent,0.0),aw,A0)
        awet=max(aw-ater_eff,0.0)
        pup=pi*A_UPLAND/1000.0;pwet=pi*aw/1000.0;popen=pi*ap/1000.0
        max_area=max(max_area,abs((A_UPLAND+aw+ap)-A_DOMAIN))
        max_precip=max(max_precip,abs((pup+pwet+popen)-pi*A_DOMAIN/1000.0))
        su+=pup;e1=min(su,ET_UPLAND*etoi*A_UPLAND/1000.0);su-=e1;dex=max(su-C_UPLAND,0.0);su-=dex
        sw+=pwet
        e2pot=etoi*(KWET*awet+float(kterr)*ater_eff)/1000.0
        e2=min(sw,e2pot);sw-=e2;dw=max(sw-C_WET,0.0);sw-=dw
        local=dex*hp['local_frac'];deep=dex-local
        fast+=local*FAST_FRAC;slow+=local*(1.0-FAST_FRAC)
        qf=min(fast,fast/hp['tau_fast']);qs=min(slow,slow/TAU_SLOW_D);fast-=qf;slow-=qs;qr=qf+qs
        surf+=popen+dw+qr
        aloss=av(surf);eo_p=epi*aloss/1000.0;qo_p=surf/hp['tau_surf'];qg_p=hp['k_gw_mm_d']*aloss/1000.0
        lp=eo_p+qo_p+qg_p;fac=min(1.0,surf/lp) if lp>0 else 1.0
        eo=eo_p*fac;qo=qo_p*fac;qg=qg_p*fac;surf-=eo+qo+qg
        if surf<0.0 and surf>-1e-12:surf=0.0
        an=av(surf)
        # Causal update: today's post-loss hydraulic exposure changes tomorrow's
        # persistent terrestrialized-area state.
        ex=min(max((A0-an)/A0,0.0),1.0);dacc+=ex/365.0
        aterr_persistent=min(float(beta)*dacc,A0)
        total=su+sw+fast+slow+surf;inputs=pup+pwet+popen;outputs=e1+e2+eo+deep+qo+qg
        err=prev+inputs-outputs-total;max_mass=max(max_mass,abs(err));prev=total
        area[i]=an;V[i]=surf;qret[i]=qr;aterr[i]=aterr_persistent;dose[i]=dacc;wet_et[i]=e2
    return {'dates':dates,'area':area,'V':V,'return_flow':qret,'A_terr':aterr,'D':dose,'wetland_vegetation_ET_m3':wet_et,
            'mass_error':max_mass,'area_partition_error':max_area,'precip_partition_error':max_precip}


def evaluate(F,P,beta,kterr,train=None):
    h=hydro_feedback(F,P,beta,kterr)
    Aterr=annual_support(h['dates'],h['A_terr'],EVAL_YEARS,OBS_MONTHS)
    H=hydrologic_feature(h['dates'],h['return_flow'],int(P['hydro_window_d']),EVAL_YEARS,OBS_MONTHS)
    Gd,_,_=peat_geomorphic_loss(h['dates'],h['V'],PEAT,P['V0'],P['p_shape']);G=annual_support(h['dates'],Gd,EVAL_YEARS,OBS_MONTHS)
    offset=[A0-Aterr[i]-G[i] for i in range(len(Y))]
    if train is None:train=list(range(len(Y)))
    kh=fit_one_nonnegative_fixed([H[i] for i in train],[Y[i]-offset[i] for i in train])
    pred=predict_fixed(offset,H,kh);met=metrics_fixed(pred,Y)
    return h,Aterr,H,G,kh,pred,met


def candidate_grid(F,P):
    rows=[];states={}
    for kt in KTERR_ANCHORS:
        coarse=[]
        for b in BETA_COARSE:
            h,Aterr,H,G,kh,pred,met=evaluate(F,P,b,kt)
            coarse.append((met['nRMSE_pct'],b,h,Aterr,H,G,kh,pred,met))
        cb=min(coarse,key=lambda z:(z[0],z[1]))[1]
        fine=sorted(set(max(0.0,cb+d) for d in range(-10,11)))
        for b in fine:
            h,Aterr,H,G,kh,pred,met=evaluate(F,P,b,kt)
            key=(kt,b);states[key]=(h,Aterr,H,G)
            rows.append({'K_terr':kt,'beta_m2_per_exposure_yr':b,'RMSE_m2':met['RMSE_m2'],'nRMSE_pct':met['nRMSE_pct'],
                         'K_hydro_m2_per_m3':kh,'Aterr_2023_m2':Aterr[-1],
                         **{f'pred_{y}':pred[i] for i,y in enumerate(EVAL_YEARS)}})
    # Deduplicate fine candidates if adjacent coarse minima generated overlap (not expected per K anchor).
    uniq={(r['K_terr'],r['beta_m2_per_exposure_yr']):r for r in rows}
    return list(uniq.values()),states


def loocv_nested(F,P,rows):
    errs=[];choices=[]
    for hold in range(len(Y)):
        train=[i for i in range(len(Y)) if i!=hold];cand=[]
        for r in rows:
            kt=r['K_terr'];b=r['beta_m2_per_exposure_yr']
            h,Aterr,H,G,kh,pred,met=evaluate(F,P,b,kt,train=train)
            trm=metrics_fixed([pred[i] for i in train],[Y[i] for i in train])
            cand.append((trm['RMSE_m2'],kt,b,pred[hold],kh))
        z=min(cand,key=lambda q:(q[0],q[1],q[2]));errs.append(float(z[3])-Y[hold])
        choices.append({'held_out_year':EVAL_YEARS[hold],'K_terr':z[1],'beta_m2_per_exposure_yr':z[2],'K_hydro_m2_per_m3':z[4]})
    rm=math.sqrt(math.fsum(e*e for e in errs)/len(errs));return rm,100.0*rm/mean_fsum(Y),choices


def main():
    F,_,_,_=deterministic_forcing();P=dict(SELECTED_STRUCTURE)
    rows,states=candidate_grid(F,P);rows.sort(key=lambda r:(r['nRMSE_pct'],r['K_terr'],r['beta_m2_per_exposure_yr']))
    best=rows[0]
    # Explicit Kterr=1 no-ET-feedback anchor should remain close to Stage74 cumulative-exposure result.
    nofb=min((r for r in rows if abs(r['K_terr']-1.0)<1e-12),key=lambda r:r['nRMSE_pct'])
    lrm,lnr,choices=loocv_nested(F,P,rows)
    with (OUT/'stage75_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    hbest,Aterr,H,G,kh,pred,met=evaluate(F,P,best['beta_m2_per_exposure_yr'],best['K_terr'])
    result={'status':'PASS_STAGE75_REFERENCE_BOUNDED_ET_FEEDBACK_TEST','pond_area_observation_2022':'ABSENT',
            'observation_variable':'mapped open-water pond surface area','observation_support':'April-May',
            'peat_rate_mm_yr':PEAT,'wetland_reference_Kc':KWET,'tested_Kterr_literature_anchors':KTERR_ANCHORS,
            'best_full_six_year':best,'no_ET_contrast_Kterr_1':nofb,
            'best_implies_ET_increase_relative_to_current_wetland':bool(best['K_terr']>KWET),
            'best_implies_ET_decrease_relative_to_current_wetland':bool(best['K_terr']<KWET),
            'nested_LOOCV_RMSE_m2':lrm,'nested_LOOCV_nRMSE_pct':lnr,'nested_LOOCV_choices':choices,
            'selection_rule':'K_terr restricted to literature anchors; beta is site-calibrated physical area-per-exposure-year coefficient; rank is output only',
            'references':[
              {'citation':'Pereira, Paredes & Espirito-Santo 2024','doi':'10.1007/s00271-024-00923-9','role':'FAO-PM wetland/riparian Kc synthesis and tested Kterr anchors'},
              {'citation':'Drexler et al. 2004','doi':'10.1002/hyp.1462','role':'wetland ET methods review; no universal single ET method'},
              {'citation':'Mohamed et al. 2012','doi':'10.1016/j.pce.2011.08.005','role':'wetland/open-water evaporation ratio is site-specific and controlled by biophysical properties'},
            ],
            'physical_closure':{'mass_error_m3':hbest['mass_error'],'area_partition_error_m2':hbest['area_partition_error'],'precip_partition_error_m3':hbest['precip_partition_error']}}
    (OUT/'stage75_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
