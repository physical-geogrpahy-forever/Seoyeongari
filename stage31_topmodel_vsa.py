#!/usr/bin/env python3
import json, math, itertools
from pathlib import Path
import numpy as np
import pandas as pd
from stage30_macro_head_drainage_fast import forcing, metrics, OBS

OUT=Path('stage31_outputs'); OUT.mkdir(exist_ok=True)
A_INIT=2241.762; A_WET=5939.5; A_BASIN=8483.0+A_INIT
AWC_DEPTH=.294*.55

def area_from_D(D,m):
    # TOPMODEL-type saturated/open-water contributing area. 2011 is NOT a cap.
    if D<=0: return A_WET
    return A_WET*math.exp(-D/m)

def sim(F,p,daily=False):
    ma=p['m_area']; q0=p['q0']; mq=p['m_q']; loc=p.get('local_frac',.30); ff=p.get('fast_frac',.25); tf=p.get('tau_fast',60.); ts=p.get('tau_slow',730.)
    # Initial state is inferred from observed 2011 area only.
    D0=-ma*math.log(A_INIT/A_WET); D=D0
    A=area_from_D(D,ma); unsat=A_BASIN-A; soil_cap=AWC_DEPTH*unsat; soil=.5*soil_cap; fast=slow=0.
    sums={y:0. for y in OBS}; counts={y:0 for y in OBS}; deepTot=rechTot=qbaseTot=0.; dry=spring=0; minD=D; maxD=D; maxA=A; maxmass=0.; rows=[]
    # Relative wetland/catchment active storage W=-D*A_BASIN; arbitrary zero datum cancels in daily mass closure.
    W=-D*A_BASIN; prev=soil+fast+slow+W
    pre=F['pre']; pes=F['pes']; eto=F['eto']; ep=F['ep']; yy=F['year']; mm=F['month']; dates=F['date']
    for i in range(len(pre)):
        A=area_from_D(D,ma); unsat=A_BASIN-A
        # Dynamic unsaturated-area soil capacity: shrinking source area releases excess water; expansion adds empty capacity.
        soil_cap=AWC_DEPTH*unsat
        p_uns=pre[i]*unsat/1000.; qrun=max(0.,pes[i]*unsat/1000.); infil=max(0.,p_uns-qrun); soil+=infil
        aet=min(soil,.95*eto[i]*unsat/1000.); soil-=aet
        rech=max(soil-soil_cap,0.); soil-=rech; local=rech*loc; deep=rech-local; rechTot+=rech; deepTot+=deep
        fast+=local*ff; slow+=local*(1-ff); qf=fast/tf; qs=slow/ts; fast-=qf; slow-=qs
        # Direct surface-water precipitation retains the project 0.87 factor; remainder is explicit interception/retention loss.
        pr=.87*pre[i]*A/1000.; pint=.13*pre[i]*A/1000.; evap=.80*ep[i]*A/1000.
        # TOPMODEL exponential baseflow/drainage: no threshold and no 2011 storage cap.
        qb=q0*math.exp(-D/mq); qbaseTot+=qb
        net=qrun+qf+qs+pr-evap-qb
        W += net; D=-W/A_BASIN
        Aout=area_from_D(D,ma); minD=min(minD,D); maxD=max(maxD,D); maxA=max(maxA,Aout)
        if Aout<1.: dry+=1; spring+=(mm[i] in (3,4))
        if yy[i] in sums and mm[i] in (5,6): sums[yy[i]]+=Aout; counts[yy[i]]+=1
        total=soil+fast+slow+W; pin=pre[i]*A_BASIN/1000.; mass=(prev+pin)-(total+aet+deep+evap+qb+pint); maxmass=max(maxmass,abs(mass)); prev=total
        if daily: rows.append((dates[i],D,Aout,W,soil,fast,slow,qrun,rech,deep,qf,qs,pr,pint,evap,qb,mass))
    pred={y:sums[y]/counts[y] for y in sums}; rm,nrm,mae=metrics(pred)
    r={'pred':pred,'rmse':rm,'nrmse':nrm,'mae':mae,'dry_days':dry,'spring_dry_days':spring,'min_D_m':minD,'max_D_m':maxD,'max_area_m2':maxA,'base_drain_m3':qbaseTot,'deep_m3':deepTot,'recharge_m3':rechTot,'max_daily_mass_error_m3':maxmass,'final_D_m':D}
    if daily:
        cols=['date','D_m','area_m2','Wrel_m3','soil_m3','fast_m3','slow_m3','runoff_m3','recharge_m3','deep_m3','fast_return_m3','slow_return_m3','rain_surface_m3','interception_m3','evap_surface_m3','base_drain_m3','mass_error_m3']; return r,pd.DataFrame(rows,columns=cols)
    return r,None

def main():
    F,missing,annual=forcing()
    # Phase A: isolate VSA geometry/drainage with Stage26 perched-return structure fixed.
    coarse=[]
    for ma,q0,mq in itertools.product([.03,.05,.075,.10,.15,.20,.30,.40,.60,.80,1.0],[.25,.5,1,2,4,8,16,32,64],[.03,.05,.075,.10,.15,.20,.30,.40,.60,.80,1.2,1.6]):
        p={'m_area':ma,'q0':q0,'m_q':mq,'local_frac':.30,'fast_frac':.25,'tau_fast':60.,'tau_slow':730.}; r,_=sim(F,p); coarse.append((r['nrmse'],p,r))
    coarse.sort(key=lambda x:x[0]);
    pd.DataFrame([{**p,**{k:v for k,v in r.items() if k!='pred'},**{f'p{y}':r['pred'][y] for y in sorted(OBS)}} for _,p,r in coarse[:100]]).to_csv(OUT/'stage31_coarse_top100.csv',index=False)
    # Phase B: only refine the best distinct VSA parameter triplets with plausible perched-return variants.
    seeds=[]
    for _,p,_ in coarse:
        t=(p['m_area'],p['q0'],p['m_q'])
        if t not in seeds: seeds.append(t)
        if len(seeds)>=15: break
    fine=[]
    for (ma,q0,mq),loc,ff,tf,ts in itertools.product(seeds,[.10,.20,.30],[.25,.50,.75],[30.,60.],[365.,730.,1460.]):
        p={'m_area':ma,'q0':q0,'m_q':mq,'local_frac':loc,'fast_frac':ff,'tau_fast':tf,'tau_slow':ts}; r,_=sim(F,p); fine.append((r['nrmse'],p,r))
    fine.sort(key=lambda x:x[0]); bp=fine[0][1]; br,bd=sim(F,bp,True); bd.to_csv(OUT/'stage31_best_daily.csv',index=False)
    pd.DataFrame([{**p,**{k:v for k,v in r.items() if k!='pred'},**{f'p{y}':r['pred'][y] for y in sorted(OBS)}} for _,p,r in fine[:100]]).to_csv(OUT/'stage31_fine_top100.csv',index=False)
    summary={'forcing_rows':len(F['pre']),'raw_missing':missing,'annual_precip_mm':annual,'best_params':bp,'best':br,'benchmark_stage26_nrmse_pct':8.008034,'rules':{'lambda':0,'hard_cap_2011':False,'freeboard_threshold':False,'DSM':False,'bathymetry':False,'A_wet_m2':A_WET,'area_equation':'A=A_wet*exp(-D/m_area), capped only by mapped wetland footprint','drainage':'Q=Q0*exp(-D/m_q)','initialization':'D0 from 2011 observed area only'}}
    (OUT/'stage31_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
