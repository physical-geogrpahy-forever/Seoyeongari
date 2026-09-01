#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path
import pandas as pd

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_kernel import A0,EVAL_YEARS,OBS_MONTHS,SELECTED_STRUCTURE,annual_support,hydro,hydrologic_feature,mean_fsum
from eghm_deterministic_scenarios import fit_one_nonnegative_fixed,metrics_fixed,peat_geomorphic_loss,predict_fixed
from stage77_peat_forming_area_feedback import ecological_path

OUT=Path('stage93_outputs'); OUT.mkdir(exist_ok=True)
OBS={2013:2154.430,2015:2147.678,2017:2051.218,2019:2045.159,2021:1965.256,2023:1882.700}
Y=[OBS[y] for y in EVAL_YEARS]
PEAT=0.38
BETAS=list(range(0,301))
SITE_LAGS=(3,4,6)
MID_LAG=5


def fit_offset_train(offset,H,train):
    kh=fit_one_nonnegative_fixed([H[i] for i in train],[Y[i]-offset[i] for i in train])
    pred=predict_fixed(offset,H,kh)
    return kh,pred


def rmse_indices(pred, idx):
    return math.sqrt(sum((pred[i]-Y[i])**2 for i in idx)/len(idx))


def woody_from_lag(dates, aterr, lag_years):
    s=pd.Series([float(v) for v in aterr],index=pd.to_datetime(dates))
    vals=[]
    for dt in s.index:
        past=dt-pd.DateOffset(years=int(lag_years))
        j=s.index.searchsorted(past,side='right')-1
        vals.append(0.0 if j<0 else float(s.iloc[j]))
    return vals


def main():
    F,_,_,_=deterministic_forcing(); P=dict(SELECTED_STRUCTURE); h=hydro(F,P)
    H=hydrologic_feature(h['dates'],h['return_flow'],int(P['hydro_window_d']),EVAL_YEARS,OBS_MONTHS)
    Gwet,_,_=peat_geomorphic_loss(h['dates'],h['V'],PEAT,P['V0'],P['p_shape'])

    cache={}
    for b in BETAS:
        ec=ecological_path(h['area'],Gwet,float(b),'coupled_area_partition')
        At=annual_support(h['dates'],ec['A_terr'],EVAL_YEARS,OBS_MONTHS)
        G=annual_support(h['dates'],ec['G_eff'],EVAL_YEARS,OBS_MONTHS)
        D=annual_support(h['dates'],ec['D'],EVAL_YEARS,OBS_MONTHS)
        off=[A0-At[i]-G[i] for i in range(len(Y))]
        cache[b]=(ec,At,G,D,off)

    full=[]
    for b in BETAS:
        ec,At,G,D,off=cache[b]
        kh,pred=fit_offset_train(off,H,list(range(len(Y))))
        m=metrics_fixed(pred,Y)
        full.append((m['RMSE_m2'],b,kh,pred,m,At,G,D))
    best=min(full,key=lambda x:(x[0],x[1]))
    _,bestb,bestkh,bestpred,bestmet,bAt,bG,bD=best

    frows=[]; ferr=[]
    for hold in (3,4,5):
        train=list(range(hold))
        cand=[]
        for b in BETAS:
            off=cache[b][4]
            kh,pred=fit_offset_train(off,H,train)
            trrm=rmse_indices(pred,train)
            cand.append((trrm,b,kh,pred))
        trrm,b,kh,pred=min(cand,key=lambda x:(x[0],x[1]))
        err=pred[hold]-Y[hold]; ferr.append(err)
        frows.append({'target_year':EVAL_YEARS[hold],
                      'training_years':'/'.join(str(EVAL_YEARS[i]) for i in train),
                      'beta_D_m2_per_exposure_yr':b,'K_hydro_m2_per_m3':kh,
                      'train_RMSE_m2':trrm,'prediction_m2':pred[hold],
                      'observation_m2':Y[hold],'error_m2':err})
    frmse=math.sqrt(sum(e*e for e in ferr)/len(ferr)); fnrmse=100*frmse/mean_fsum([Y[i] for i in (3,4,5)])

    ec=cache[bestb][0]
    wrows=[]
    lagset=sorted(set(SITE_LAGS+(MID_LAG,)))
    for lag in lagset:
        Aw=woody_from_lag(h['dates'],ec['A_terr'],lag)
        Ah=[max(float(a)-float(w),0.0) for a,w in zip(ec['A_terr'],Aw)]
        aw=annual_support(h['dates'],Aw,EVAL_YEARS,OBS_MONTHS)
        ah=annual_support(h['dates'],Ah,EVAL_YEARS,OBS_MONTHS)
        at=annual_support(h['dates'],ec['A_terr'],EVAL_YEARS,OBS_MONTHS)
        for i,y in enumerate(EVAL_YEARS):
            wrows.append({'lag_years':lag,'year':y,'A_terr_m2':at[i],
                          'A_woody_m2':aw[i],'A_herbaceous_transition_m2':ah[i],
                          'woody_fraction_of_Aterr':0.0 if at[i]<=0 else aw[i]/at[i]})

    pd.DataFrame(frows).to_csv(OUT/'stage93_forward_validation.csv',index=False)
    pd.DataFrame(wrows).to_csv(OUT/'stage93_woody_cohort_sensitivity.csv',index=False)
    pd.DataFrame([{'year':y,'pred_m2':bestpred[i],'obs_m2':Y[i],'error_m2':bestpred[i]-Y[i],
                   'Aterr_m2':bAt[i],'G_eff_m2':bG[i],'D_exposure_yr':bD[i]}
                  for i,y in enumerate(EVAL_YEARS)]).to_csv(OUT/'stage93_full_fit_predictions.csv',index=False)

    out={'status':'PASS_STAGE93_STAGE78_TEMPORAL_WOODY_VALIDATION',
         'full_fit':{'beta_D':bestb,'K_hydro':bestkh,**bestmet},
         'forward_validation':{'targets':[2019,2021,2023],'RMSE_m2':frmse,'nRMSE_pct':fnrmse,'rows':frows},
         'woody_succession':{
             'pond_area_equation_changed':False,
             'woody_double_counting_in_open_water_loss':False,
             'definition':'Aterr is total persistent terrestrialized area; Awoody is the lagged cohort subset; Aherb=Aterr-Awoody.',
             'site_informed_lag_sensitivity_years':list(SITE_LAGS),
             'midpoint_diagnostic_lag_years':MID_LAG,
             'lag_used_for_parameter_fitting':False,
             'lag_used_to_change_pond_area_accuracy':False,
             'site_evidence':'A1/B1/B2 are inside the 2011 pond polygon and estimated establishment years are ~2015/~2017/~2014, respectively; exact first exposure dates are unknown, so no exact lag is claimed.'
         },
         'mass_closure':{'mass_error_m3':h['mass_error'],'area_partition_error_m2':h['area_partition_error'],'precip_partition_error_m3':h['precip_partition_error']}}
    (OUT/'stage93_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
