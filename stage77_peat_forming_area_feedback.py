#!/usr/bin/env python3
"""Stage77 — terrestrialization-dependent peat-forming-area feedback.

Question
--------
Field cores show that the aquatic/wet center of Seoyeongari has higher organic
matter than terrestrial grassland and Cryptomeria-dominated peripheral cores,
where drainage and decomposition are more active. Therefore it is not defensible
to let the same wet-peat geomorphic contribution act uniformly over area already
classified as persistently terrestrialized.

This stage does NOT create a fitted decomposition coefficient and does NOT alter
the field-derived local wet-peat long-term accumulation rate (0.38 mm/yr).
Instead, it tests an area-partition interpretation:

    f_peat(t) = max(1 - A_terr(t)/A0, 0)
    G_eff(t)  = f_peat(t) * G_wet(t)

where G_wet is the surface-expression effect that would arise if the whole
original pond footprint retained the local wet-peat accumulation regime.
Thus local vertical rate is preserved and only the basin-integrated area over
which that process contributes is reduced.

Three formulations are compared:
1. uniform_peat_oneway: Stage74 reference, G=G_wet and D from hydraulic area;
2. area_partition_oneway: D from hydraulic area, but G=f_peat*G_wet;
3. coupled_area_partition: causal negative eco-geomorphic feedback. Previous
   terrestrialized area reduces today's peat-forming fraction; today's peat
   surface-expression modifies ecological exposure; exposure updates D and
   tomorrow's A_terr.

No scenario/rank outcome is an acceptance gate. 2022 pond-area observation is
absent. Hydrologic process parameters and conserved V are unchanged.
"""
from __future__ import annotations

import csv, json, math
from pathlib import Path
from typing import Dict, List, Sequence

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_kernel import (
    A0,EVAL_YEARS,OBS_MONTHS,SELECTED_STRUCTURE,annual_support,hydro,
    hydrologic_feature,mean_fsum,
)
from eghm_deterministic_scenarios import (
    fit_one_nonnegative_fixed,metrics_fixed,peat_geomorphic_loss,predict_fixed,
)

OUT=Path('stage77_outputs');OUT.mkdir(exist_ok=True)
OBS={2013:2154.430,2015:2147.678,2017:2051.218,2019:2045.159,2021:1965.256,2023:1882.700}
Y=[OBS[y] for y in EVAL_YEARS]
PEAT=0.38
BETA_COARSE=[float(x) for x in range(0,301,10)]
MODES=('uniform_peat_oneway','area_partition_oneway','coupled_area_partition')


def clamp01(x:float)->float:return min(max(float(x),0.0),1.0)


def ecological_path(area:Sequence[float],Gwet:Sequence[float],beta:float,mode:str):
    if len(area)!=len(Gwet):raise ValueError('daily arrays mismatch')
    D=[];Aterr=[];Geff=[];Aexpose=[];Fpeat=[]
    dacc=0.0;at_prev=0.0
    for ah,gw in zip(area,Gwet):
        ah=float(ah);gw=float(gw)
        if mode=='uniform_peat_oneway':
            fp=1.0;ge=gw;aexp=ah
        elif mode=='area_partition_oneway':
            # Ecological exposure remains hydrology-only. Area partition affects
            # geomorphic expression after Aterr has been established.
            fp=clamp01(1.0-at_prev/A0);ge=gw*fp;aexp=ah
        elif mode=='coupled_area_partition':
            # Causal negative feedback: previous terrestrialization weakens the
            # area-integrated peat effect; today's residual peat expression then
            # contributes to today's exposure and updates tomorrow's Aterr.
            fp=clamp01(1.0-at_prev/A0);ge=gw*fp;aexp=max(ah-ge,0.0)
        else:raise KeyError(mode)
        e=clamp01((A0-aexp)/A0);dacc+=e/365.0
        at=min(max(float(beta)*dacc,0.0),A0)
        # For the one-way area-partition case, apply today's updated Aterr to the
        # reported geomorphic contribution without feeding it back to D.
        if mode=='area_partition_oneway':
            fp=clamp01(1.0-at/A0);ge=gw*fp
        D.append(dacc);Aterr.append(at);Geff.append(ge);Aexpose.append(aexp);Fpeat.append(fp);at_prev=at
    return {'D':D,'A_terr':Aterr,'G_eff':Geff,'A_exposure_basis':Aexpose,'peat_forming_fraction':Fpeat}


def state(h,H,Gwet,beta,mode):
    ec=ecological_path(h['area'],Gwet,beta,mode)
    At=annual_support(h['dates'],ec['A_terr'],EVAL_YEARS,OBS_MONTHS)
    G=annual_support(h['dates'],ec['G_eff'],EVAL_YEARS,OBS_MONTHS)
    Fp=annual_support(h['dates'],ec['peat_forming_fraction'],EVAL_YEARS,OBS_MONTHS)
    D=annual_support(h['dates'],ec['D'],EVAL_YEARS,OBS_MONTHS)
    return ec,At,G,Fp,D


