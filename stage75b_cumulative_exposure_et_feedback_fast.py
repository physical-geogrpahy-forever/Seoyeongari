#!/usr/bin/env python3
"""Stage75b — cached execution of the exact Stage75 ET-feedback experiment.

Scientific equations, literature Kterr anchors, beta grid, peat rate and data
contract are identical to Stage75. The only change is computational: each daily
hydrologic trajectory is computed once and reused for nested LOOCV fitting.
"""
from __future__ import annotations
import csv,json,math
from pathlib import Path

import stage75_cumulative_exposure_et_feedback as s
from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_kernel import A0,EVAL_YEARS,OBS_MONTHS,SELECTED_STRUCTURE,annual_support,hydrologic_feature,mean_fsum
from eghm_deterministic_scenarios import fit_one_nonnegative_fixed,metrics_fixed,peat_geomorphic_loss,predict_fixed

OUT=Path('stage75b_outputs');OUT.mkdir(exist_ok=True)


def state(F,P,beta,kterr):
    h=s.hydro_feedback(F,P,beta,kterr)
    Aterr=annual_support(h['dates'],h['A_terr'],EVAL_YEARS,OBS_MONTHS)
    H=hydrologic_feature(h['dates'],h['return_flow'],int(P['hydro_window_d']),EVAL_YEARS,OBS_MONTHS)
    Gd,_,_=peat_geomorphic_loss(h['dates'],h['V'],s.PEAT,P['V0'],P['p_shape'])
    G=annual_support(h['dates'],Gd,EVAL_YEARS,OBS_MONTHS)
    return h,Aterr,H,G


def fit_cached(Aterr,H,G,train=None):
    if train is None:train=list(range(len(s.Y)))
    offset=[A0-Aterr[i]-G[i] for i in range(len(s.Y))]
    kh=fit_one_nonnegative_fixed([H[i] for i in train],[s.Y[i]-offset[i] for i in train])
    pred=predict_fixed(offset,H,kh);met=metrics_fixed(pred,s.Y)
    return kh,pred,met


def main():
    F,_,_,_=deterministic_forcing();P=dict(SELECTED_STRUCTURE)
    candidates={};rows=[]
    for kt in s.KTERR_ANCHORS:
        coarse=[]
        for b in s.BETA_COARSE:
            st=state(F,P,b,kt);kh,pred,met=fit_cached(st[1],st[2],st[3])
            coarse.append((met['nRMSE_pct'],b,st,kh,pred,met))
        cb=min(coarse,key=lambda z:(z[0],z[1]))[1]
        fine=sorted(set(max(0.0,cb+d) for d in range(-10,11)))
        for b in fine:
            st=state(F,P,b,kt);kh,pred,met=fit_cached(st[1],st[2],st[3]);candidates[(kt,b)]=st
            rows.append({'K_terr':kt,'beta_m2_per_exposure_yr':b,'RMSE_m2':met['RMSE_m2'],'nRMSE_pct':met['nRMSE_pct'],
                         'K_hydro_m2_per_m3':kh,'Aterr_2023_m2':st[1][-1],**{f'pred_{y}':pred[i] for i,y in enumerate(EVAL_YEARS)}})
    rows.sort(key=lambda r:(r['nRMSE_pct'],r['K_terr'],r['beta_m2_per_exposure_yr']))
    best=rows[0];nofb=min((r for r in rows if r['K_terr']==1.0),key=lambda r:r['nRMSE_pct'])

    errs=[];choices=[]
    for hold in range(len(s.Y)):
        train=[i for i in range(len(s.Y)) if i!=hold];tested=[]
        for r in rows:
            st=candidates[(r['K_terr'],r['beta_m2_per_exposure_yr'])]
            kh,pred,_=fit_cached(st[1],st[2],st[3],train)
            trm=metrics_fixed([pred[i] for i in train],[s.Y[i] for i in train])
            tested.append((trm['RMSE_m2'],r['K_terr'],r['beta_m2_per_exposure_yr'],pred[hold],kh))
        z=min(tested,key=lambda q:(q[0],q[1],q[2]));errs.append(z[3]-s.Y[hold])
        choices.append({'held_out_year':EVAL_YEARS[hold],'K_terr':z[1],'beta_m2_per_exposure_yr':z[2],'K_hydro_m2_per_m3':z[4]})
    lrm=math.sqrt(math.fsum(x*x for x in errs)/len(errs));lnr=100*lrm/mean_fsum(s.Y)

    with (OUT/'stage75b_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    hbest=candidates[(best['K_terr'],best['beta_m2_per_exposure_yr'])][0]
    result={'status':'PASS_STAGE75B_REFERENCE_BOUNDED_ET_FEEDBACK_TEST','pond_area_observation_2022':'ABSENT',
            'scientific_equations_identical_to_stage75':True,'wetland_reference_Kc':s.KWET,
            'tested_Kterr_literature_anchors':s.KTERR_ANCHORS,'peat_rate_mm_yr':s.PEAT,
            'best_full_six_year':best,'no_ET_contrast_Kterr_1':nofb,
            'best_implies_ET_increase_relative_to_current_wetland':best['K_terr']>s.KWET,
            'best_implies_ET_decrease_relative_to_current_wetland':best['K_terr']<s.KWET,
            'nested_LOOCV_RMSE_m2':lrm,'nested_LOOCV_nRMSE_pct':lnr,'nested_LOOCV_choices':choices,
            'references':[
                {'citation':'Pereira, Paredes & Espirito-Santo 2024','doi':'10.1007/s00271-024-00923-9'},
                {'citation':'Drexler et al. 2004','doi':'10.1002/hyp.1462'},
                {'citation':'Mohamed et al. 2012','doi':'10.1016/j.pce.2011.08.005'}],
            'physical_closure':{'mass_error_m3':hbest['mass_error'],'area_partition_error_m2':hbest['area_partition_error'],'precip_partition_error_m3':hbest['precip_partition_error']}}
    (OUT/'stage75b_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
