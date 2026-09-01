#!/usr/bin/env python3
import itertools, json, math
from pathlib import Path
import numpy as np
import pandas as pd

AWS='OBS_AWS_DD_20250930013603.csv'; ASOS='OBS_ASOS_DD_20250930041037.csv'
OUT=Path('stage30_fast_outputs'); OUT.mkdir(exist_ok=True)
A_REF=2241.762; A_EXT=8483.0; HB=1.2; ALPHA=1.3; SOIL_CAP=.294*.55*A_EXT
OBS={2013:2154.430,2015:2147.678,2017:2051.218,2019:2045.159,2021:1965.256,2023:1882.700}
T26={2013:2182.2346,2015:2203.2931,2017:1962.5506,2019:1999.3472,2021:2184.1155,2023:2196.6569}
LAT=33.30456; ALT=188.42; CN=68.; S=25400/CN-254; IA=.2*S

def e0(t): return .6108*np.exp(17.27*t/(t+237.3))
def delta(t): return 4098*e0(t)/(t+237.3)**2
def ra_n(doy,lat):
 d=1+.033*np.cos(2*np.pi*doy/365); dec=.409*np.sin(2*np.pi*doy/365-1.39); ws=np.arccos(np.clip(-np.tan(lat)*np.tan(dec),-1,1));
 return (24*60/np.pi)*.082*d*(ws*np.sin(lat)*np.sin(dec)+np.cos(lat)*np.cos(dec)*np.sin(ws)),(24/np.pi)*ws

def read_asos():
 for enc in ('cp949','utf-8-sig','utf-8'):
  try: return pd.read_csv(ASOS,encoding=enc)
  except Exception: pass
 raise RuntimeError('ASOS read failed')

def forcing():
 a=pd.read_csv(AWS); dt=pd.to_datetime(a.time,errors='coerce')
 d=pd.DataFrame({'date':dt,'doy':dt.dt.dayofyear,'tmean':pd.to_numeric(a.tmean,errors='coerce'),'tmin':pd.to_numeric(a.tmin,errors='coerce'),'tmax':pd.to_numeric(a.tmax,errors='coerce'),'pre':pd.to_numeric(a.pre,errors='coerce'),'wind':pd.to_numeric(a.wind,errors='coerce')})
 s=read_asos();
 if '지점' in s.columns: s=s[s['지점']==189]
 sun=pd.DataFrame({'date':pd.to_datetime(s['time'],errors='coerce'),'sun':pd.to_numeric(s['hour'],errors='coerce')}).dropna(subset=['date']).groupby('date',as_index=False).sun.mean()
 d=d.merge(sun,on='date',how='left'); d['sun']=d.sun.fillna(0); d=d[(d.date>='2011-01-01')&(d.date<='2023-12-31')].copy().reset_index(drop=True)
 raw_missing={c:int(d[c].isna().sum()) for c in ['tmean','tmin','tmax','pre','wind','sun']}
 d.pre=d.pre.fillna(0).clip(lower=0)
 for c in ['tmean','tmin','tmax','wind']: d[c]=d[c].interpolate(limit_direction='both')
 lat=np.deg2rad(LAT); P=101.3*((293-.0065*ALT)/293)**5.26; ga=.000665*P; lam=2.45
 ra,N=ra_n(d.doy.to_numpy(float),lat); u2=d.wind.to_numpy(float)*4.87/np.log(67.8*2-5.42); rso=(.75+2e-5*ALT)*ra; nN=np.clip(d.sun.to_numpy(float)/np.maximum(N,1e-6),0,1); rs=(.25+.50*nN)*ra
 es=(e0(d.tmax.to_numpy(float))+e0(d.tmin.to_numpy(float)))/2; ea=e0(d.tmin.to_numpy(float)); D=delta(d.tmean.to_numpy(float)); sig=4.903e-9
 f=np.clip(rs/np.maximum(rso,1e-6),0,1); rnl=sig*(((d.tmax.to_numpy(float)+273.16)**4+(d.tmin.to_numpy(float)+273.16)**4)/2)*(.34-.14*np.sqrt(np.maximum(ea,0)))*(1.35*f-.35)
 rnveg=(1-.23)*rs-rnl; rnwat=(1-.08)*rs-rnl
 eto=np.maximum((.408*D*rnveg+ga*(900/(d.tmean.to_numpy(float)+273))*u2*(es-ea))/(D+ga*(1+.34*u2)),0)
 ep=np.maximum((D/(D+ga))*(rnwat/lam)+(ga/(D+ga))*(6.43*(1+.536*u2)/lam)*(es-ea),0)
 pre=d.pre.to_numpy(float); pes=np.where(pre<=IA,0,(pre-IA)**2/(pre+.8*S))
 years=d.date.dt.year.to_numpy(int); months=d.date.dt.month.to_numpy(int)
 F={'pre':pre,'pes':pes,'eto':eto,'ep':ep,'pp':.87*pre,'year':years,'month':months,'date':d.date.to_numpy()}
 annual={int(y):float(v) for y,v in d.groupby(d.date.dt.year).pre.sum().items()}
 pd.DataFrame({'date':d.date,'PRE':pre,'ETo':eto,'E_P':ep,'P_ES':pes,'P_P':.87*pre}).to_csv(OUT/'forcing.csv',index=False)
 return F,raw_missing,annual