def fit_state(At,G,H,train=None):
    if train is None:train=list(range(len(Y)))
    offset=[A0-At[i]-G[i] for i in range(len(Y))]
    kh=fit_one_nonnegative_fixed([H[i] for i in train],[Y[i]-offset[i] for i in train])
    pred=predict_fixed(offset,H,kh);met=metrics_fixed(pred,Y)
    return kh,pred,met


def main():
    F,_,_,_=deterministic_forcing();P=dict(SELECTED_STRUCTURE);h=hydro(F,P)
    H=hydrologic_feature(h['dates'],h['return_flow'],int(P['hydro_window_d']),EVAL_YEARS,OBS_MONTHS)
    Gwet,_,_=peat_geomorphic_loss(h['dates'],h['V'],PEAT,P['V0'],P['p_shape'])
    rows=[];cache={}
    for mode in MODES:
        coarse=[]
        for b in BETA_COARSE:
            st=state(h,H,Gwet,b,mode);kh,pred,met=fit_state(st[1],st[2],H)
            coarse.append((met['nRMSE_pct'],b))
        cb=min(coarse,key=lambda z:(z[0],z[1]))[1]
        for b in sorted(set(max(0.0,cb+d) for d in range(-10,11))):
            st=state(h,H,Gwet,b,mode);cache[(mode,b)]=st;kh,pred,met=fit_state(st[1],st[2],H)
            rows.append({'mode':mode,'beta_m2_per_exposure_yr':b,'RMSE_m2':met['RMSE_m2'],'nRMSE_pct':met['nRMSE_pct'],
                         'K_hydro_m2_per_m3':kh,'D_2023_exposure_yr':st[4][-1],'Aterr_2023_m2':st[1][-1],
                         'G_2023_m2':st[2][-1],'peat_forming_fraction_2023':st[3][-1],
                         **{f'pred_{y}':pred[i] for i,y in enumerate(EVAL_YEARS)}})
    rows.sort(key=lambda r:(r['nRMSE_pct'],r['mode'],r['beta_m2_per_exposure_yr']))
    best=rows[0]
    family_best={m:min((r for r in rows if r['mode']==m),key=lambda r:(r['nRMSE_pct'],r['beta_m2_per_exposure_yr'])) for m in MODES}

    # Nested LOOCV over both formulation and beta. Diagnostic only.
    errs=[];choices=[]
    for hold in range(len(Y)):
        train=[i for i in range(len(Y)) if i!=hold];cand=[]
        for r in rows:
            st=cache[(r['mode'],r['beta_m2_per_exposure_yr'])];kh,pred,_=fit_state(st[1],st[2],H,train)
            tr=metrics_fixed([pred[i] for i in train],[Y[i] for i in train])
            cand.append((tr['RMSE_m2'],r['mode'],r['beta_m2_per_exposure_yr'],pred[hold],kh))
        z=min(cand,key=lambda q:(q[0],q[1],q[2]));errs.append(z[3]-Y[hold])
        choices.append({'held_out_year':EVAL_YEARS[hold],'mode':z[1],'beta_m2_per_exposure_yr':z[2],'K_hydro_m2_per_m3':z[4]})
    lrm=math.sqrt(math.fsum(e*e for e in errs)/len(errs));lnr=100.0*lrm/mean_fsum(Y)

    with (OUT/'stage77_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    result={'status':'PASS_STAGE77_PEAT_FORMING_AREA_FEEDBACK_TEST','pond_area_observation_2022':'ABSENT',
            'local_wet_peat_rate_mm_yr':PEAT,'local_wet_peat_rate_changed':False,'conserved_hydrology_changed':False,
            'tested_modes':list(MODES),'best_full_six_year':best,'family_best':family_best,
            'nested_LOOCV_RMSE_m2':lrm,'nested_LOOCV_nRMSE_pct':lnr,'nested_LOOCV_choices':choices,
            'central_interpretation':'Area partition preserves the local 0.38 mm/yr wet-peat vertical rate and reduces only the basin-integrated geomorphic contribution over terrestrialized area; it is not a fitted decomposition law.',
            'field_support':'Aquatic-center cores have higher organic matter than terrestrial grassland/Cryptomeria peripheral cores; peripheral terrestrialized zones show stronger drainage/decomposition.',
            'references':[
              {'citation':'Seoyeongari field carbon/vegetation report','role':'site-specific vegetation-type OM difference and drainage/decomposition evidence'},
              {'citation':'Laiho 2006','doi':'10.1016/j.soilbio.2006.02.017','role':'water-table lowering increases oxygen availability and can accelerate peat decomposition'},
              {'citation':'Morris & Waddington 2011','doi':'10.1029/2010WR009492','role':'water-table/oxic-zone controls on peat decay and ecohydrologic feedback'},
              {'citation':'Philben et al. 2014','doi':'10.1002/2013JG002573','role':'oxygen exposure time as strong control on peat decomposition'},
              {'citation':'Morris, Belyea & Baird 2011','doi':'10.1111/j.1365-2745.2011.01842.x','role':'coupled peatland ecohydrological feedback theory'},
            ],
            'physical_closure':{'mass_error_m3':h['mass_error'],'area_partition_error_m2':h['area_partition_error'],'precip_partition_error_m3':h['precip_partition_error']}}
    (OUT/'stage77_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
