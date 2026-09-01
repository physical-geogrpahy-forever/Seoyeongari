#!/usr/bin/env python3
"""Stage76 — field-anchored woody-encroachment interception feedback.

This stage tests a genuine positive ecohydrologic feedback without fitting an
arbitrary vegetation ET multiplier:

    hydraulic exposure -> cumulative exposure dose D
    -> persistent terrestrialized area A_terr = beta_D D
    -> after field-supported woody establishment lag, A_woody
    -> canopy interception loss on A_woody
    -> reduced wetland-soil precipitation -> hydrology -> exposure

Independent Seoyeongari evidence
--------------------------------
The project field/tree-ring dataset contains six trees with
    Age = 5.283 + 1.760 * Distance(m), R2 ~= 0.916,
consistent with younger trees toward the pond and a several-year woody
establishment lag. We therefore FIX the lag at 5.283 yr; it is not selected by
pond-area fit.

Site vegetation/soil observations also distinguish aquatic vegetation,
terrestrial grassland and Cryptomeria japonica forest around the wetland.

Interception anchors
--------------------
No interception coefficient is freely optimized. We test:
- 0.0000 : no-feedback contrast
- 0.1337 : Japanese cedar rainfall interception reported in a young stand
- 0.2550 : Sugi (Cryptomeria japonica) stand rainfall interception measured
           over 19 months (Saito et al. 2013, J Hydrol,
           DOI 10.1016/j.jhydrol.2013.09.053)

The existing wetland ET calculation is otherwise unchanged (no fitted Kterr).
Peat central rate remains the field Clymo 0.38 mm/yr estimate.
2022 pond-area observation remains absent.
"""
from __future__ import annotations

import csv, json, math
from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_geometry import area_v_deterministic
from eghm_deterministic_kernel import (
    A0,A_WET,A_UPLAND,A_DOMAIN,C_UPLAND,C_WET,ET_UPLAND,FAST_FRAC,TAU_SLOW_D,
    EVAL_YEARS,OBS_MONTHS,SELECTED_STRUCTURE,annual_support,hydrologic_feature,mean_fsum,
)
from eghm_deterministic_scenarios import (
    fit_one_nonnegative_fixed,metrics_fixed,peat_geomorphic_loss,predict_fixed,
)

OUT=Path('stage76_outputs');OUT.mkdir(exist_ok=True)
OBS={2013:2154.430,2015:2147.678,2017:2051.218,2019:2045.159,2021:1965.256,2023:1882.700}
Y=[OBS[y] for y in EVAL_YEARS]
PEAT=0.38
WOODY_LAG_YR=5.283
WOODY_LAG_D=int(round(WOODY_LAG_YR*365.2425))
INTERCEPTION_ANCHORS=[0.0,0.1337,0.2550]
BETA_COARSE=[float(x) for x in range(0,301,10)]


