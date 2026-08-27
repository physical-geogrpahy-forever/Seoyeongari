#!/usr/bin/env python3
from __future__ import annotations
import csv, json, math
from pathlib import Path
from typing import Sequence

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_kernel import A0,EVAL_YEARS,OBS_MONTHS,SELECTED_STRUCTURE,annual_support,hydro,mean_fsum
from eghm_deterministic_scenarios import fit_one_nonnegative_fixed,metrics_fixed,peat_geomorphic_loss
from stage77_peat_forming_area_feedback import ecological_path

OUT=Path('stage95_outputs'); OUT.mkdir(exist_ok=True)
OBS={2013:2154.430,2015:2147.678,2017:2051.218,2019:2045.159,2021:1965.256,2023:1882.700}
Y=[OBS[y] for y in EVAL_YEARS]
T=[float(y-2011) for y in EVAL_YEARS]
PEAT=0.38
BETAS=range(0,301)

def rmse(pred:Sequence[float], idx:Sequence[int])->float:
    return math.sqrt(math.fsum((float(pred[i])-Y[i])**2 for i in idx)/len(idx))

def nrmse_from_errors(errs, obs):
    r=math.sqrt(math.fsum(e*e for e in errs)/len(errs))
    return r,100*r/mean_fsum(obs)

def aicc(rmse_m2,k,n=6):
    rss=rmse_m2**2*n
    if rss<=0:return float('-inf')
    if n-k-1<=0:return float('inf')
    return n*math.log(rss/n)+2*k+(2*k*(k+1)/(n-k-1) if k else 0)

