#!/usr/bin/env python3
"""Stage94 — publication-defensible fallback route derived from Stage78.

Purpose
-------
Create a frozen fallback route that can be used if the exact-TLMM route does not
reach acceptable site fit/transferability. This route deliberately REMOVES the
Stage78 short-term hydrologic observation term +Kh*H. Pond-area prediction is
therefore driven only by the fixed 2011 reference area, cumulative-exposure
terrestrialization, and the independently constrained peat geomorphic process.

Woody succession is a diagnostic substate of A_terr and never an additional
open-water loss term; this structurally prevents double counting.
"""
from __future__ import annotations
import csv, json, math
from pathlib import Path
from typing import Sequence
import pandas as pd

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_kernel import A0,EVAL_YEARS,OBS_MONTHS,SELECTED_STRUCTURE,annual_support,hydro,mean_fsum
from eghm_deterministic_scenarios import metrics_fixed,peat_geomorphic_loss
from stage77_peat_forming_area_feedback import ecological_path

OUT=Path('stage94_outputs'); OUT.mkdir(exist_ok=True)
OBS={2013:2154.430,2015:2147.678,2017:2051.218,2019:2045.159,2021:1965.256,2023:1882.700}
Y=[OBS[y] for y in EVAL_YEARS]
PEAT=0.38
BETAS=range(0,301)
WOODY_UPPER_BOUND_SENSITIVITY=(3,4,6)
WOODY_MID_DIAGNOSTIC=5


def rmse(pred:Sequence[float],idx:Sequence[int]):
    return math.sqrt(math.fsum((float(pred[i])-Y[i])**2 for i in idx)/len(idx))


def aicc(rmse_m2:float,k:int):
    n=len(Y); rss=(rmse_m2**2)*n
    if rss<=0:return float('-inf')
    if n-k-1<=0:return float('inf')
    return n*math.log(rss/n)+2*k+(0 if k==0 else (2*k*(k+1))/(n-k-1))


def woody_from_lag(dates,aterr,lag_years):
    s=pd.Series([float(v) for v in aterr],index=pd.to_datetime(dates))
    out=[]
    for dt in s.index:
        past=dt-pd.DateOffset(years=int(lag_years)); j=s.index.searchsorted(past,side='right')-1
        out.append(0.0 if j<0 else float(s.iloc[j]))
    return out


