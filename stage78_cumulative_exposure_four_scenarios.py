#!/usr/bin/env python3
"""Stage78 — rebuild the four manuscript scenarios after replacing S by cumulative exposure.

Scenario definitions
--------------------
Baseline:
    A = A0 + Kh H
Hydrosere Only:
    A = A0 - A_terr + Kh H
    A_terr = beta_D * cumulative hydraulic exposure dose
Eco-Geo Only:
    A = A0 - G_wet + Kh H
Integrated:
    A = A0 - A_terr - G_eff + Kh H
    G_eff uses the Stage77 causal peat-forming-area partition.

The abstract S, r_est and K_colonizable observation coefficient are not used in
these scenario calculations. beta_D has units m2 per exposure-year and directly
converts cumulative hydrologic exposure to persistent terrestrialized area.

Hydrology remains the accepted deterministic conserved trajectory. Peat rate is
external/site-derived (0.29/0.38/0.47 mm/yr; central 0.38), never selected by
pond-area rank. Scenario ranking is output only. 2022 pond-area observation is
absent. Nested LOOCV is diagnostic only.
"""
from __future__ import annotations

import csv,json,math
from pathlib import Path
from typing import Dict,List,Sequence

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_kernel import (
    A0,EVAL_YEARS,OBS_MONTHS,SELECTED_STRUCTURE,annual_support,hydro,
    hydrologic_feature,mean_fsum,
)
from eghm_deterministic_scenarios import (
    fit_one_nonnegative_fixed,metrics_fixed,peat_geomorphic_loss,predict_fixed,
)
from stage77_peat_forming_area_feedback import ecological_path

OUT=Path('stage78_outputs');OUT.mkdir(exist_ok=True)
OBS={2013:2154.430,2015:2147.678,2017:2051.218,2019:2045.159,2021:1965.256,2023:1882.700}
Y=[OBS[y] for y in EVAL_YEARS]
PEAT_RATES=[0.29,0.38,0.47]
CENTRAL_PEAT=0.38
BETA_COARSE=[float(x) for x in range(0,301,10)]


def metric_aicc(met:Dict[str,float],k:int)->float:
    n=len(Y);rss=(float(met['RMSE_m2'])**2)*n
    if rss<=0:return float('-inf')
    if n-k-1<=0:return float('inf')
    return n*math.log(rss/n)+2*k+(2*k*(k+1))/(n-k-1)


def direct_exposure_state(area:Sequence[float],beta:float):
    d=0.0;D=[];At=[]
    for a in area:
        e=min(max((A0-float(a))/A0,0.0),1.0);d+=e/365.0
        D.append(d);At.append(min(max(float(beta)*d,0.0),A0))
    return D,At


def fit_offset(offset,H,train=None):
    if train is None:train=list(range(len(Y)))
    kh=fit_one_nonnegative_fixed([H[i] for i in train],[Y[i]-offset[i] for i in train])
    pred=predict_fixed(offset,H,kh);met=metrics_fixed(pred,Y)
    return kh,pred,met


def beta_candidates_hydrosere(h,H):
    rows=[];cache={}
    coarse=[]
    for b in BETA_COARSE:
        D,Ad=direct_exposure_state(h['area'],b);At=annual_support(h['dates'],Ad,EVAL_YEARS,OBS_MONTHS)
        off=[A0-x for x in At];kh,pred,met=fit_offset(off,H);coarse.append((met['nRMSE_pct'],b))
    cb=min(coarse,key=lambda z:(z[0],z[1]))[1]
    for b in sorted(set(max(0.0,cb+d) for d in range(-10,11))):
        D,Ad=direct_exposure_state(h['area'],b);At=annual_support(h['dates'],Ad,EVAL_YEARS,OBS_MONTHS)
        Da=annual_support(h['dates'],D,EVAL_YEARS,OBS_MONTHS);cache[b]=(At,Da)
        off=[A0-x for x in At];kh,pred,met=fit_offset(off,H)
        rows.append({'beta':b,'At':At,'D':Da,'Kh':kh,'pred':pred,'met':met})
    return rows,cache


