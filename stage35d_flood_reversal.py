#!/usr/bin/env python3
"""Stage35D: test whether literature-supported inundation-driven vegetation loss
is identifiable while preserving exact water balance and nRMSE <=2%.

Ecological state:
 dx/dt = r_est E28 (1-x) - r_flood F28 x
where E28 and F28 are 28-d antecedent exposure/flooding indices generated only
from the exact Stage35 water balance + Hayashi storage-area state.
van der Valk et al. (1994) found persistent elevated water levels increased open
water and reduced emergent vegetation; hence the sign of r_flood is fixed >=0.
2022 remains excluded from fitting and model selection.
"""
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing,OBS
from stage35c_mass_balance_state_operator import hydro,A0
OUT=Path('stage35d_outputs');OUT.mkdir(exist_ok=True)
YEARS=np.array(sorted(OBS),int);Y=np.array([OBS[int(y)] for y in YEARS],float)
V0S=[1200.,1600.,2400.];PS=[8.,12.,20.];TS=[60.,120.];LOCAL=[.2,.3,.4];TF=[30.,60.]
RE=[.05,.1,.2,.5];RF=[0.,.05,.1,.2,.5,1.0];WINDOW=30

def state(area,re,rf):
 ex=np.clip((A0-area)/A0,0,1);fl=np.clip((area-A0)/A0,0,1)
 e=pd.Series(ex).rolling(28,min_periods=28).mean().fillna(0).to_numpy();f=pd.Series(fl).rolling(28,min_periods=28).mean().fillna(0).to_numpy()
 x=0.;out=np.empty(len(area))
 for i in range(len(area)):
  x += (re/365.)*e[i]*(1-x) - (rf/365.)*f[i]*x;x=min(1.,max(0.,x));out[i]=x
 return out,e,f

def ann(dt,x):
 yr=dt.year.to_numpy();mo=dt.month.to_numpy();return np.array([float(x[(yr==y)&np.isin(mo,[5,6])].mean()) for y in YEARS])
def hydro_feature(dt,q):
 yr=dt.year.to_numpy();mo=dt.month.to_numpy();r=pd.Series(q,index=dt).rolling(WINDOW,min_periods=1).sum().to_numpy();ref=float(r[(yr==2011)&np.isin(mo,[5,6])].mean())
 return np.array([float(r[(yr==y)&np.isin(mo,[5,6])].mean()-ref) for y in YEARS])
def fit(S,H,y=Y):
 X=np.c_[-S,H];t=y-A0;c=[];b=np.linalg.lstsq(X,t,rcond=None)[0]
 if 0<=b[0]<=A0 and b[1]>=0:c.append(b)
 d=np.dot(S,S);kc=min(A0,max(0,np.dot(-S,t)/d)) if d else 0;c.append(np.array([kc,0.]))
 d=np.dot(H,H);kh=max(0,np.dot(H,t)/d) if d else 0;c.append(np.array([0.,kh]));c.append(np.array([0.,0.]))
 bb=min(c,key=lambda z:float(np.sum((A0+X@z-y)**2)));return bb,A0+X@bb
def metrics(p):
 rm=float(np.sqrt(np.mean((p-Y)**2)));return rm,100*rm/Y.mean()
def cv(S,H):
 pp=[]
 for i in range(6):
  k=np.arange(6)!=i;b,_=fit(S[k],H[k],Y[k]);pp.append(float(A0+np.array([-S[i],H[i]])@b))
 pp=np.array(pp);rm=float(np.sqrt(np.mean((pp-Y)**2)));return 100*rm/Y.mean(),pp

def main():
 F,_,_=forcing();rows=[]
 for V0,p,ts,lf,tf in itertools.product(V0S,PS,TS,LOCAL,TF):
  hp={'V0':V0,'p_shape':p,'tau_surf':ts,'local_frac':lf,'tau_fast':tf};h=hydro(F,hp);H=hydro_feature(h['dates'],h['return_flow'])
  for re,rf in itertools.product(RE,RF):
   st,e,f=state(h['area'],re,rf);S=ann(h['dates'],st);b,pred=fit(S,H);rm,nrm=metrics(pred);cn,cvp=cv(S,H);corr=float(np.corrcoef(S,YEARS)[0,1]) if np.std(S)>0 else 1
   hydrange=float(b[1]*(H.max()-H.min()))
   rows.append({'nrmse':nrm,'rmse':rm,'loocv_nrmse':cn,**hp,'r_est_yr':re,'r_flood_yr':rf,'K_colonizable_m2':b[0],'K_returnflow':b[1],
                'hydro_effect_range_m2':hydrange,'state_year_corr':corr,'max_mass_error_m3':h['mass_error'],**{f'pred_{y}':pred[j] for j,y in enumerate(YEARS)},**{f'cv_{y}':cvp[j] for j,y in enumerate(YEARS)}})
 feasible=[r for r in rows if r['nrmse']<=2 and r['max_mass_error_m3']<1e-8 and r['state_year_corr']<.99]
 nonzero=[r for r in feasible if r['r_flood_yr']>0]
 chosen=sorted(feasible,key=lambda z:(z['loocv_nrmse'],z['nrmse']))[0] if feasible else sorted(rows,key=lambda z:z['nrmse'])[0]
 chosen_nonzero=sorted(nonzero,key=lambda z:(z['loocv_nrmse'],z['nrmse']))[0] if nonzero else None
 pd.DataFrame(sorted(rows,key=lambda z:(z['nrmse'],z['loocv_nrmse']))[:500]).to_csv(OUT/'top500.csv',index=False);pd.DataFrame(sorted(feasible,key=lambda z:(z['loocv_nrmse'],z['nrmse']))[:500]).to_csv(OUT/'feasible.csv',index=False)
 out={'model':'Stage35D flood reversal identifiability test','n_candidates':len(rows),'n_feasible':len(feasible),'n_feasible_nonzero_flood':len(nonzero),'best_any':chosen,'best_nonzero_flood':chosen_nonzero,
      'rules':{'exact_water_balance':True,'CN':False,'TOPMODEL':False,'lambda':0,'hard_cap':False,'freeboard':False,'explicit_time':False,'2022_fit':False,'flood_loss_sign':'>=0'},
      'benchmark_balanced_stage35c':{'nrmse':1.6727834950024372,'loocv':1.99897134390346,'2022_holdout_abs_pct':2.2963381126156754}}
 (OUT/'stage35d_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
