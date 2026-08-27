#!/usr/bin/env python3
"""Stage87 — no-fit pond-side hydrologic contract ablation.

Diagnoses legacy pond loss / forcing terms while keeping the Stage85 catchment
soil stores, local-return routing, geometry, and initial conditions unchanged.
No observational parameter fitting is performed.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
import stage85_exact_tlmm_integrated as s85
from eghm_deterministic_forcing import deterministic_forcing

OUT=Path('stage87_outputs'); OUT.mkdir(exist_ok=True)
OBS=s85.OBS; YEARS=s85.EVAL_YEARS

VARIANTS={
 'current_stage85': dict(use_eff_rain=False,use_eff_evap=False,use_surface_outflow=True,use_legacy_gw=True),
 'no_surface_outflow': dict(use_eff_rain=False,use_eff_evap=False,use_surface_outflow=False,use_legacy_gw=True),
 'percolation_1pct_only': dict(use_eff_rain=False,use_eff_evap=False,use_surface_outflow=True,use_legacy_gw=False),
 'no_outflow_plus_1pct': dict(use_eff_rain=False,use_eff_evap=False,use_surface_outflow=False,use_legacy_gw=False),
 'canonical_pond_contract': dict(use_eff_rain=True,use_eff_evap=True,use_surface_outflow=False,use_legacy_gw=False),
}


def forcing_frame():
    F,_,_,_=deterministic_forcing()
    return pd.DataFrame({
      'DATE':pd.to_datetime(F['date']),'PRE':F['pre'],'PP':F['pp'],'ETo':F['eto'],'EP':F['ep'],'PES':F['pes']
    })


def run_variant(df,cfg):
    su=.5*s85.C_UPLAND; sw=.5*s85.C_WET; fast=0.; slow=0.; surf=s85.V0
    prev=su+sw+fast+slow+surf; maxerr=0.; rows=[]
    for r in df.itertuples(index=False):
        rawp=float(r.PRE); pp=float(r.PP); etoi=float(r.ETo); ep=float(r.EP)
        ap=s85.area_v(surf); ah0=min(ap,s85.A0); aw=max(s85.A_WET-ap,0.)
        # Keep non-pond catchment/wetland precipitation unchanged in this ablation.
        pup=rawp*s85.A_UPLAND/1000.; pwet=rawp*aw/1000.
        pond_p_mm=pp if cfg['use_eff_rain'] else rawp
        popen=pond_p_mm*ap/1000.
        su+=pup; e1=min(su,s85.ET_UPLAND*etoi*s85.A_UPLAND/1000.); su-=e1
        dex=max(su-s85.C_UPLAND,0.); su-=dex
        sw+=pwet
        exposed=max(s85.A0-ah0,0.); bg=max(aw-exposed,0.)
        e2=min(sw,etoi*(s85.K_BG*bg+s85.K_BARE*exposed)/1000.); sw-=e2
        dw=max(sw-s85.C_WET,0.); sw-=dw
        local=dex*s85.LOCAL_FRAC; deep=dex-local
        fast+=local*s85.FAST_FRAC; slow+=local*(1-s85.FAST_FRAC)
        qf=min(fast,fast/s85.TAU_FAST); qs=min(slow,slow/s85.TAU_SLOW_D); fast-=qf; slow-=qs; qr=qf+qs
        surf+=popen+dw+qr
        aloss=s85.area_v(surf)
        evap_mm=(0.8*ep) if cfg['use_eff_evap'] else ep
        eo_p=evap_mm*aloss/1000.
        qo_p=(surf/s85.TAU_SURF) if cfg['use_surface_outflow'] else 0.
        # Legacy qg = 4 mm/day × area. Canonical old-model seepage assumption:
        # 1% of effective pond precipitation on that same day's pond area.
        qg_p=(s85.K_GW_MM_D*aloss/1000.) if cfg['use_legacy_gw'] else (0.01*pp*aloss/1000.)
        lp=eo_p+qo_p+qg_p; fac=min(1.,surf/lp) if lp>0 else 1.
        eo=eo_p*fac; qo=qo_p*fac; qg=qg_p*fac; surf-=eo+qo+qg
        if surf<0 and surf>-1e-12: surf=0.
        total=su+sw+fast+slow+surf; inputs=pup+pwet+popen; outputs=e1+e2+eo+deep+qo+qg
        err=prev+inputs-outputs-total; maxerr=max(maxerr,abs(err)); prev=total
        rows.append({'DATE':r.DATE,'V_m3':surf,'area_m2':s85.area_v(surf),'qev_m3':eo,'qout_m3':qo,'qgw_m3':qg,'qret_m3':qr,'deep_m3':deep})
    out=pd.DataFrame(rows); out['DATE']=pd.to_datetime(out.DATE)
    return out,maxerr


def metrics(out):
    preds={}; errs=[]
    for y in YEARS:
        g=out[(out.DATE.dt.year==y)&(out.DATE.dt.month.isin([4,5]))]
        p=float(g.area_m2.mean()); preds[y]=p; errs.append(p-OBS[y])
    rmse=float(np.sqrt(np.mean(np.square(errs)))); nrmse=100*rmse/np.mean(list(OBS.values()))
    z=out.V_m3<=1e-9
    marapr=out.DATE.dt.month.isin([3,4])
    return preds,rmse,nrmse,int(z.sum()),int((z&marapr).sum()),float(out.V_m3.max())


def main():
    df=forcing_frame(); summary=[]; predrows=[]
    for name,cfg in VARIANTS.items():
        out,me=run_variant(df,cfg); pred,rmse,nrmse,zd,sd,vmax=metrics(out)
        for y,p in pred.items(): predrows.append({'variant':name,'year':y,'pred_m2':p,'obs_m2':OBS[y],'error_m2':p-OBS[y]})
        summary.append({'variant':name,'RMSE_m2':rmse,'nRMSE_pct':nrmse,'zero_surface_days':zd,'MarApr_zero_days':sd,'max_V_m3':vmax,'max_mass_error_m3':me,
                        'use_eff_rain':cfg['use_eff_rain'],'use_eff_evap':cfg['use_eff_evap'],'surface_outflow':cfg['use_surface_outflow'],'legacy_4mm_gw':cfg['use_legacy_gw']})
        out.to_csv(OUT/f'{name}_daily.csv',index=False)
    s=pd.DataFrame(summary).sort_values('nRMSE_pct'); p=pd.DataFrame(predrows)
    s.to_csv(OUT/'stage87_summary.csv',index=False); p.to_csv(OUT/'stage87_predictions.csv',index=False)
    print(s.to_string(index=False)); print('\nPredictions:\n',p.pivot(index='year',columns='variant',values='pred_m2').to_string())
    audit={'status':'PASS_STAGE87_POND_CONTRACT_ABLATION','parameter_fitting':False,'catchment_structure_changed':False,
           'only_pond_side_terms_tested':['effective pond precipitation 0.87P','effective evaporation 0.8 Penman','surface outflow removal','legacy 4 mm/day loss replacement with 1% effective-P seepage'],
           'max_mass_error_m3':float(s.max_mass_error_m3.max())}
    (OUT/'stage87_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8'); print(json.dumps(audit,indent=2))

if __name__=='__main__': main()
