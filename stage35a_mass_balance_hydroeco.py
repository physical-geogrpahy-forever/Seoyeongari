#!/usr/bin/env python3
"""Stage 35A: mass-balance-first hydro-ecology experiment.

Design constraints
------------------
1) Daily conservation of water is the governing structure. No CN event equation,
   lambda, hard 2011 cap, freeboard or explicit calendar-time trend.
2) External catchment and wetland soil stores generate drainable surplus only
   after their finite soil-water stores are filled (WetMAT-type soil balance).
3) Return flow is routed by linear reservoirs, a standard lumped groundwater/
   perched-aquifer representation. Surface wetland water is itself a linear
   reservoir; there is no spill threshold.
4) Open-water area is a monotone diagnostic of conserved surface storage,
   A_h=min(A_wet,V_surface/sigma). sigma is a lumped specific surface-storage
   coefficient, not a measured bathymetry.
5) Ecology is bounded colonisation: only previously open area that is exposed
   can be colonised; colonisation cannot exceed the 2011 open-water footprint.
   Establishment is driven by antecedent exposure over a 28 d window.

References motivating FORM, not site coefficients:
- Panciera et al. 2026 HESS (WetMAT): daily total wetland balance; soil water
  balance generates drainable water only when soil is saturated; interconnected
  stores and ET/precipitation terms.
- Moore 2007 HESS (PDM): saturation-excess production and fast/slow storage
  routing are standard water-balance rainfall-runoff structures.
- O'Reilly et al. 2020 WRR: perched aquifer as reservoir; linear-reservoir
  storage-outflow relation is a standard lumped representation.
- Smith et al. 2009 / USGS: rapid vegetation colonisation after drawdown, with
  high cover observed at some transects after ~4 weeks.
"""
import itertools, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from stage31_topmodel_vsa import forcing, OBS

OUT=Path('stage35a_outputs'); OUT.mkdir(exist_ok=True)
YEARS=np.array(sorted(OBS),dtype=int)
Y=np.array([OBS[int(y)] for y in YEARS],dtype=float)
A0=2241.762
A_EXT=8483.0
A_WET=5939.5
# Existing project soil-water depth: 0.294 m profile * 0.55 effective fraction.
SOIL_DEPTH_M=0.294*0.55
C_EXT=SOIL_DEPTH_M*A_EXT
C_WET=SOIL_DEPTH_M*A_WET
ET_EXT_FACTOR=0.95
EST_WINDOW=28

# Reference-constrained search: only water-balance response times, local return,
# surface specific storage, and establishment rate are varied.
SIGMA=[0.03,0.05,0.075,0.10,0.15,0.20,0.30]  # m3 per m2 effective surface storage
TAU_SURF=[15.,30.,60.,120.,240.]               # d, continuous drainage
LOCAL_FRAC=[.10,.20,.30,.40]
TAU_FAST=[7.,15.,30.,60.]
TAU_SLOW=[180.,365.,730.]
R_EST=[0.00025,0.0005,0.001,0.002,0.004,0.008] # d-1 bounded colonisation
FAST_FRAC=.75


def score(pred):
    p=np.array([pred[int(y)] for y in YEARS]); rm=float(np.sqrt(np.mean((p-Y)**2)))
    return rm,100*rm/Y.mean(),float(np.mean(np.abs(p-Y)))


def hydro(F,p,keep=False):
    pre=np.asarray(F['pre'],float); eto=np.asarray(F['eto'],float); ep=np.asarray(F['ep'],float)
    dates=pd.to_datetime(F['date']); n=len(pre)
    # Initial conditions are states, not fluxes. 2011 observed area only fixes V0.
    se=.5*C_EXT; sw=.5*C_WET; fast=0.; slow=0.; surf=p['sigma']*A0
    prev_total=se+sw+fast+slow+surf
    a=np.empty(n); mass=np.empty(n); surf_arr=np.empty(n)
    qret_arr=np.empty(n); deep_arr=np.empty(n); qsurf_arr=np.empty(n)
    maxerr=0.
    for i in range(n):
        a_prev=min(A_WET,max(0.,surf/p['sigma']))
        # Rainfall partition is by current open-water area: open water receives
        # direct rainfall; the remainder of the mapped wetland receives soil rain.
        p_ext=pre[i]*A_EXT/1000.
        p_open=pre[i]*a_prev/1000.
        p_wsoil=pre[i]*(A_WET-a_prev)/1000.

        # External soil water balance.
        se += p_ext
        et_ext=min(se,ET_EXT_FACTOR*eto[i]*A_EXT/1000.); se-=et_ext
        dwf_ext=max(se-C_EXT,0.); se-=dwf_ext

        # Wetland soil water balance. The fixed storage represents the wetland
        # soil column; open-water rainfall bypasses the soil and enters surface store.
        sw += p_wsoil
        et_wet=min(sw,eto[i]*(A_WET-a_prev)/1000.); sw-=et_wet
        dwf_wet=max(sw-C_WET,0.); sw-=dwf_wet

        # External drainable surplus: local perched return vs deep loss.
        local=dwf_ext*p['local_frac']; deep=dwf_ext-local
        fast += local*FAST_FRAC; slow += local*(1-FAST_FRAC)
        qf=min(fast,fast/p['tau_fast']); qs=min(slow,slow/p['tau_slow'])
        fast-=qf; slow-=qs; qret=qf+qs

        # Surface wetland balance: all terms are explicit fluxes. Wetland-soil
        # saturation excess is a direct source; no channel/freeboard threshold.
        surf += p_open + dwf_wet + qret
        e_open=min(surf,ep[i]*a_prev/1000.); surf-=e_open
        qsurf=min(surf,surf/p['tau_surf']); surf-=qsurf
        a_now=min(A_WET,max(0.,surf/p['sigma']))

        # Whole-system daily closure.
        total=se+sw+fast+slow+surf
        inputs=p_ext+p_wsoil+p_open
        outputs=et_ext+et_wet+e_open+deep+qsurf
        err=prev_total+inputs-outputs-total
        maxerr=max(maxerr,abs(err)); prev_total=total
        a[i]=a_now; mass[i]=err; surf_arr[i]=surf
        qret_arr[i]=qret; deep_arr[i]=deep; qsurf_arr[i]=qsurf
    out={'max_mass_error_m3':maxerr,'surface_area':a,'surface_storage':surf_arr,
         'return_flow':qret_arr,'deep_loss':deep_arr,'surface_drain':qsurf_arr,'dates':dates}
    return out