def vh(h): return 0. if h<=0 else A_REF*HB/(ALPHA+1)*(h/HB)**(ALPHA+1)
def hv(v): return 0. if v<=0 else HB*(v/(A_REF*HB/(ALPHA+1)))**(1/(ALPHA+1))
def av(v):
 h=hv(v); return 0. if h<=0 else A_REF*(h/HB)**ALPHA

def metrics(pred):
 ys=sorted(OBS); o=np.array([OBS[y] for y in ys]); p=np.array([pred[y] for y in ys]); rm=float(np.sqrt(np.mean((p-o)**2)))
 return rm,rm/o.mean()*100,float(np.mean(abs(p-o)))

def sim(F,p,stage26=False,v=None,daily=False):
 v=v or {}; soil={'zero':0.,'half':SOIL_CAP/2,'full':SOIL_CAP}[v.get('soil_init','half')]; fast=slow=0.; pond=vh(HB); cap=vh(HB)
 loc=p.get('local_frac',.30); ff=p.get('fast_frac',.25); tf=p.get('tau_fast',60.); ts=p.get('tau_slow',730.); leak=p.get('leak_mm_d',.5); c2=p.get('c2',0.)
 sums={y:0. for y in OBS}; counts={y:0 for y in OBS}; spilltot=drain=deepTot=rechTot=0.; maxh=0.; dry=springdry=0; maxmass=0.; rows=[]
 prev=soil+fast+slow+pond
 pre=F['pre']; pes=F['pes']; eto=F['eto']; ep=F['ep']; pp=F['pp']; yy=F['year']; mm=F['month']; dates=F['date']
 for i in range(len(pre)):
  pext=pre[i]*A_EXT/1000; qrun=max(0.,pes[i]*A_EXT/1000); infil=max(0.,pext-qrun); soil+=infil
  if v.get('soil_order','et_then_recharge')=='recharge_then_et':
   rech=max(soil-SOIL_CAP,0.); soil-=rech; aet=min(soil,.95*eto[i]*A_EXT/1000); soil-=aet
  else:
   aet=min(soil,.95*eto[i]*A_EXT/1000); soil-=aet; rech=max(soil-SOIL_CAP,0.); soil-=rech
  local=rech*loc; deep=rech-local; rechTot+=rech; deepTot+=deep; rf=local*ff; rs=local-rf
  if v.get('release_order','post')=='pre':
   qf=fast/tf; qs=slow/ts; fast-=qf; slow-=qs; fast+=rf; slow+=rs
  else:
   fast+=rf; slow+=rs; qf=fast/tf; qs=slow/ts; fast-=qf; slow-=qs
  area=av(pond); h=hv(pond); ar=A_REF if v.get('pond_rain_area','dynamic')=='fixed' else area; ae=A_REF if v.get('pond_evap_area','dynamic')=='fixed' else area; al=A_REF if v.get('pond_leak_area','dynamic')=='fixed' else area
  pr=pp[i]*ar/1000; pev=.80*ep[i]*ae/1000; pleak=leak*al/1000 + ((.01*pp[i]*al/1000) if v.get('include_qs01',False) else 0.); qlat=0. if stage26 else c2*h*h
  available=pond+qrun+qf+qs+pr; loss=pev+pleak+qlat
  if loss>available and loss>0: fac=available/loss; pev*=fac; pleak*=fac; qlat*=fac
  pond=available-pev-pleak-qlat; sp=0.
  if stage26 and pond>cap: sp=pond-cap; pond=cap
  spilltot+=sp; drain+=qlat
  total=soil+fast+slow+pond; mass=(prev+pext+pr)-(total+aet+deep+pev+pleak+qlat+sp); maxmass=max(maxmass,abs(mass)); prev=total
  aout=av(pond); hout=hv(pond); maxh=max(maxh,hout)
  if aout<1: dry+=1; springdry+=(mm[i] in (3,4))
  if yy[i] in sums and mm[i] in (5,6): sums[yy[i]]+=aout; counts[yy[i]]+=1
  if daily: rows.append((dates[i],aout,hout,pond,soil,fast,slow,rech,deep,qrun,qf,qs,pr,pev,pleak,qlat,sp,mass))
 pred={y:sums[y]/counts[y] for y in sums}; rm,nrm,mae=metrics(pred)
 r={'pred':pred,'rmse':rm,'nrmse':nrm,'mae':mae,'max_h':maxh,'dry_days':dry,'spring_dry_days':springdry,'spill_m3':spilltot,'head_drain_m3':drain,'deep_m3':deepTot,'recharge_m3':rechTot,'max_daily_mass_error_m3':maxmass,'final_storage_m3':prev}
 if daily:
  cols=['date','area_m2','h_m','pond_m3','soil_m3','fast_m3','slow_m3','recharge_m3','deep_m3','runoff_m3','fast_return_m3','slow_return_m3','pond_rain_m3','pond_evap_m3','pond_leak_m3','head_drain_m3','spill_m3','mass_error_m3']; return r,pd.DataFrame(rows,columns=cols)
 return r,None

