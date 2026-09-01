#!/usr/bin/env python3
"""Stage89 — field-constrained subsurface/visible-surface partition diagnostic.

No observational fitting.

Keeps the Stage85 mass-conservative external catchment soil + fast/slow local
return structure, but replaces the pond-side always-on V/60 drainage and
4 mm d-1 loss with:
  * an explicit drainable wetland subsurface store,
  * visible surface water only after that store is full,
  * a 2011-reference surface-depression capacity V0 with explicit spill,
  * effective pond precipitation 0.87 P,
  * effective pond evaporation 0.8 Penman,
  * parsimonious seepage = 1% of effective pond precipitation.

Central subsurface capacity 729.6 m3 is the previously derived depth-dependent
specific-yield estimate. 400 and 1036.5 m3 are physical sensitivity bounds
(order-of-magnitude lower bound and total pore-water upper bound, respectively),
not values fitted here.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import stage85_exact_tlmm_integrated as s85
from eghm_deterministic_forcing import deterministic_forcing

OUT=Path('stage89_outputs'); OUT.mkdir(exist_ok=True)
OBS=s85.OBS; YEARS=s85.EVAL_YEARS
SUBCAPS=(400.0,729.6,1036.5)


def forcing_frame():
    F,_,_,_=deterministic_forcing()
    return pd.DataFrame({'DATE':pd.to_datetime(F['date']),'PRE':F['pre'],'PP':F['pp'],'ETo':F['eto'],'EP':F['ep']})


def partition(X, cap):
    sub=min(max(X,0.0),cap)
    surf=max(X-cap,0.0)
    return sub,surf


def simulate(df, subcap):
    su=.5*s85.C_UPLAND
    # If visible water exists at initialization, the drainable subsurface store
    # beneath it must already be filled.  This preserves the mapped 2011 A0/V0
    # surface initial condition without introducing a fitted initialization term.
    X=subcap+s85.V0
    fast=0.; slow=0.
    prev=su+X+fast+slow
    maxerr=0.; spill_total=0.; rows=[]

    for r in df.itertuples(index=False):
        dt=pd.Timestamp(r.DATE); rawp=float(r.PRE); pp=float(r.PP); etoi=float(r.ETo); ep=float(r.EP)
        sub,surf=partition(X,subcap)
        ap=s85.area_v(surf); ah0=min(ap,s85.A0); aw=max(s85.A_WET-ap,0.)

        pup=rawp*s85.A_UPLAND/1000.
        pwet=rawp*aw/1000.
        popen=pp*ap/1000.

        # Upland bucket unchanged from Stage85.
        su+=pup
        e1=min(su,s85.ET_UPLAND*etoi*s85.A_UPLAND/1000.); su-=e1
        dex=max(su-s85.C_UPLAND,0.); su-=dex
        local=dex*s85.LOCAL_FRAC; deep=dex-local
        fast+=local*s85.FAST_FRAC; slow+=local*(1.-s85.FAST_FRAC)
        qf=min(fast,fast/s85.TAU_FAST); qs=min(slow,slow/s85.TAU_SLOW_D)
        fast-=qf; slow-=qs; qr=qf+qs

        # Wetland rainfall and local return enter the connected wetland store.
        X += pwet + popen + qr
        sub,surf=partition(X,subcap)

        # Terrestrial/wetland vegetation ET is drawn from subsurface water first.
        # Baseline diagnostic: exposed 2011 pond zone is bare; remaining wetland
        # non-pond area retains background vegetation.
        ap_now=s85.area_v(surf); ah0_now=min(ap_now,s85.A0); aw_now=max(s85.A_WET-ap_now,0.)
        exposed=max(s85.A0-ah0_now,0.); bg=max(aw_now-exposed,0.)
        e2d=etoi*(s85.K_BG*bg+s85.K_BARE*exposed)/1000.
        e2=min(sub,e2d)
        X-=e2
        sub,surf=partition(X,subcap)

        # Pond-only losses act only where visible surface water exists.
        ap_loss=s85.area_v(surf)
        eo_p=.8*ep*ap_loss/1000.
        qg_p=.01*pp*ap_loss/1000.
        pond_available=surf
        pond_loss=eo_p+qg_p
        fac=min(1.,pond_available/pond_loss) if pond_loss>0 else 1.
        eo=eo_p*fac; qg=qg_p*fac
        X-=eo+qg
        sub,surf=partition(X,subcap)

        # Topographic surface-depression capacity: excess above V0 spills.
        spill=max(surf-s85.V0,0.)
        if spill>0:
            X-=spill; spill_total+=spill
        sub,surf=partition(X,subcap)

        total=su+X+fast+slow
        inputs=pup+pwet+popen
        outputs=e1+e2+deep+eo+qg+spill
        err=prev+inputs-outputs-total; maxerr=max(maxerr,abs(err)); prev=total
        area=s85.area_v(surf) if surf>0 else 0.0
        rows.append({'DATE':dt,'subcap_m3':subcap,'subsurface_m3':sub,'surface_m3':surf,'surface_area_m2':area,
                     'surface_dry':int(surf<=1e-9),'upland_soil_m3':su,'fast_m3':fast,'slow_m3':slow,
                     'wetland_ET_m3':e2,'pond_evap_m3':eo,'pond_seep_m3':qg,'spill_m3':spill,'local_return_m3':qr,'deep_loss_m3':deep,
                     'mass_error_m3':err})
    out=pd.DataFrame(rows)
    return out,maxerr,spill_total


def metrics(out,months):
    pred=[]; errs=[]
    for y in YEARS:
        g=out[(out.DATE.dt.year==y)&(out.DATE.dt.month.isin(months))]
        p=float(g.surface_area_m2.mean()); pred.append((y,p)); errs.append(p-OBS[y])
    rmse=float(np.sqrt(np.mean(np.square(errs))))
    return pred,rmse,100*rmse/np.mean(list(OBS.values()))


def main():
    df=forcing_frame(); summary=[]; predrows=[]
    for cap in SUBCAPS:
        out,me,spill=simulate(df,cap)
        ap,rmse,nrmse=metrics(out,[4,5]); mp,mrmse,mnrmse=metrics(out,[5,6])
        z=out.surface_dry.astype(bool); marapr=out.DATE.dt.month.isin([3,4])
        for y,p in ap: predrows.append({'subcap_m3':cap,'window':'Apr-May','year':y,'pred_m2':p,'obs_m2':OBS[y],'error_m2':p-OBS[y]})
        for y,p in mp: predrows.append({'subcap_m3':cap,'window':'May-Jun','year':y,'pred_m2':p,'obs_m2':OBS[y],'error_m2':p-OBS[y]})
        summary.append({'subcap_m3':cap,'AprMay_RMSE_m2':rmse,'AprMay_nRMSE_pct':nrmse,'MayJun_RMSE_m2':mrmse,'MayJun_nRMSE_pct':mnrmse,
                        'surface_dry_days':int(z.sum()),'MarApr_surface_dry_days':int((z&marapr).sum()),
                        'total_spill_m3':float(spill),'max_surface_m3':float(out.surface_m3.max()),'max_surface_area_m2':float(out.surface_area_m2.max()),
                        'mean_subsurface_m3':float(out.subsurface_m3.mean()),'max_mass_error_m3':float(me)})
        out.to_csv(OUT/f'subcap_{str(cap).replace(".","p")}_daily.csv',index=False)
    s=pd.DataFrame(summary); p=pd.DataFrame(predrows)
    s.to_csv(OUT/'stage89_summary.csv',index=False); p.to_csv(OUT/'stage89_predictions.csv',index=False)
    print(s.to_string(index=False))
    print('\nApr-May predictions:\n',p[p.window=='Apr-May'].pivot(index='year',columns='subcap_m3',values='pred_m2').to_string())
    audit={'status':'PASS_STAGE89_SUBSURFACE_SURFACE_PARTITION_DIAGNOSTIC','parameter_fitting':False,
           'central_subcap_m3':729.6,'sensitivity_subcap_m3':[400.0,1036.5],
           'always_on_surface_drainage':False,'legacy_4mm_loss':False,
           'pond_contract':{'rain':'0.87P','evaporation':'0.8 Penman','seepage':'0.01 of effective P'},
           'surface_capacity_m3':s85.V0,'max_mass_error_m3':float(s.max_mass_error_m3.max())}
    (OUT/'stage89_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8'); print(json.dumps(audit,indent=2))
if __name__=='__main__': main()