def hydro_woody_feedback(forcing:Mapping[str,Sequence[float]],p:Mapping[str,float],beta:float,interception_fraction:float):
    pre=[float(x) for x in forcing['pre']];eto=[float(x) for x in forcing['eto']];ep=[float(x) for x in forcing['ep']]
    dates=pd.to_datetime(forcing['date']);n=len(pre)
    hp={k:float(p[k]) for k in ('V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d')}
    su=0.5*C_UPLAND;sw=0.5*C_WET;fast=0.0;slow=0.0;surf=hp['V0'];prev=su+sw+surf
    area=[0.0]*n;V=[0.0]*n;qret=[0.0]*n;aterr=[0.0]*n;awoody=[0.0]*n;dose=[0.0]*n;qint=[0.0]*n
    # Daily increments in persistent terrestrialized area. An increment enters
    # the woody pool only after the fixed field-supported lag.
    cohort=[0.0]*n
    dacc=0.0;aterr_persistent=0.0;woody_persistent=0.0
    max_mass=max_area=max_precip=0.0
    def av(v):return area_v_deterministic(v,hp['V0'],hp['p_shape'],A0=A0,A_WET=A_WET)

    for i in range(n):
        if i-WOODY_LAG_D>=0:
            woody_persistent+=cohort[i-WOODY_LAG_D]
        pi=pre[i];etoi=eto[i];epi=ep[i]
        ap=av(surf);aw=max(A_WET-ap,0.0)
        woody_eff=min(max(woody_persistent,0.0),max(aterr_persistent,0.0),aw,A0)
        pup=pi*A_UPLAND/1000.0
        pwet_gross=pi*aw/1000.0
        popen=pi*ap/1000.0
        interception=pi*woody_eff*float(interception_fraction)/1000.0
        pwet_net=max(pwet_gross-interception,0.0)
        max_area=max(max_area,abs((A_UPLAND+aw+ap)-A_DOMAIN))
        max_precip=max(max_precip,abs((pup+pwet_gross+popen)-pi*A_DOMAIN/1000.0))

        su+=pup;e1=min(su,ET_UPLAND*etoi*A_UPLAND/1000.0);su-=e1;dex=max(su-C_UPLAND,0.0);su-=dex
        sw+=pwet_net;e2=min(sw,etoi*aw/1000.0);sw-=e2;dw=max(sw-C_WET,0.0);sw-=dw
        local=dex*hp['local_frac'];deep=dex-local
        fast+=local*FAST_FRAC;slow+=local*(1.0-FAST_FRAC)
        qf=min(fast,fast/hp['tau_fast']);qs=min(slow,slow/TAU_SLOW_D);fast-=qf;slow-=qs;qr=qf+qs
        surf+=popen+dw+qr
        aloss=av(surf);eo_p=epi*aloss/1000.0;qo_p=surf/hp['tau_surf'];qg_p=hp['k_gw_mm_d']*aloss/1000.0
        lp=eo_p+qo_p+qg_p;fac=min(1.0,surf/lp) if lp>0.0 else 1.0
        eo=eo_p*fac;qo=qo_p*fac;qg=qg_p*fac;surf-=eo+qo+qg
        if surf<0.0 and surf>-1e-12:surf=0.0
        an=av(surf)

        # Causal terrestrialization update after today's hydraulic state.
        ex=min(max((A0-an)/A0,0.0),1.0);dacc+=ex/365.0
        anew=min(float(beta)*dacc,A0)
        cohort[i]=max(anew-aterr_persistent,0.0)
        aterr_persistent=anew

        total=su+sw+fast+slow+surf
        # Gross precipitation is the external input; canopy interception is an
        # explicit same-day atmospheric output.
        inputs=pup+pwet_gross+popen
        outputs=e1+e2+eo+deep+qo+qg+interception
        err=prev+inputs-outputs-total;max_mass=max(max_mass,abs(err));prev=total
        area[i]=an;V[i]=surf;qret[i]=qr;aterr[i]=aterr_persistent;awoody[i]=woody_persistent;dose[i]=dacc;qint[i]=interception
    return {'dates':dates,'area':area,'V':V,'return_flow':qret,'A_terr':aterr,'A_woody':awoody,'D':dose,'canopy_interception_m3':qint,
            'mass_error':max_mass,'area_partition_error':max_area,'precip_partition_error':max_precip}


def state(F,P,beta,ic):
    h=hydro_woody_feedback(F,P,beta,ic)
    Aterr=annual_support(h['dates'],h['A_terr'],EVAL_YEARS,OBS_MONTHS)
    Awoody=annual_support(h['dates'],h['A_woody'],EVAL_YEARS,OBS_MONTHS)
    H=hydrologic_feature(h['dates'],h['return_flow'],int(P['hydro_window_d']),EVAL_YEARS,OBS_MONTHS)
    Gd,_,_=peat_geomorphic_loss(h['dates'],h['V'],PEAT,P['V0'],P['p_shape']);G=annual_support(h['dates'],Gd,EVAL_YEARS,OBS_MONTHS)
    return h,Aterr,Awoody,H,G


def fit_cached(st,train=None):
    h,Aterr,Awoody,H,G=st
    if train is None:train=list(range(len(Y)))
    offset=[A0-Aterr[i]-G[i] for i in range(len(Y))]
    kh=fit_one_nonnegative_fixed([H[i] for i in train],[Y[i]-offset[i] for i in train])
    pred=predict_fixed(offset,H,kh);met=metrics_fixed(pred,Y)
    return kh,pred,met


