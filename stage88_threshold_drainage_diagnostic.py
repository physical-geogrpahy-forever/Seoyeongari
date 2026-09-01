#!/usr/bin/env python3
"""Stage88 — threshold-controlled surface drainage diagnostic.

No parameter fitting.  Tests whether the calibrated always-on Stage49 drainage
term V/tau_surf can be replaced by a topographically interpretable threshold:
no surface drainage below the 2011 reference storage V0; drainage/spill is
activated only for storage above V0.  Pond seepage is the manuscript's
parsimonious 1% of effective pond precipitation.

This is a structural diagnostic, not an accepted final model.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import stage85_exact_tlmm_integrated as s85
from eghm_deterministic_forcing import deterministic_forcing

OUT=Path('stage88_outputs'); OUT.mkdir(exist_ok=True)
YEARS=s85.EVAL_YEARS; OBS=s85.OBS

VARIANTS={
  # Controls reproduced from Stage87 logic.
  'always_linear_raw': dict(rain='raw',evap='raw',drain='always_linear'),
  'threshold_soft_raw': dict(rain='raw',evap='raw',drain='threshold_soft'),
  'threshold_hard_raw': dict(rain='raw',evap='raw',drain='threshold_hard'),
  'threshold_soft_effective': dict(rain='effective',evap='effective',drain='threshold_soft'),
  'threshold_hard_effective': dict(rain='effective',evap='effective',drain='threshold_hard'),
}


def forcing_frame():
    F,_,_,_=deterministic_forcing()
    return pd.DataFrame({'DATE':pd.to_datetime(F['date']),'PRE':F['pre'],'PP':F['pp'],'ETo':F['eto'],'EP':F['ep']})


def simulate(df,cfg):
    su=.5*s85.C_UPLAND; sw=.5*s85.C_WET; fast=slow=0.; surf=s85.V0
    prev=su+sw+fast+slow+surf; maxerr=0.; total_spill=0.; rows=[]
    for r in df.itertuples(index=False):
        rawp=float(r.PRE); pp=float(r.PP); etoi=float(r.ETo); ep=float(r.EP)
        ap=s85.area_v(surf); ah0=min(ap,s85.A0); aw=max(s85.A_WET-ap,0.)
        pup=rawp*s85.A_UPLAND/1000.; pwet=rawp*aw/1000.
        pond_p_mm=pp if cfg['rain']=='effective' else rawp
        popen=pond_p_mm*ap/1000.

        su+=pup; e1=min(su,s85.ET_UPLAND*etoi*s85.A_UPLAND/1000.); su-=e1
        dex=max(su-s85.C_UPLAND,0.); su-=dex
        sw+=pwet
        exposed=max(s85.A0-ah0,0.); bg=max(aw-exposed,0.)
        e2=min(sw,etoi*(s85.K_BG*bg+s85.K_BARE*exposed)/1000.); sw-=e2
        dw=max(sw-s85.C_WET,0.); sw-=dw
        local=dex*s85.LOCAL_FRAC; deep=dex-local
        fast+=local*s85.FAST_FRAC; slow+=local*(1.-s85.FAST_FRAC)
        qf=min(fast,fast/s85.TAU_FAST); qs=min(slow,slow/s85.TAU_SLOW_D)
        fast-=qf; slow-=qs; qr=qf+qs

        surf+=popen+dw+qr
        aloss=s85.area_v(surf)
        evap_mm=.8*ep if cfg['evap']=='effective' else ep
        eo_p=evap_mm*aloss/1000.
        qg_p=.01*pp*aloss/1000.
        if cfg['drain']=='always_linear':
            qo_p=surf/s85.TAU_SURF
        elif cfg['drain']=='threshold_soft':
            qo_p=max(surf-s85.V0,0.)/s85.TAU_SURF
        elif cfg['drain']=='threshold_hard':
            qo_p=max(surf-s85.V0,0.)
        else: raise ValueError(cfg)

        lp=eo_p+qg_p+qo_p; fac=min(1.,surf/lp) if lp>0 else 1.
        eo=eo_p*fac; qg=qg_p*fac; qo=qo_p*fac
        surf-=eo+qg+qo; total_spill+=qo
        if surf<0 and surf>-1e-12: surf=0.
        total=su+sw+fast+slow+surf; inputs=pup+pwet+popen; outputs=e1+e2+eo+deep+qg+qo
        err=prev+inputs-outputs-total; maxerr=max(maxerr,abs(err)); prev=total
        rows.append({'DATE':r.DATE,'V_m3':surf,'area_m2':s85.area_v(surf),'surface_drain_m3':qo,'seep_m3':qg,'evap_m3':eo,
                     'return_m3':qr,'zero_surface':int(surf<=1e-9),'above_V0':int(surf>s85.V0+1e-9)})
    out=pd.DataFrame(rows); out['DATE']=pd.to_datetime(out.DATE)
    return out,maxerr,total_spill


def window_metrics(out,months):
    preds=[]; errs=[]
    for y in YEARS:
        g=out[(out.DATE.dt.year==y)&(out.DATE.dt.month.isin(months))]
        p=float(g.area_m2.mean()); preds.append((y,p)); errs.append(p-OBS[y])
    rmse=float(np.sqrt(np.mean(np.square(errs)))); return preds,rmse,100*rmse/np.mean(list(OBS.values()))


def main():
    df=forcing_frame(); summary=[]; predictions=[]
    for name,cfg in VARIANTS.items():
        out,me,spill=simulate(df,cfg)
        ap,rmse,nrmse=window_metrics(out,[4,5]); mp,mrmse,mnrmse=window_metrics(out,[5,6])
        marapr=(out.DATE.dt.month.isin([3,4])); z=out.zero_surface.astype(bool)
        for y,p in ap: predictions.append({'variant':name,'window':'Apr-May','year':y,'pred_m2':p,'obs_m2':OBS[y],'error_m2':p-OBS[y]})
        for y,p in mp: predictions.append({'variant':name,'window':'May-Jun','year':y,'pred_m2':p,'obs_m2':OBS[y],'error_m2':p-OBS[y]})
        summary.append({
          'variant':name,'AprMay_RMSE_m2':rmse,'AprMay_nRMSE_pct':nrmse,'MayJun_RMSE_m2':mrmse,'MayJun_nRMSE_pct':mnrmse,
          'zero_surface_days':int(z.sum()),'MarApr_zero_days':int((z&marapr).sum()),'above_V0_days':int(out.above_V0.sum()),
          'total_surface_drain_m3':float(spill),'max_V_m3':float(out.V_m3.max()),'max_area_m2':float(out.area_m2.max()),'max_mass_error_m3':float(me),
          'rain_contract':cfg['rain'],'evap_contract':cfg['evap'],'drain_contract':cfg['drain']})
        out.to_csv(OUT/f'{name}_daily.csv',index=False)
    s=pd.DataFrame(summary).sort_values('AprMay_nRMSE_pct'); p=pd.DataFrame(predictions)
    s.to_csv(OUT/'stage88_summary.csv',index=False); p.to_csv(OUT/'stage88_predictions.csv',index=False)
    print(s.to_string(index=False))
    print('\nApr-May predictions:\n',p[p.window=='Apr-May'].pivot(index='year',columns='variant',values='pred_m2').to_string())
    audit={'status':'PASS_STAGE88_THRESHOLD_DRAINAGE_DIAGNOSTIC','parameter_fitting':False,'threshold_storage_m3':s85.V0,
           'threshold_source':'2011 reference/initial storage V0 already fixed in accepted EGHM geometry; not optimized here',
           'seepage_contract':'1% of effective pond precipitation','max_mass_error_m3':float(s.max_mass_error_m3.max())}
    (OUT/'stage88_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8'); print(json.dumps(audit,indent=2))
if __name__=='__main__': main()
