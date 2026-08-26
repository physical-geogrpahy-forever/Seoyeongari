#!/usr/bin/env python3
import json, itertools
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing, sim, OBS

OUT=Path('stage31c_outputs'); OUT.mkdir(exist_ok=True)
YEARS=np.array(sorted(OBS),dtype=int)
Y=np.array([OBS[int(y)] for y in YEARS],dtype=float)
A2011=2241.762

# Stage31 neighborhood chosen to retain a reasonably shaped hydrologic signal.
HYDRO_GRID={
 'm_area':[0.6,0.8,1.0,1.2,1.5],
 'q0':[32,48,64,96],
 'm_q':[0.4,0.6,0.8,1.0],
 'local_frac':[0.1,0.2,0.3],
 'fast_frac':[0.25,0.5,0.75],
 'tau_fast':[30.,60.],
 'tau_slow':[365.,730.]
}

SEASONS={
 'annual':set(range(1,13)),
 'mar_oct':set(range(3,11)),
 'apr_oct':set(range(4,11)),
 'may_sep':set(range(5,10)),
}
MEMORY=[0.80,0.90,0.95,0.975,0.99,1.0]
POWER=[0.5,1.0,1.5,2.0]


def fit3(hydro, state):
    X=np.c_[np.ones(len(Y)), hydro, state]
    b=np.linalg.lstsq(X,Y,rcond=None)[0]
    pred=X@b
    rm=float(np.sqrt(np.mean((pred-Y)**2))); nrm=rm/Y.mean()*100; mae=float(np.mean(np.abs(pred-Y)))
    # LOOCV only diagnostic, not selection metric.
    cv=[]
    for i in range(len(Y)):
        keep=np.arange(len(Y))!=i
        bb=np.linalg.lstsq(X[keep],Y[keep],rcond=None)[0]
        cv.append(float(X[i]@bb))
    cv=np.array(cv); rcv=float(np.sqrt(np.mean((cv-Y)**2))); ncv=rcv/Y.mean()*100
    return b,pred,rm,nrm,mae,cv,rcv,ncv


def annual_hydro_and_exposure(daily, season, power):
    d=daily.copy(); d['date']=pd.to_datetime(d['date']); d['year']=d.date.dt.year; d['month']=d.date.dt.month
    # Potential colonization driver: fraction of the 2011 open-water footprint not inundated.
    deficit=np.maximum(0.,(A2011-d.area_m2.to_numpy(float))/A2011)**power
    # Flooding can oppose establishment; keep a separate diagnostic, not mandatory in the first state equation.
    excess=np.maximum(0.,(d.area_m2.to_numpy(float)-A2011)/A2011)**power
    d['deficit']=deficit; d['excess']=excess
    use=d[d.month.isin(SEASONS[season])]
    exp=use.groupby('year').deficit.mean().to_dict(); inund=use.groupby('year').excess.mean().to_dict()
    hydro=d[d.month.isin([5,6])].groupby('year').area_m2.mean().to_dict()
    return hydro,exp,inund


def build_state(exp, inund, memory, flood_reversal):
    # C is a dimensionless persistent colonization/exposure state. It has no calendar-time input.
    C=0.; out={}
    for y in range(2011,2024):
        e=float(exp.get(y,0.)); w=float(inund.get(y,0.))
        C=max(0., memory*C + e - flood_reversal*w)
        if y in OBS: out[y]=C
    return np.array([out[int(y)] for y in YEARS],dtype=float)


def main():
    F,missing,annual=forcing()
    combos=list(itertools.product(*HYDRO_GRID.values()))
    names=list(HYDRO_GRID.keys())
    rows=[]; best=None
    # Keep runtime bounded: each hydrologic run yields daily states then many ecological operators are evaluated cheaply.
    for j,vals in enumerate(combos):
        p=dict(zip(names,vals))
        r,daily=sim(F,p,True)
        raw=np.array([r['pred'][int(y)] for y in YEARS],dtype=float)
        # Reject only numerical pathologies; ecological behavior is not yet a selection constraint.
        if not np.all(np.isfinite(raw)): continue
        for season,power in itertools.product(SEASONS,POWER):
            hydro,exp,inund=annual_hydro_and_exposure(daily,season,power)
            h=np.array([hydro[int(y)] for y in YEARS],dtype=float)
            for memory,flood_rev in itertools.product(MEMORY,[0.,0.25,0.5,1.0]):
                state=build_state(exp,inund,memory,flood_rev)
                b,pred,rm,nrm,mae,cv,rcv,ncv=fit3(h,state)
                item={
                    'nrmse':nrm,'rmse':rm,'mae':mae,'loocv_nrmse':ncv,'loocv_rmse':rcv,
                    'season':season,'power':power,'memory':memory,'flood_reversal':flood_rev,
                    **p,
                    'beta0':float(b[0]),'beta_hydro':float(b[1]),'beta_state':float(b[2]),
                    'raw_nrmse':r['nrmse'],'raw_rmse':r['rmse'],'raw_dry_days':r['dry_days'],
                    'state_2013':float(state[0]),'state_2023':float(state[-1]),
                    **{f'raw_{y}':float(h[i]) for i,y in enumerate(YEARS)},
                    **{f'pred_{y}':float(pred[i]) for i,y in enumerate(YEARS)},
                    **{f'cv_{y}':float(cv[i]) for i,y in enumerate(YEARS)},
                }
                rows.append(item)
                if best is None or nrm<best['nrmse']:
                    best=item.copy(); best['_daily']=daily; best['_hydro_result']=r
    rows.sort(key=lambda x:x['nrmse'])
    pd.DataFrame(rows[:500]).to_csv(OUT/'stage31c_top500.csv',index=False)
    # Best without direct time term.
    bclean={k:v for k,v in best.items() if not k.startswith('_')}
    best['_daily'].to_csv(OUT/'stage31c_best_daily_raw_hydrology.csv',index=False)
    summary={
      'objective':'retain Stage31B accuracy while replacing explicit calendar-time trend with hydroperiod/exposure state',
      'best':bclean,
      'benchmarks':{'stage26_nrmse_pct':8.008034,'stage31_nrmse_pct':11.77377869600642,'stage31b_linear_nrmse_pct':0.7692692574776534,'stage31b_linear_loocv_nrmse_pct':1.266132430355888},
      'state_equation':'C_y = max(0, memory*C_(y-1) + mean[(max(0,(A2011-Ahydro)/A2011))^power] - flood_reversal*mean[(max(0,(Ahydro-A2011)/A2011))^power])',
      'observation_operator':'A_cal = beta0 + beta_hydro*A_hydro(May-Jun) + beta_state*C',
      'rules':{'explicit_time_term':False,'lambda':0,'DSM':False,'bathymetry':False,'hard_2011_cap':False,'selection_metric':'in-sample nRMSE; LOOCV diagnostic only'},
      'forcing_rows':len(F['pre']),'raw_missing':missing,'annual_precip_mm':annual,
    }
    (OUT/'stage31c_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