def beta_candidates_integrated(h,H,Gwet):
    rows=[];cache={};coarse=[]
    for b in BETA_COARSE:
        ec=ecological_path(h['area'],Gwet,b,'coupled_area_partition')
        At=annual_support(h['dates'],ec['A_terr'],EVAL_YEARS,OBS_MONTHS);G=annual_support(h['dates'],ec['G_eff'],EVAL_YEARS,OBS_MONTHS)
        off=[A0-At[i]-G[i] for i in range(len(Y))];kh,pred,met=fit_offset(off,H);coarse.append((met['nRMSE_pct'],b))
    cb=min(coarse,key=lambda z:(z[0],z[1]))[1]
    for b in sorted(set(max(0.0,cb+d) for d in range(-10,11))):
        ec=ecological_path(h['area'],Gwet,b,'coupled_area_partition')
        At=annual_support(h['dates'],ec['A_terr'],EVAL_YEARS,OBS_MONTHS);G=annual_support(h['dates'],ec['G_eff'],EVAL_YEARS,OBS_MONTHS)
        D=annual_support(h['dates'],ec['D'],EVAL_YEARS,OBS_MONTHS);Fp=annual_support(h['dates'],ec['peat_forming_fraction'],EVAL_YEARS,OBS_MONTHS)
        cache[b]=(At,G,D,Fp)
        off=[A0-At[i]-G[i] for i in range(len(Y))];kh,pred,met=fit_offset(off,H)
        rows.append({'beta':b,'At':At,'G':G,'D':D,'Fp':Fp,'Kh':kh,'pred':pred,'met':met})
    return rows,cache


def best_row(rows):return min(rows,key=lambda z:(z['met']['nRMSE_pct'],z.get('beta',0.0)))


def scenario_full(h,H,peat_rate):
    off0=[A0]*len(Y);kh0,p0,m0=fit_offset(off0,H)
    rh,ch=beta_candidates_hydrosere(h,H);bh=best_row(rh)
    Gwet,_,_=peat_geomorphic_loss(h['dates'],h['V'],peat_rate,SELECTED_STRUCTURE['V0'],SELECTED_STRUCTURE['p_shape'])
    Ga=annual_support(h['dates'],Gwet,EVAL_YEARS,OBS_MONTHS)
    offg=[A0-g for g in Ga];khg,pg,mg=fit_offset(offg,H)
    ri,ci=beta_candidates_integrated(h,H,Gwet);bi=best_row(ri)
    rows=[
      {'Scenario':'Baseline Model','beta_D_m2_per_exposure_yr':None,'K_hydro_m2_per_m3':kh0,'pred':p0,**m0,'AICc':metric_aicc(m0,1)},
      {'Scenario':'Hydrosere Only Model','beta_D_m2_per_exposure_yr':bh['beta'],'K_hydro_m2_per_m3':bh['Kh'],'pred':bh['pred'],**bh['met'],'AICc':metric_aicc(bh['met'],2),'Aterr_2023_m2':bh['At'][-1],'D_2023_exposure_yr':bh['D'][-1]},
      {'Scenario':'Eco-Geo Only Model','beta_D_m2_per_exposure_yr':None,'K_hydro_m2_per_m3':khg,'pred':pg,**mg,'AICc':metric_aicc(mg,1),'G_2023_m2':Ga[-1]},
      {'Scenario':'Integrated Model','beta_D_m2_per_exposure_yr':bi['beta'],'K_hydro_m2_per_m3':bi['Kh'],'pred':bi['pred'],**bi['met'],'AICc':metric_aicc(bi['met'],2),'Aterr_2023_m2':bi['At'][-1],'D_2023_exposure_yr':bi['D'][-1],'G_2023_m2':bi['G'][-1],'peat_forming_fraction_2023':bi['Fp'][-1]},
    ]
    rank={z['Scenario']:i+1 for i,z in enumerate(sorted(rows,key=lambda z:(z['nRMSE_pct'],z['RMSE_m2'],z['Scenario'])))}
    for z in rows:z['rank']=rank[z['Scenario']]
    return rows,{'hydrosere_rows':rh,'integrated_rows':ri,'Gannual':Ga}