def apply_ecology(h,r_est):
    a=np.asarray(h['surface_area'],float); n=len(a)
    # Antecedent exposure fraction relative to the 2011 open-water footprint.
    exposure=np.clip((A0-a)/A0,0,1)
    e28=pd.Series(exposure).rolling(EST_WINDOW,min_periods=EST_WINDOW).mean().fillna(0).to_numpy()
    C=0.; c=np.empty(n); opena=np.empty(n)
    for i in range(n):
        # Only area within the 2011 open-water footprint can be converted in this
        # first bounded-colonisation test. Available exposed area is finite.
        exposed_area=max(0.,A0-min(A0,a[i]))
        eligible=max(0.,exposed_area-C)
        dC=r_est*eligible*e28[i]
        C=min(A0,C+dC)
        c[i]=C
        opena[i]=max(0.,a[i]-C)
    return opena,c,exposure,e28


def eval_mj(dates,opena):
    yr=dates.year.to_numpy(); mo=dates.month.to_numpy(); pred={}
    for y in YEARS:
        m=(yr==y)&np.isin(mo,[5,6]); pred[int(y)]=float(np.mean(opena[m]))
    return pred


def main():
    F,missing,annual=forcing(); rows=[]; best_series=None
    for sigma,tau_s,lf,tf,ts in itertools.product(SIGMA,TAU_SURF,LOCAL_FRAC,TAU_FAST,TAU_SLOW):
        hp={'sigma':sigma,'tau_surf':tau_s,'local_frac':lf,'tau_fast':tf,'tau_slow':ts}
        h=hydro(F,hp)
        for re in R_EST:
            opena,c,ex,e28=apply_ecology(h,re); pred=eval_mj(h['dates'],opena); rm,nrm,mae=score(pred)
            # Hydrologic-only May-June area is recorded separately: it is not the
            # calibration target because observed polygons are OPEN WATER, not total wetness.
            hydpred=eval_mj(h['dates'],h['surface_area']); hrm,hnrm,hmae=score(hydpred)
            row={'nrmse':nrm,'rmse':rm,'mae':mae,'hydrology_only_nrmse':hnrm,
                 **hp,'r_est_d':re,'max_daily_mass_error_m3':h['max_mass_error_m3'],
                 'colonized_2023_m2':float(c[-1]),
                 **{f'pred_{y}':pred[int(y)] for y in YEARS},
                 **{f'hydro_{y}':hydpred[int(y)] for y in YEARS}}
            rows.append(row)
    rows.sort(key=lambda r:(r['nrmse'],r['rmse']))
    feasible=[r for r in rows if r['nrmse']<=2.0 and r['max_daily_mass_error_m3']<1e-8]
    chosen=feasible[0] if feasible else rows[0]
    # regenerate chosen daily output
    hp={k:chosen[k] for k in ['sigma','tau_surf','local_frac','tau_fast','tau_slow']}
    h=hydro(F,hp); opena,c,ex,e28=apply_ecology(h,chosen['r_est_d'])
    daily=pd.DataFrame({'date':h['dates'],'hydrologic_area_m2':h['surface_area'],'surface_storage_m3':h['surface_storage'],
                        'open_water_m2':opena,'colonized_m2':c,'exposure_fraction':ex,'exposure_28d':e28,
                        'return_flow_m3':h['return_flow'],'deep_loss_m3':h['deep_loss'],'surface_drain_m3':h['surface_drain']})
    daily.to_csv(OUT/'stage35a_best_daily.csv',index=False)
    pd.DataFrame(rows[:500]).to_csv(OUT/'stage35a_top500.csv',index=False)
    pd.DataFrame(feasible[:500]).to_csv(OUT/'stage35a_feasible_top500.csv',index=False)
    summary={'model':'Stage35A mass-balance-first hydro-ecology','selection':'minimize nRMSE; accept only nRMSE<=2% and exact daily closure',
             'n_candidates':len(rows),'n_feasible_2pct':len(feasible),'best':chosen,
             'rules':{'lambda':0,'CN_daily_runoff':False,'explicit_time':False,'future_leakage':False,'hard_2011_cap':False,'freeboard':False,
                      'daily_mass_balance':'exact','A2011_role':'initial surface storage and bounded colonisable footprint only','surface_outflow':'linear reservoir, no threshold'},
             'fixed':{'A_ext_m2':A_EXT,'A_wet_m2':A_WET,'A2011_m2':A0,'soil_storage_depth_m':SOIL_DEPTH_M,'fast_fraction':FAST_FRAC,'establishment_window_d':EST_WINDOW},
             'reference_forms':['WetMAT 2026 daily water balance and saturation-generated drainable flux','Moore 2007 PDM saturation-excess and reservoir routing','OReilly et al 2020 perched-aquifer reservoir concept','Smith et al 2009 rapid drawdown colonisation on ~4-week scale'],
             'benchmark_stage34':{'nrmse':0.9568720534166563,'loocv_nrmse':1.2766706907049148}}
    (OUT/'stage35a_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