def main():
    F,_,_,_=deterministic_forcing();P=dict(SELECTED_STRUCTURE);h=hydro(F,P)
    Gwet,_,_=peat_geomorphic_loss(h['dates'],h['V'],PEAT,P['V0'],P['p_shape'])
    Ga=annual_support(h['dates'],Gwet,EVAL_YEARS,OBS_MONTHS)

    hydro_cache={}; integ_cache={}
    for b in BETAS:
        d=0.0; at=[]; D=[]
        for a in h['area']:
            e=min(max((A0-float(a))/A0,0.0),1.0); d += e/365.0
            D.append(d); at.append(min(float(b)*d,A0))
        At=annual_support(h['dates'],at,EVAL_YEARS,OBS_MONTHS)
        hydro_cache[b]={'pred':[A0-x for x in At],'At':At,'D':annual_support(h['dates'],D,EVAL_YEARS,OBS_MONTHS)}

        ec=ecological_path(h['area'],Gwet,float(b),'coupled_area_partition')
        Ati=annual_support(h['dates'],ec['A_terr'],EVAL_YEARS,OBS_MONTHS)
        Gi=annual_support(h['dates'],ec['G_eff'],EVAL_YEARS,OBS_MONTHS)
        Di=annual_support(h['dates'],ec['D'],EVAL_YEARS,OBS_MONTHS)
        integ_cache[b]={'pred':[A0-Ati[i]-Gi[i] for i in range(len(Y))],'At':Ati,'G':Gi,'D':Di,'ec':ec}

    def fit_beta(cache,train):
        return min(((rmse(v['pred'],train),b,v) for b,v in cache.items()),key=lambda z:(z[0],z[1]))

    p0=[A0]*len(Y); m0=metrics_fixed(p0,Y)
    rh,bh,vh=fit_beta(hydro_cache,list(range(len(Y)))); mh=metrics_fixed(vh['pred'],Y)
    pg=[A0-g for g in Ga]; mg=metrics_fixed(pg,Y)
    ri,bi,vi=fit_beta(integ_cache,list(range(len(Y)))); mi=metrics_fixed(vi['pred'],Y)
    scenarios=[
      {'Scenario':'Baseline Model','fitted_parameter_count':0,'beta_D':None,'RMSE_m2':m0['RMSE_m2'],'nRMSE_pct':m0['nRMSE_pct'],'AICc':aicc(m0['RMSE_m2'],0),'pred':p0},
      {'Scenario':'Hydrosere Only Model','fitted_parameter_count':1,'beta_D':bh,'RMSE_m2':mh['RMSE_m2'],'nRMSE_pct':mh['nRMSE_pct'],'AICc':aicc(mh['RMSE_m2'],1),'pred':vh['pred']},
      {'Scenario':'Eco-Geo Only Model','fitted_parameter_count':0,'beta_D':None,'RMSE_m2':mg['RMSE_m2'],'nRMSE_pct':mg['nRMSE_pct'],'AICc':aicc(mg['RMSE_m2'],0),'pred':pg},
      {'Scenario':'Integrated Model','fitted_parameter_count':1,'beta_D':bi,'RMSE_m2':mi['RMSE_m2'],'nRMSE_pct':mi['nRMSE_pct'],'AICc':aicc(mi['RMSE_m2'],1),'pred':vi['pred']},
    ]
    for rank,z in enumerate(sorted(scenarios,key=lambda q:(q['nRMSE_pct'],q['RMSE_m2'])),1): z['rank']=rank

    loocv={}
    for name,cache in [('Hydrosere Only Model',hydro_cache),('Integrated Model',integ_cache)]:
        errs=[];choices=[]
        for hold in range(len(Y)):
            train=[i for i in range(len(Y)) if i!=hold]
            _,b,v=fit_beta(cache,train); e=v['pred'][hold]-Y[hold];errs.append(e)
            choices.append({'held_out_year':EVAL_YEARS[hold],'beta_D':b,'prediction_m2':v['pred'][hold],'observation_m2':Y[hold],'error_m2':e})
        r=math.sqrt(math.fsum(e*e for e in errs)/len(errs))
        loocv[name]={'RMSE_m2':r,'nRMSE_pct':100*r/mean_fsum(Y),'choices':choices}
    loocv['Baseline Model']={'RMSE_m2':m0['RMSE_m2'],'nRMSE_pct':m0['nRMSE_pct']}
    loocv['Eco-Geo Only Model']={'RMSE_m2':mg['RMSE_m2'],'nRMSE_pct':mg['nRMSE_pct']}

    temporal=[]
    for cutoff in (2,3,4):
        train=list(range(cutoff+1)); test=list(range(cutoff+1,len(Y)))
        tr,b,v=fit_beta(integ_cache,train); errs=[v['pred'][i]-Y[i] for i in test]
        rr=math.sqrt(math.fsum(e*e for e in errs)/len(errs))
        temporal.append({'calibration_through':EVAL_YEARS[cutoff],'training_years':[EVAL_YEARS[i] for i in train],
                         'held_out_years':[EVAL_YEARS[i] for i in test],'beta_D':b,'train_RMSE_m2':tr,
                         'holdout_RMSE_m2':rr,'holdout_nRMSE_pct':100*rr/mean_fsum([Y[i] for i in test]),
                         'predictions':[{'year':EVAL_YEARS[i],'prediction_m2':v['pred'][i],'observation_m2':Y[i],'error_m2':v['pred'][i]-Y[i]} for i in test]})

    profile=[]
    for b,v in integ_cache.items():
        m=metrics_fixed(v['pred'],Y); profile.append({'beta_D':b,'RMSE_m2':m['RMSE_m2'],'nRMSE_pct':m['nRMSE_pct']})
    best_n=mi['nRMSE_pct']
    intervals={str(t):[min(r['beta_D'] for r in profile if r['nRMSE_pct']<=best_n+t),max(r['beta_D'] for r in profile if r['nRMSE_pct']<=best_n+t)] for t in (0.05,0.10,0.25,0.50)}

    wrows=[]
    for lag in sorted(set(WOODY_UPPER_BOUND_SENSITIVITY+(WOODY_MID_DIAGNOSTIC,))):
        aw=woody_from_lag(h['dates'],vi['ec']['A_terr'],lag)
        ah=[max(float(a)-float(w),0.0) for a,w in zip(vi['ec']['A_terr'],aw)]
        Awa=annual_support(h['dates'],aw,EVAL_YEARS,OBS_MONTHS); Aha=annual_support(h['dates'],ah,EVAL_YEARS,OBS_MONTHS)
        for i,y in enumerate(EVAL_YEARS):
            wrows.append({'lag_upper_bound_years':lag,'year':y,'A_terr_m2':vi['At'][i],'A_woody_diagnostic_m2':Awa[i],
                          'A_nonwoody_terr_m2':Aha[i],'woody_fraction_of_Aterr':0 if vi['At'][i]<=0 else Awa[i]/vi['At'][i]})

    flat=[]
    for z in scenarios:
        q={k:v for k,v in z.items() if k!='pred'}
        for i,y in enumerate(EVAL_YEARS):q[f'pred_{y}']=z['pred'][i]
        flat.append(q)
    pd.DataFrame(flat).to_csv(OUT/'stage94_four_scenarios_no_kh.csv',index=False)
    pd.DataFrame(profile).to_csv(OUT/'stage94_integrated_beta_profile.csv',index=False)
    pd.DataFrame(wrows).to_csv(OUT/'stage94_woody_substate_sensitivity.csv',index=False)
    pd.DataFrame([{'calibration_through':r['calibration_through'],'held_out_years':'/'.join(map(str,r['held_out_years'])),'beta_D':r['beta_D'],'train_RMSE_m2':r['train_RMSE_m2'],'holdout_RMSE_m2':r['holdout_RMSE_m2'],'holdout_nRMSE_pct':r['holdout_nRMSE_pct']} for r in temporal]).to_csv(OUT/'stage94_temporal_holdout_summary.csv',index=False)

    result={
      'status':'PASS_STAGE94_FALLBACK_NO_KH_ROUTE',
      'route_role':'publication-defensible fallback if exact TLMM transfer remains inadequate; not yet manuscript primary route',
      'observation_equation':'A_pred = A0 - A_terr - G_eff for Integrated; NO +KhH term',
      'short_term_observation_correction_removed':True,
      'central_peat_rate_mm_yr':PEAT,
      'four_scenarios':[{k:v for k,v in z.items() if k!='pred'} for z in sorted(scenarios,key=lambda q:q['rank'])],
      'integrated_full_fit':{'beta_D':bi,**mi},
      'integrated_nested_LOOCV':loocv['Integrated Model'],
      'integrated_fixed_origin_temporal_holdout':temporal,
      'integrated_beta_profile_intervals_nRMSE_plus_percentage_points':intervals,
      'woody_substate':{
        'open_water_equation_uses_Awoody_separately':False,
        'double_counting_prevented':True,
        'identity':'A_terr = A_nonwoody_terr + A_woody_diagnostic',
        'upper_bound_sensitivity_years':list(WOODY_UPPER_BOUND_SENSITIVITY),
        'midpoint_diagnostic_years':WOODY_MID_DIAGNOSTIC,
        'interpretation':'3/4/6 yr are upper-bound intervals from last confirmed inside-pond observation (2011) to estimated tree establishment (~2014/~2015/~2017), not exact exposure-to-establishment lags.',
        'intermediate_2013_2021_polygons_available_in_current_recovery':False,
        'lag_fitted_to_pond_area':False,
      },
      'site_independent_evidence':{
        'tree_age_distance':'Age = 5.283 + 1.760*Distance; r~0.957, R2~0.916, p~0.00272, n=6',
        'historical_spatial':'A1/B1/B2 locations are inside 2011 pond polygon; estimated establishment ~2015/~2017/~2014',
      },
      'mass_closure':{'mass_error_m3':h['mass_error'],'area_partition_error_m2':h['area_partition_error'],'precip_partition_error_m3':h['precip_partition_error']},
      'limitations':['beta_D remains an empirical time-series-estimated rate coefficient','n=6 scored pond-area years is small','2013/2015/2017/2019/2021 intermediate polygon geometries are not in the current recovery package, so exact tree exposure dates cannot yet be reconstructed'],
    }
    (OUT/'stage94_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
