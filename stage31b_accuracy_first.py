#!/usr/bin/env python3
import itertools, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing, sim, OBS

OUT=Path('stage31b_outputs'); OUT.mkdir(exist_ok=True)
YEARS=np.array(sorted(OBS),dtype=int)
Y=np.array([OBS[int(y)] for y in YEARS],dtype=float)
T=(YEARS-2011).astype(float)
PRED_COLS=[f'p{y}' for y in YEARS]

def fit_operator(pred, quadratic=False):
    pred=np.asarray(pred,dtype=float)
    X=np.c_[np.ones(len(pred)), pred, T]
    if quadratic:
        X=np.c_[X,T*T]
    beta=np.linalg.lstsq(X,Y,rcond=None)[0]
    fit=X@beta
    rmse=float(np.sqrt(np.mean((fit-Y)**2)))
    nrmse=float(rmse/Y.mean()*100)
    mae=float(np.mean(np.abs(fit-Y)))
    # leave-one-out diagnostic; selection remains in-sample nRMSE because this is the accuracy-first stage.
    cv=[]
    for i in range(len(Y)):
        keep=np.arange(len(Y))!=i
        b=np.linalg.lstsq(X[keep],Y[keep],rcond=None)[0]
        cv.append(float(X[i]@b))
    cv=np.asarray(cv)
    cv_rmse=float(np.sqrt(np.mean((cv-Y)**2)))
    cv_nrmse=float(cv_rmse/Y.mean()*100)
    return {'beta':beta.tolist(),'pred':fit.tolist(),'rmse':rmse,'nrmse':nrmse,'mae':mae,'loocv_pred':cv.tolist(),'loocv_rmse':cv_rmse,'loocv_nrmse':cv_nrmse}

def trend_only():
    X=np.c_[np.ones(len(Y)),T]
    b=np.linalg.lstsq(X,Y,rcond=None)[0]; p=X@b
    rm=float(np.sqrt(np.mean((p-Y)**2)))
    return {'beta':b.tolist(),'pred':p.tolist(),'rmse':rm,'nrmse':float(rm/Y.mean()*100)}

def row_from_candidate(p,r,op,quad=False):
    row={**p,'hydro_nrmse':r['nrmse'],'hydro_rmse':r['rmse'],'operator':'quadratic_time' if quad else 'linear_time',
         'cal_rmse':op['rmse'],'cal_nrmse':op['nrmse'],'cal_mae':op['mae'],'loocv_rmse':op['loocv_rmse'],'loocv_nrmse':op['loocv_nrmse']}
    for j,b in enumerate(op['beta']): row[f'beta{j}']=b
    for j,y in enumerate(YEARS):
        row[f'hydro_{y}']=r['pred'][int(y)]; row[f'cal_{y}']=op['pred'][j]; row[f'cv_{y}']=op['loocv_pred'][j]
    return row

def main():
    F,missing,annual=forcing()
    # Phase A: broaden VSA hydrology but keep perched-return structure fixed.
    coarse=[]
    for ma,q0,mq in itertools.product([.20,.30,.50,.75,1.0,1.25,1.5,2.0,3.0],[8,16,24,32,48,64,96,128,192],[.20,.30,.40,.50,.60,.80,1.0,1.2,1.6,2.0]):
        p={'m_area':ma,'q0':q0,'m_q':mq,'local_frac':.20,'fast_frac':.75,'tau_fast':60.,'tau_slow':365.}
        r,_=sim(F,p)
        hp=[r['pred'][int(y)] for y in YEARS]
        op=fit_operator(hp,False); oq=fit_operator(hp,True)
        coarse.append((op['nrmse'],p,r,op,oq))
    coarse.sort(key=lambda x:x[0])
    pd.DataFrame([row_from_candidate(p,r,op,False) for _,p,r,op,oq in coarse[:100]]).to_csv(OUT/'coarse_linear_top100.csv',index=False)
    # Hydrology seeds chosen by calibrated accuracy, not by ecological criteria.
    seeds=[]
    for _,p,_,_,_ in coarse:
        key=(p['m_area'],p['q0'],p['m_q'])
        if key not in seeds: seeds.append(key)
        if len(seeds)>=25: break
    fine=[]
    for (ma,q0,mq),loc,ff,tf,ts in itertools.product(seeds,[.05,.10,.20,.30,.40],[.10,.25,.50,.75,.90],[15.,30.,60.,120.],[180.,365.,730.,1460.]):
        p={'m_area':ma,'q0':q0,'m_q':mq,'local_frac':loc,'fast_frac':ff,'tau_fast':tf,'tau_slow':ts}
        r,_=sim(F,p); hp=[r['pred'][int(y)] for y in YEARS]
        op=fit_operator(hp,False); oq=fit_operator(hp,True)
        fine.append((op['nrmse'],p,r,op,oq))
    fine.sort(key=lambda x:x[0])
    linear=fine[0]
    # Quadratic-time optimum from the same fine set, reported separately as a more flexible calibration ceiling.
    qbest=min(fine,key=lambda x:x[4]['nrmse'])
    pd.DataFrame([row_from_candidate(p,r,op,False) for _,p,r,op,oq in fine[:200]]).to_csv(OUT/'fine_linear_top200.csv',index=False)
    qsorted=sorted(fine,key=lambda x:x[4]['nrmse'])
    pd.DataFrame([row_from_candidate(p,r,oq,True) for _,p,r,op,oq in qsorted[:200]]).to_csv(OUT/'fine_quadratic_top200.csv',index=False)

    def pack(item,quad=False):
        _,p,r,op,oq=item; o=oq if quad else op
        return {'hydrology_params':p,'raw_hydrology':r,'operator':{'form':'A_cal = beta0 + beta1*A_hydro + beta2*t' + (' + beta3*t^2' if quad else ''),'beta':o['beta']},
                'calibrated':{'pred':{str(y):o['pred'][i] for i,y in enumerate(YEARS)},'rmse':o['rmse'],'nrmse':o['nrmse'],'mae':o['mae']},
                'loocv':{'pred':{str(y):o['loocv_pred'][i] for i,y in enumerate(YEARS)},'rmse':o['loocv_rmse'],'nrmse':o['loocv_nrmse']}}
    summary={'objective':'accuracy first; ecological/dry-day constraints intentionally not used for selection',
             'observations_m2':{str(k):v for k,v in OBS.items()},'trend_only':trend_only(),
             'linear_time_best':pack(linear,False),'quadratic_time_best':pack(qbest,True),
             'benchmark_stage26_nrmse_pct':8.008034,'benchmark_stage31_nrmse_pct':11.77377869600642,
             'forcing_rows':len(F['pre']),'raw_missing':missing,'annual_precip_mm':annual,
             'rules':{'lambda':0,'DSM':False,'bathymetry':False,'hard_2011_cap':False,'selection_metric':'in-sample nRMSE only'}}
    (OUT/'stage31b_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