def loocv_scenario(h,H,peat_rate,scenario,cache):
    Gwet,_,_=peat_geomorphic_loss(h['dates'],h['V'],peat_rate,SELECTED_STRUCTURE['V0'],SELECTED_STRUCTURE['p_shape'])
    Ga=annual_support(h['dates'],Gwet,EVAL_YEARS,OBS_MONTHS)
    errs=[];choices=[]
    for hold in range(len(Y)):
        tr=[i for i in range(len(Y)) if i!=hold]
        if scenario=='Baseline Model':
            off=[A0]*len(Y);kh,pred,_=fit_offset(off,H,tr);choice=None
        elif scenario=='Eco-Geo Only Model':
            off=[A0-Ga[i] for i in range(len(Y))];kh,pred,_=fit_offset(off,H,tr);choice=None
        elif scenario=='Hydrosere Only Model':
            cand=[]
            for r in cache['hydrosere_rows']:
                off=[A0-r['At'][i] for i in range(len(Y))];kh,pred,_=fit_offset(off,H,tr)
                mt=metrics_fixed([pred[i] for i in tr],[Y[i] for i in tr]);cand.append((mt['RMSE_m2'],r['beta'],pred,kh))
            q=min(cand,key=lambda x:(x[0],x[1]));choice=q[1];pred=q[2];kh=q[3]
        elif scenario=='Integrated Model':
            cand=[]
            for r in cache['integrated_rows']:
                off=[A0-r['At'][i]-r['G'][i] for i in range(len(Y))];kh,pred,_=fit_offset(off,H,tr)
                mt=metrics_fixed([pred[i] for i in tr],[Y[i] for i in tr]);cand.append((mt['RMSE_m2'],r['beta'],pred,kh))
            q=min(cand,key=lambda x:(x[0],x[1]));choice=q[1];pred=q[2];kh=q[3]
        else:raise KeyError(scenario)
        errs.append(pred[hold]-Y[hold]);choices.append({'held_out_year':EVAL_YEARS[hold],'beta':choice,'K_hydro_m2_per_m3':kh})
    rm=math.sqrt(math.fsum(e*e for e in errs)/len(errs));return rm,100*rm/mean_fsum(Y),choices


def main():
    F,_,_,_=deterministic_forcing();P=dict(SELECTED_STRUCTURE);h=hydro(F,P)
    H=hydrologic_feature(h['dates'],h['return_flow'],int(P['hydro_window_d']),EVAL_YEARS,OBS_MONTHS)
    allrows=[];sensitivity=[];central_cache=None;central_rows=None
    for rate in PEAT_RATES:
        rows,cache=scenario_full(h,H,rate)
        for z in rows:
            zz={k:v for k,v in z.items() if k!='pred'};zz['peat_rate_mm_yr']=rate
            for i,y in enumerate(EVAL_YEARS):zz[f'pred_{y}']=z['pred'][i]
            allrows.append(zz)
        sensitivity.append({'peat_rate_mm_yr':rate,'ranking':[z['Scenario'] for z in sorted(rows,key=lambda z:z['rank'])],'Integrated_nRMSE_pct':next(z['nRMSE_pct'] for z in rows if z['Scenario']=='Integrated Model'),'Hydrosere_nRMSE_pct':next(z['nRMSE_pct'] for z in rows if z['Scenario']=='Hydrosere Only Model')})
        if abs(rate-CENTRAL_PEAT)<1e-12:central_cache=cache;central_rows=rows

    loocv={}
    for scen in ('Baseline Model','Hydrosere Only Model','Eco-Geo Only Model','Integrated Model'):
        rm,nr,ch=loocv_scenario(h,H,CENTRAL_PEAT,scen,central_cache);loocv[scen]={'RMSE_m2':rm,'nRMSE_pct':nr,'choices':ch}

    # Scenario rows contain scenario-specific diagnostics, so construct a union
    # schema instead of assuming the first (Baseline) row has every field.
    fieldnames=[]
    for row in allrows:
        for key in row:
            if key not in fieldnames:fieldnames.append(key)
    with (OUT/'stage78_all_scenarios.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fieldnames,extrasaction='raise');w.writeheader();w.writerows(allrows)

    central=[{k:v for k,v in z.items() if k!='pred'} for z in sorted(central_rows,key=lambda z:z['rank'])]
    result={'status':'PASS_STAGE78_CUMULATIVE_EXPOSURE_FOUR_SCENARIO_COMPARISON','pond_area_observation_2022':'ABSENT','observation_variable':'mapped open-water pond surface area','observation_support':'April-May','ecological_memory':'cumulative hydrologic exposure dose D; no abstract S/r_est/K_colonizable','central_peat_rate_mm_yr':CENTRAL_PEAT,'primary_peat_rates_mm_yr':PEAT_RATES,'central_scenarios':central,'nested_LOOCV_central':loocv,'peat_sensitivity':sensitivity,'AICc_parameter_count':{'Baseline Model':1,'Hydrosere Only Model':2,'Eco-Geo Only Model':1,'Integrated Model':2},'peat_rate_counted_as_fitted_parameter':False,'scenario_rank_not_acceptance_gate':True,'loocv_not_acceptance_gate':True,'physical_closure':{'mass_error_m3':h['mass_error'],'area_partition_error_m2':h['area_partition_error'],'precip_partition_error_m3':h['precip_partition_error']}}
    (OUT/'stage78_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
