#!/usr/bin/env python3
import json,itertools
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing,sim,OBS

OUT=Path('stage31c_fast_outputs'); OUT.mkdir(exist_ok=True)
YEARS=np.array(sorted(OBS),int); Y=np.array([OBS[int(y)] for y in YEARS],float); AREF=2241.762
HYDRO={
 'm_area':[0.8,1.0,1.2,1.5], 'q0':[48,64,96], 'm_q':[0.4,0.6,0.8,1.0],
 'local_frac':[0.1,0.2,0.3], 'fast_frac':[0.25,0.5,0.75], 'tau_fast':[30.,60.], 'tau_slow':[365.,730.]}
SEASONS={'annual':range(1,13),'mar_oct':range(3,11),'apr_oct':range(4,11),'may_sep':range(5,10)}
POWERS=[0.5,1.,1.5,2.]; MEM=[0.8,0.9,0.95,0.975,0.99,1.0]; REV=[0.,0.25,0.5,1.]

def fit_constrained(h,s,y=Y):
    # Ecological sign constraints: more hydrologic water cannot reduce open water (bh>=0),
    # and greater persistent exposure/colonization state cannot increase it (bs<=0).
    cand=[]
    X=np.c_[np.ones(len(y)),h,s]; b=np.linalg.lstsq(X,y,rcond=None)[0]
    if b[1]>=0 and b[2]<=0: cand.append(b)
    # active-set boundaries
    Xh=np.c_[np.ones(len(y)),h]; bh=np.linalg.lstsq(Xh,y,rcond=None)[0]
    if bh[1]>=0: cand.append(np.array([bh[0],bh[1],0.]))
    Xs=np.c_[np.ones(len(y)),s]; bs=np.linalg.lstsq(Xs,y,rcond=None)[0]
    if bs[1]<=0: cand.append(np.array([bs[0],0.,bs[1]]))
    cand.append(np.array([float(np.mean(y)),0.,0.]))
    best=None
    for bb in cand:
        pred=X@bb; ss=float(np.sum((pred-y)**2))
        if best is None or ss<best[0]: best=(ss,bb,pred)
    return best[1],best[2]

def metrics(pred):
    rm=float(np.sqrt(np.mean((pred-Y)**2))); return rm,rm/Y.mean()*100,float(np.mean(np.abs(pred-Y)))

def loocv(h,s):
    out=[]
    for i in range(len(Y)):
        keep=np.arange(len(Y))!=i; bb,_=fit_constrained(h[keep],s[keep],Y[keep]); out.append(float(np.array([1.,h[i],s[i]])@bb))
    out=np.array(out); rm=float(np.sqrt(np.mean((out-Y)**2))); return out,rm,rm/Y.mean()*100

def annual_means(year,month,area,season,power):
    seas=np.isin(month,list(SEASONS[season])); deficit=np.maximum(0.,(AREF-area)/AREF)**power; excess=np.maximum(0.,(area-AREF)/AREF)**power
    e={}; w={}; h={}
    for y in range(2011,2024):
        m=(year==y)&seas; e[y]=float(deficit[m].mean()) if m.any() else 0.; w[y]=float(excess[m].mean()) if m.any() else 0.
        mj=(year==y)&np.isin(month,[5,6]); h[y]=float(area[mj].mean()) if mj.any() else np.nan
    return h,e,w

def state_vec(e,w,mem,rev):
    c=0.; o={}
    for y in range(2011,2024):
        c=max(0.,mem*c+e[y]-rev*w[y])
        if y in OBS:o[y]=c
    return np.array([o[int(y)] for y in YEARS],float)

def main():
    F,missing,annual=forcing(); names=list(HYDRO); rows=[]; best=None; tested=0
    for vals in itertools.product(*HYDRO.values()):
        p=dict(zip(names,vals)); r,d=sim(F,p,True); tested+=1
        dt=pd.to_datetime(d.date); yr=dt.dt.year.to_numpy(int); mo=dt.dt.month.to_numpy(int); area=d.area_m2.to_numpy(float)
        cache={}
        for season,powr in itertools.product(SEASONS,POWERS):
            h,e,w=annual_means(yr,mo,area,season,powr); hv=np.array([h[int(y)] for y in YEARS],float)
            for mem,rev in itertools.product(MEM,REV):
                sv=state_vec(e,w,mem,rev); b,pred=fit_constrained(hv,sv); rm,nrm,mae=metrics(pred); cv,crm,cnrm=loocv(hv,sv)
                item={'nrmse':nrm,'rmse':rm,'mae':mae,'loocv_nrmse':cnrm,'loocv_rmse':crm,'season':season,'power':powr,'memory':mem,'flood_reversal':rev,
                      **p,'beta0':float(b[0]),'beta_hydro':float(b[1]),'beta_state':float(b[2]),'raw_nrmse':r['nrmse'],'raw_dry_days':r['dry_days'],
                      'state_2013':float(sv[0]),'state_2023':float(sv[-1]),
                      **{f'raw_{y}':float(hv[i]) for i,y in enumerate(YEARS)},**{f'pred_{y}':float(pred[i]) for i,y in enumerate(YEARS)},**{f'cv_{y}':float(cv[i]) for i,y in enumerate(YEARS)}}
                rows.append(item)
                if best is None or nrm<best['nrmse']: best=item.copy()
    rows.sort(key=lambda x:x['nrmse']); pd.DataFrame(rows[:500]).to_csv(OUT/'stage31c_fast_top500.csv',index=False)
    summary={'objective':'retain accuracy while improving hydrologic/ecological consistency','best':best,
             'benchmarks':{'stage31b_linear_nrmse':0.7692692574776534,'stage31b_linear_loocv_nrmse':1.266132430355888,'stage26_nrmse':8.008034},
             'constraints':{'explicit_time_term':False,'beta_hydro_gte_0':True,'beta_exposure_state_lte_0':True,'lambda':0,'DSM':False,'bathymetry':False,'hard_2011_cap':False},
             'state':'persistent hydroperiod-driven exposure/colonization potential with optional flood reversal','hydrology_combinations':tested,'missing':missing,'annual_precip_mm':annual}
    (OUT/'stage31c_fast_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