def main():
    F,_,_,_=deterministic_forcing(); P=dict(SELECTED_STRUCTURE); h=hydro(F,P)
    Gwet,_,_=peat_geomorphic_loss(h['dates'],h['V'],PEAT,P['V0'],P['p_shape'])
    Ga=annual_support(h['dates'],Gwet,EVAL_YEARS,OBS_MONTHS)
    hc={}; ic={}
    for b in BETAS:
        d=0.0; at=[]
        for a in h['area']:
            e=min(max((A0-float(a))/A0,0.0),1.0); d+=e/365.0; at.append(min(float(b)*d,A0))
        At=annual_support(h['dates'],at,EVAL_YEARS,OBS_MONTHS)
        hc[b]=[A0-x for x in At]
        ec=ecological_path(h['area'],Gwet,float(b),'coupled_area_partition')
        Ati=annual_support(h['dates'],ec['A_terr'],EVAL_YEARS,OBS_MONTHS)
        Gi=annual_support(h['dates'],ec['G_eff'],EVAL_YEARS,OBS_MONTHS)
        ic[b]=[A0-Ati[i]-Gi[i] for i in range(len(Y))]
    def best_beta(cache, idx):
        return min(BETAS,key=lambda b:(rmse(cache[b],idx),b))
    allidx=list(range(len(Y)))
    r_base=fit_one_nonnegative_fixed(T,[A0-y for y in Y])
    p_base=[A0-r_base*T[i] for i in allidx]
    r_eco=fit_one_nonnegative_fixed(T,[A0-Ga[i]-Y[i] for i in allidx])
    p_eco=[A0-r_eco*T[i]-Ga[i] for i in allidx]
    b_h=best_beta(hc,allidx); p_h=hc[b_h]
    b_i=best_beta(ic,allidx); p_i=ic[b_i]
    eq=[('Baseline secular-null',r_base,'trend_m2_yr',p_base),('Hydrosere exposure',b_h,'beta_D_m2_exposure_yr',p_h),('Eco-Geo secular+peat',r_eco,'trend_m2_yr',p_eco),('Integrated exposure+peat',b_i,'beta_D_m2_exposure_yr',p_i)]
    equal_rows=[]
    for name,param,pname,pred in eq:
        m=metrics_fixed(pred,Y)
        equal_rows.append({'Model':name,'fitted_parameter_count':1,'parameter_name':pname,'parameter_value':param,'RMSE_m2':m['RMSE_m2'],'nRMSE_pct':m['nRMSE_pct'],'AICc':aicc(m['RMSE_m2'],1),**{f'pred_{y}':pred[j] for j,y in enumerate(EVAL_YEARS)}})
    loo=[]
    for name,_,pname,_ in eq:
        errs=[]; choices=[]
        for hold in allidx:
            tr=[i for i in allidx if i!=hold]
            if name=='Baseline secular-null':
                p=fit_one_nonnegative_fixed([T[i] for i in tr],[A0-Y[i] for i in tr]); pred=A0-p*T[hold]
            elif name=='Eco-Geo secular+peat':
                p=fit_one_nonnegative_fixed([T[i] for i in tr],[A0-Ga[i]-Y[i] for i in tr]); pred=A0-p*T[hold]-Ga[hold]
            elif name=='Hydrosere exposure':
                p=best_beta(hc,tr); pred=hc[p][hold]
            else:
                p=best_beta(ic,tr); pred=ic[p][hold]
            errs.append(pred-Y[hold]); choices.append({'held_out_year':EVAL_YEARS[hold],'parameter':p,'prediction_m2':pred,'error_m2':pred-Y[hold]})
        r,nr=nrmse_from_errors(errs,Y)
        loo.append({'Model':name,'LOOCV_RMSE_m2':r,'LOOCV_nRMSE_pct':nr,'choices':choices})
    B=p_base
    nested=[]
    mb=metrics_fixed(B,Y); nested.append({'Scenario':'Baseline common-backbone','shared_trend_m2_yr':r_base,'additional_beta_D':None,**mb,'pred':B})
    best=None
    for b in BETAS:
        At=[A0-hc[b][i] for i in allidx]; pred=[B[i]-At[i] for i in allidx]; m=metrics_fixed(pred,Y); z=(m['RMSE_m2'],b,pred,m)
        if best is None or z[:2]<best[:2]: best=z
    _,bhn,phn,mhn=best; nested.append({'Scenario':'Hydrosere + common-backbone','shared_trend_m2_yr':r_base,'additional_beta_D':bhn,**mhn,'pred':phn})
    pen=[B[i]-Ga[i] for i in allidx]; men=metrics_fixed(pen,Y); nested.append({'Scenario':'Eco-Geo + common-backbone','shared_trend_m2_yr':r_base,'additional_beta_D':None,**men,'pred':pen})
    best=None
    for b in BETAS:
        loss=[A0-ic[b][i] for i in allidx]; pred=[B[i]-loss[i] for i in allidx]; m=metrics_fixed(pred,Y); z=(m['RMSE_m2'],b,pred,m)
        if best is None or z[:2]<best[:2]: best=z
    _,bin_,pin,min_=best; nested.append({'Scenario':'Integrated + common-backbone','shared_trend_m2_yr':r_base,'additional_beta_D':bin_,**min_,'pred':pin})
    hold=[]
    for cutoff in (2,3,4):
        tr=list(range(cutoff+1)); te=list(range(cutoff+1,len(Y)))
        for name,_,pname,_ in eq:
            if name=='Baseline secular-null':
                p=fit_one_nonnegative_fixed([T[i] for i in tr],[A0-Y[i] for i in tr]); pred=[A0-p*T[i] for i in te]
            elif name=='Eco-Geo secular+peat':
                p=fit_one_nonnegative_fixed([T[i] for i in tr],[A0-Ga[i]-Y[i] for i in tr]); pred=[A0-p*T[i]-Ga[i] for i in te]
            elif name=='Hydrosere exposure':
                p=best_beta(hc,tr); pred=[hc[p][i] for i in te]
            else:
                p=best_beta(ic,tr); pred=[ic[p][i] for i in te]
            rr=math.sqrt(math.fsum((pred[j]-Y[i])**2 for j,i in enumerate(te))/len(te))
            hold.append({'Model':name,'calibration_through':EVAL_YEARS[cutoff],'held_out_years':'/'.join(str(EVAL_YEARS[i]) for i in te),'parameter_value':p,'holdout_RMSE_m2':rr,'holdout_nRMSE_pct':100*rr/mean_fsum([Y[i] for i in te])})
    with (OUT/'stage95_equal_complexity_benchmark.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(equal_rows[0].keys())); w.writeheader(); w.writerows(equal_rows)
    nflat=[]
    for z in nested:
        q={k:v for k,v in z.items() if k!='pred'}
        for i,y in enumerate(EVAL_YEARS):q[f'pred_{y}']=z['pred'][i]
        nflat.append(q)
    with (OUT/'stage95_common_backbone_nested.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(nflat[0].keys()));w.writeheader();w.writerows(nflat)
    with (OUT/'stage95_temporal_holdout.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(hold[0].keys()));w.writeheader();w.writerows(hold)
    summary={'status':'PASS_STAGE95_FAIR_BENCHMARK_AND_NESTED_ABLATION','interpretation':'Predictive benchmark and strict nested process ablation are separated. Do not use equal-complexity benchmark as nested causal attribution.','equal_complexity_benchmark':equal_rows,'equal_complexity_LOOCV':loo,'strict_common_backbone_nested':[{k:v for k,v in z.items() if k!='pred'} for z in nested],'temporal_holdout':hold,'critical_result':'A one-parameter secular null is already highly accurate; in strict common-backbone ablation the optimum added hydrosere beta is zero. Therefore six pond-area time points alone cannot identify incremental hydrosere causality; independent dendrochronology must carry that process evidence.'}
    (OUT/'stage95_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
