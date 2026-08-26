#!/usr/bin/env python3
import json,itertools
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing,sim,OBS
OUT=Path('stage31d_outputs'); OUT.mkdir(exist_ok=True)
YEARS=np.array(sorted(OBS),int); Y=np.array([OBS[int(y)] for y in YEARS],float); AREF=2241.762
CAND=[]
for ma,q0,mq in [(0.8,48,.5),(0.8,64,.6),(1.0,48,.6),(1.0,64,.6),(1.0,64,.8),(1.0,96,.8),(1.2,48,.6),(1.2,64,.8),(1.2,96,1.0),(1.5,48,.8),(1.5,64,1.0),(1.5,96,1.0)]:
 CAND.append({'m_area':ma,'q0':q0,'m_q':mq,'local_frac':.2,'fast_frac':.75,'tau_fast':60.,'tau_slow':365.})
SEAS={'annual':range(1,13),'mar_oct':range(3,11),'apr_oct':range(4,11),'may_sep':range(5,10)}; POW=[.5,1.,1.5,2.]; MEM=[.8,.9,.95,.975,.99,1.]; REV=[0,.25,.5,1.]

def state(e,w,mem,rev):
 c=0;o={}
 for y in range(2011,2024):
  c=max(0.,mem*c+e.get(y,0.)-rev*w.get(y,0.));
  if y in OBS:o[y]=c
 return np.array([o[int(y)] for y in YEARS])

def hydro_anom(h,s,train=None):
 if train is None: train=np.ones(len(h),dtype=bool)
 X=np.c_[np.ones(train.sum()),s[train]]; b=np.linalg.lstsq(X,h[train],rcond=None)[0]
 return h-(b[0]+b[1]*s)

def fit_sign(s,ha,y=Y):
 X=np.c_[np.ones(len(y)),s,ha]; cand=[]; b=np.linalg.lstsq(X,y,rcond=None)[0]
 if b[1]<=0 and b[2]>=0:cand.append(b)
 Xs=np.c_[np.ones(len(y)),s]; q=np.linalg.lstsq(Xs,y,rcond=None)[0]
 if q[1]<=0:cand.append(np.array([q[0],q[1],0.]))
 Xh=np.c_[np.ones(len(y)),ha]; q=np.linalg.lstsq(Xh,y,rcond=None)[0]
 if q[1]>=0:cand.append(np.array([q[0],0.,q[1]]))
 cand.append(np.array([y.mean(),0.,0.]))
 bb=min(cand,key=lambda x:float(np.sum((X@x-y)**2))); return bb,X@bb

def main():
 F,_,_=forcing(); rows=[]
 for p in CAND:
  r,d=sim(F,p,True); dt=pd.to_datetime(d.date); yr=dt.dt.year.to_numpy();mo=dt.dt.month.to_numpy();ar=d.area_m2.to_numpy(float)
  h=np.array([float(ar[(yr==y)&np.isin(mo,[5,6])].mean()) for y in YEARS])
  for sn,powr in itertools.product(SEAS,POW):
   mask=np.isin(mo,list(SEAS[sn])); de=np.maximum(0,(AREF-ar)/AREF)**powr; ex=np.maximum(0,(ar-AREF)/AREF)**powr
   e={y:float(de[(yr==y)&mask].mean()) for y in range(2011,2024)};w={y:float(ex[(yr==y)&mask].mean()) for y in range(2011,2024)}
   for mem,rev in itertools.product(MEM,REV):
    s=state(e,w,mem,rev);ha=hydro_anom(h,s);b,pred=fit_sign(s,ha);rm=float(np.sqrt(np.mean((pred-Y)**2)));nrm=rm/Y.mean()*100
    cv=[]
    for i in range(6):
     keep=np.arange(6)!=i; hai=hydro_anom(h,s,keep);bb,_=fit_sign(s[keep],hai[keep],Y[keep]);cv.append(float(np.array([1,s[i],hai[i]])@bb))
    cv=np.array(cv);cn=float(np.sqrt(np.mean((cv-Y)**2))/Y.mean()*100)
    rows.append({'nrmse':nrm,'rmse':rm,'loocv_nrmse':cn,'season':sn,'power':powr,'memory':mem,'flood_reversal':rev,**p,'beta0':b[0],'beta_state':b[1],'beta_hydro_anom':b[2],'raw_nrmse':r['nrmse'],**{f'pred_{y}':pred[j] for j,y in enumerate(YEARS)},**{f'cv_{y}':cv[j] for j,y in enumerate(YEARS)}})
 rows.sort(key=lambda x:x['nrmse']);pd.DataFrame(rows[:100]).to_csv(OUT/'top100.csv',index=False)
 summary={'best':rows[0],'benchmarks':{'stage31b_time_nrmse':0.7692692574776534,'stage31c_no_time_nrmse':1.0969697397128737},'form':'A = beta0 + beta_state*C_exposure + beta_hydro_anom*(H - E[H|C])','constraints':{'no_time':True,'beta_state<=0':True,'beta_hydro_anom>=0':True,'lambda':0,'hard_cap':False}}
 (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