def main():
 F,missing,annual=forcing(); target=np.array([T26[y] for y in sorted(T26)]); variants=[]
 # Regression fingerprint search; no science is selected from this search, only bookkeeping convention.
 for vals in itertools.product(['zero','half','full'],['et_then_recharge','recharge_then_et'],['post','pre'],['dynamic','fixed'],['dynamic','fixed'],['dynamic','fixed'],[False,True]):
  v=dict(zip(['soil_init','soil_order','release_order','pond_rain_area','pond_evap_area','pond_leak_area','include_qs01'],vals)); r,_=sim(F,{'local_frac':.30,'fast_frac':.25,'tau_fast':60.,'tau_slow':730.,'leak_mm_d':.5},True,v); pr=np.array([r['pred'][y] for y in sorted(T26)]); rr=float(np.sqrt(np.mean((pr-target)**2))); variants.append((rr,v,r))
 variants.sort(key=lambda x:x[0]); rr,vbest,r26=variants[0]
 pd.DataFrame([{'target_rmse_m2':x[0],**x[1],'obs_nrmse_pct':x[2]['nrmse'],'spill_m3':x[2]['spill_m3'],**{f'p{y}':x[2]['pred'][y] for y in sorted(T26)}} for x in variants[:25]]).to_csv(OUT/'stage26_regression_top25.csv',index=False)
 print('STAGE26_REGRESSION',rr,json.dumps(vbest),json.dumps(r26))
 # Gate: Stage30 numbers are explicitly marked provisional if regression fingerprint is not close.
 c2vals=[0,.125,.25,.5,1,2,3,4,5,6,8,10,12,16,24,32,48]
 fixed=[]
 for c2 in c2vals:
  p={'local_frac':.30,'fast_frac':.25,'tau_fast':60.,'tau_slow':730.,'leak_mm_d':.5,'c2':c2}; r,_=sim(F,p,False,vbest); fixed.append((r['nrmse'],p,r))
 pd.DataFrame([{**p,**{k:x for k,x in r.items() if k!='pred'},**{f'p{y}':r['pred'][y] for y in sorted(OBS)}} for _,p,r in fixed]).to_csv(OUT/'stage30_fixed.csv',index=False)
 grid=[ [.10,.20,.30], [.25,.50,.75], [30.,60.], [365.,730.,1460.], [.5,1.,2.,4.091], [.125,.25,.5,1.,2.,3.,4.,5.,6.,8.,10.,12.,16.,24.,32.,48.] ]
 best=[]
 for vals in itertools.product(*grid):
  p=dict(zip(['local_frac','fast_frac','tau_fast','tau_slow','leak_mm_d','c2'],vals)); r,_=sim(F,p,False,vbest); best.append((r['nrmse'],p,r))
 best.sort(key=lambda x:x[0]); bp=best[0][1]; br,bd=sim(F,bp,False,vbest,True); bd.to_csv(OUT/'stage30_best_daily.csv',index=False)
 pd.DataFrame([{**p,**{k:x for k,x in r.items() if k!='pred'},**{f'p{y}':r['pred'][y] for y in sorted(OBS)}} for _,p,r in best[:100]]).to_csv(OUT/'stage30_top100.csv',index=False)
 summary={'forcing_rows':len(F['pre']),'raw_missing':missing,'annual_precip_mm':annual,'stage26_target_rmse_m2':rr,'stage26_variant':vbest,'stage26_reconstructed':r26,'stage30_status':'VALID_FOR_COMPARISON' if rr<=10 else 'PROVISIONAL_REGRESSION_MISMATCH','stage30_best_params':bp,'stage30_best':br,'rules':{'lambda':0,'hard_cap':False,'freeboard_threshold':False,'DSM':False,'bathymetry':False,'head_drain':'Q=C2*h^2'}}
 (OUT/'stage30_fast_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8'); print('SUMMARY_JSON'); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