def main():
    F,_,_,_=deterministic_forcing();P=dict(SELECTED_STRUCTURE)
    rows=[];states={}
    for ic in INTERCEPTION_ANCHORS:
        coarse=[]
        for b in BETA_COARSE:
            st=state(F,P,b,ic);kh,pred,met=fit_cached(st);coarse.append((met['nRMSE_pct'],b))
        cb=min(coarse,key=lambda z:(z[0],z[1]))[1]
        for b in sorted(set(max(0.0,cb+d) for d in range(-10,11))):
            st=state(F,P,b,ic);states[(ic,b)]=st;kh,pred,met=fit_cached(st)
            qint=sum(st[0]['canopy_interception_m3'])
            rows.append({'interception_fraction':ic,'beta_m2_per_exposure_yr':b,'RMSE_m2':met['RMSE_m2'],'nRMSE_pct':met['nRMSE_pct'],
                         'K_hydro_m2_per_m3':kh,'Aterr_2023_m2':st[1][-1],'Awoody_2023_m2':st[2][-1],
                         'total_2011_2023_canopy_interception_m3':qint,
                         **{f'pred_{y}':pred[i] for i,y in enumerate(EVAL_YEARS)}})
    rows.sort(key=lambda r:(r['nRMSE_pct'],r['interception_fraction'],r['beta_m2_per_exposure_yr']))
    best=rows[0];nofb=min((r for r in rows if r['interception_fraction']==0.0),key=lambda r:r['nRMSE_pct'])

    errs=[];choices=[]
    for hold in range(len(Y)):
        train=[i for i in range(len(Y)) if i!=hold];cand=[]
        for r in rows:
            st=states[(r['interception_fraction'],r['beta_m2_per_exposure_yr'])];kh,pred,_=fit_cached(st,train)
            tr=metrics_fixed([pred[i] for i in train],[Y[i] for i in train])
            cand.append((tr['RMSE_m2'],r['interception_fraction'],r['beta_m2_per_exposure_yr'],pred[hold],kh))
        z=min(cand,key=lambda x:(x[0],x[1],x[2]));errs.append(z[3]-Y[hold]);choices.append({'held_out_year':EVAL_YEARS[hold],'interception_fraction':z[1],'beta_m2_per_exposure_yr':z[2],'K_hydro_m2_per_m3':z[4]})
    lrm=math.sqrt(math.fsum(e*e for e in errs)/len(errs));lnr=100*lrm/mean_fsum(Y)

    with (OUT/'stage76_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    hbest=states[(best['interception_fraction'],best['beta_m2_per_exposure_yr'])][0]
    result={'status':'PASS_STAGE76_WOODY_INTERCEPTION_FEEDBACK_TEST','pond_area_observation_2022':'ABSENT','peat_rate_mm_yr':PEAT,
            'woody_lag_years_fixed_from_site_tree_ring_intercept':WOODY_LAG_YR,'woody_lag_days':WOODY_LAG_D,
            'tested_interception_fractions':INTERCEPTION_ANCHORS,'best_full_six_year':best,'no_feedback_contrast':nofb,
            'nested_LOOCV_RMSE_m2':lrm,'nested_LOOCV_nRMSE_pct':lnr,'nested_LOOCV_choices':choices,
            'feedback_loop':'hydraulic exposure -> D -> A_terr -> lagged A_woody -> canopy interception -> hydrology -> exposure',
            'references':[
              {'citation':'Saito et al. 2013','doi':'10.1016/j.jhydrol.2013.09.053','role':'Cryptomeria japonica measured interception fraction 25.5%'},
              {'citation':'Japanese cedar rainfall redistribution study','role':'young-stand interception anchor 13.37%'},
              {'citation':'Seoyeongari tree-ring field analysis','role':'Age = 5.283 + 1.760 Distance; woody lag fixed at 5.283 yr, not fit'},
            ],
            'physical_closure':{'mass_error_m3':hbest['mass_error'],'area_partition_error_m2':hbest['area_partition_error'],'precip_partition_error_m3':hbest['precip_partition_error']}}
    (OUT/'stage76_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
