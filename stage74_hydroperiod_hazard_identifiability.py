#!/usr/bin/env python3
"""Stage74 — identify whether the Stage73 hydroperiod-hazard rate is actually estimable.

The Stage73 best rule was a first-order persistent establishment hazard weighted
by daily exposed fraction.  Because K_colonizable is fitted simultaneously, the
hazard rate may be weakly identifiable.  This stage profiles the rate densely and
compares it with a parameter-free cumulative exposure-dose state.

No hydrologic or geomorphic parameter changes.  Accuracy/profile results are
outputs only.
"""
from __future__ import annotations

import csv, json, math
from pathlib import Path
from typing import List, Sequence

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_kernel import A0,EVAL_YEARS,OBS_MONTHS,SELECTED_STRUCTURE,annual_support,hydro,hydrologic_feature,mean_fsum
from eghm_deterministic_scenarios import fit_two_nonnegative_fixed,metrics_fixed,peat_geomorphic_loss,predict_fixed

OUT=Path('stage74_outputs'); OUT.mkdir(exist_ok=True)
OBS={2013:2154.430,2015:2147.678,2017:2051.218,2019:2045.159,2021:1965.256,2023:1882.700}
Y=[OBS[y] for y in EVAL_YEARS]
PEAT=0.38
RATES=[i/1000.0 for i in range(5,251,5)]  # 0.005..0.250 yr-1


def exposed(area): return [min(max((A0-float(a))/A0,0.0),1.0) for a in area]


def hazard_state(e,rate):
    rd=float(rate)/365.0; surv=1.0; out=[]
    for x in e:
        surv*=min(max(1.0-rd*float(x),0.0),1.0); out.append(1.0-surv)
    return out


def cumulative_exposure_years(e):
    acc=0.0; out=[]
    for x in e:
        acc += float(x)/365.0; out.append(acc)
    return out


def fit_basis(C,H,G,upper=None,train=None):
    if train is None: train=list(range(len(Y)))
    geom=[A0-float(G[i]) for i in range(len(Y))]; neg=[-float(x) for x in C]
    target=[float(Y[i])-geom[i] for i in train]
    b0,b1=fit_two_nonnegative_fixed([neg[i] for i in train],[H[i] for i in train],target,upper_first=upper)
    pred=predict_fixed(geom,neg,b0,H,b1); met=metrics_fixed(pred,Y)
    return b0,b1,pred,met


def loocv(C,H,G,upper=None):
    errs=[]
    for hold in range(len(Y)):
        train=[i for i in range(len(Y)) if i!=hold]
        _,_,pred,_=fit_basis(C,H,G,upper=upper,train=train)
        errs.append(float(pred[hold])-float(Y[hold]))
    rm=math.sqrt(math.fsum(x*x for x in errs)/len(errs))
    return rm,100.0*rm/mean_fsum(Y)


def aicc(rmse,n,k):
    if n-k-1<=0:return float('inf')
    return n*math.log(rmse*rmse)+2*k+(2*k*(k+1))/(n-k-1)


def main():
    F,_,_,_=deterministic_forcing(); P=dict(SELECTED_STRUCTURE); h=hydro(F,P)
    e=exposed(h['area']); H=hydrologic_feature(h['dates'],h['return_flow'],int(P['hydro_window_d']),EVAL_YEARS,OBS_MONTHS)
    Gd,_,_=peat_geomorphic_loss(h['dates'],h['V'],PEAT,P['V0'],P['p_shape']); G=annual_support(h['dates'],Gd,EVAL_YEARS,OBS_MONTHS)
    rows=[]
    for r in RATES:
        C=annual_support(h['dates'],hazard_state(e,r),EVAL_YEARS,OBS_MONTHS)
        kc,kh,pred,met=fit_basis(C,H,G,upper=A0)
        rows.append({'rate_yr':r,'RMSE_m2':met['RMSE_m2'],'nRMSE_pct':met['nRMSE_pct'],'K_colonizable_m2':kc,'K_hydro_m2_per_m3':kh,
                     'Kc_times_rate_m2_per_yr':kc*r,**{f'C_{y}':C[i] for i,y in enumerate(EVAL_YEARS)}})
    rows.sort(key=lambda z:(z['nRMSE_pct'],z['rate_yr']))
    best=rows[0]

    # No hazard-rate parameter: cumulative exposure dose in exposure-years.
    D=annual_support(h['dates'],cumulative_exposure_years(e),EVAL_YEARS,OBS_MONTHS)
    beta,kh,pred,met=fit_basis(D,H,G,upper=None)
    lrm,lnr=loocv(D,H,G,upper=None)
    linear={'state':'cumulative_exposure_years','RMSE_m2':met['RMSE_m2'],'nRMSE_pct':met['nRMSE_pct'],
            'beta_m2_per_exposure_year':beta,'K_hydro_m2_per_m3':kh,'LOOCV_RMSE_m2':lrm,'LOOCV_nRMSE_pct':lnr,
            'AICc_relative':aicc(met['RMSE_m2'],len(Y),2),**{f'D_{y}_exposure_yr':D[i] for i,y in enumerate(EVAL_YEARS)}}

    # Profile flatness around minimum.
    bnr=float(best['nRMSE_pct'])
    flat={}
    for tol in [0.001,0.005,0.01,0.05]:
        xs=[z['rate_yr'] for z in rows if z['nRMSE_pct']<=bnr+tol]
        flat[str(tol)]={'min_rate_yr':min(xs),'max_rate_yr':max(xs),'n_rates':len(xs)}
    bestC=annual_support(h['dates'],hazard_state(e,best['rate_yr']),EVAL_YEARS,OBS_MONTHS)
    hrm,hnr=loocv(bestC,H,G,upper=A0)
    best['LOOCV_RMSE_m2_fixed_rate']=hrm; best['LOOCV_nRMSE_pct_fixed_rate']=hnr
    best['AICc_relative_counting_rate_Kc_Kh']=aicc(best['RMSE_m2'],len(Y),3)

    with (OUT/'stage74_rate_profile.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    summary={'status':'PASS_STAGE74_IDENTIFIABILITY_PROFILE','pond_area_observation_2022':'ABSENT','hydrology_changed':False,'peat_rate_changed':False,
             'best_hazard':best,'rate_profile_flatness_pp':flat,'linear_cumulative_exposure':linear,
             'interpretation':'If a broad rate range has near-identical nRMSE while Kc compensates, the rate is weakly identifiable; cumulative exposure dose is the parsimonious no-rate comparator.',
             'physical_closure':{'mass_error_m3':h['mass_error'],'area_partition_error_m2':h['area_partition_error'],'precip_partition_error_m3':h['precip_partition_error']}}
    (OUT/'stage74_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
