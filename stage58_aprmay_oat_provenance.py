#!/usr/bin/env python3
"""Stage58 — April-May process-parameter OAT robustness and provenance.

This is the metadata-aligned successor to Stage52. The central model is Stage56
(April-May observation support; hydro_window=14 d) and the geomorphic central
rate is the field-derived 0.38 mm/yr Clymo long-term estimate.

Two questions remain separated:
A) FIXED: lock the central Stage57 Kc/Kh and perturb one process parameter.
B) PROFILE REFIT: refit only Kc/Kh after each process perturbation.

OAT values are inherited admissible calibration-search support, not independent
physical uncertainty intervals. Scenario rank is never an acceptance criterion.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd

import stage57_aprmay_four_scenario_peat as s57
from stage31_topmodel_vsa import forcing
from stage38_domain_corrected import hydro
from stage49_six_observation_irreversible_recruitment import irreversible_state

OUT=Path('stage58_outputs'); OUT.mkdir(exist_ok=True)
PEAT_RATE=0.38
CENTRAL=dict(s57.P56)

OAT={
 'V0':[1000.,1600.,2200.],
 'p_shape':[6.,12.,18.],
 'tau_surf':[60.,120.,240.],
 'local_frac':[.15,.30,.45],
 'tau_fast':[30.,60.,120.],
 'k_gw_mm_d':[.05,.10,.25,1.,2.,4.],
 'r_est_yr':[.025,.05,.10,.25],
 'hydro_window_d':[14,30,60,90,180],
 'est_window_d':[7,14,21],
}

PROVENANCE=[
 ('V0',1000.,'m3','calibrated effective geometry/storage scale'),
 ('p_shape',18.,'dimensionless','calibrated hypsometric shape parameter'),
 ('tau_surf',60.,'day','calibrated effective surface drainage/storage timescale'),
 ('local_frac',.45,'fraction','calibrated local perched-return routing fraction'),
 ('tau_fast',30.,'day','calibrated effective fast-return reservoir timescale'),
 ('k_gw_mm_d',4.,'mm day-1','calibrated effective area-proportional subsurface loss; not Ksat'),
 ('r_est_yr',.05,'yr-1','calibrated persistent occupation/establishment rate'),
 ('hydro_window_d',14,'day','calibrated causal antecedent return-flow feature window after April-May alignment'),
 ('est_window_d',7,'day','calibrated/literature-bounded continuous exposure timing parameter'),
 ('peat_rate_persistent',PEAT_RATE,'mm yr-1','field-derived Clymo-model long-term central estimate'),
]


def peat_loss(dt,V,P,rate=PEAT_RATE):
    dt=pd.to_datetime(dt); V=np.asarray(V,float)
    p=float(P['p_shape']); V0=float(P['V0'])
    h0=V0*(p+2.)/(s57.A0*p)
    ratio=np.maximum(V,0.)/V0
    h=h0*np.power(ratio,p/(p+2.))
    Ah=np.where(V>0,s57.A0*np.power(ratio,2./(p+2.)),0.); Ah=np.minimum(Ah,s57.A_WET)
    elapsed=np.maximum((dt-pd.Timestamp('2011-01-01')).days.to_numpy()/365.2425,0.)
    B=float(rate)/1000.*elapsed
    hr=np.maximum(h-B,0.)
    Ap=np.where(hr>0,s57.A0*np.power(hr/h0,2./p),0.); Ap=np.minimum(Ap,s57.A_WET)
    return np.maximum(Ah-Ap,0.)


def states(P):
    F,_,_=forcing()
    hp={k:P[k] for k in ['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']}
    h=hydro(F,hp)
    exposed=np.clip((s57.A0-np.asarray(h['area'],float))/s57.A0,0.,1.)
    ew=int(P['est_window_d'])
    E=pd.Series(exposed).rolling(ew,min_periods=ew).min().fillna(0.).to_numpy()
    st=irreversible_state(E,P['r_est_yr'])
    S=s57.aggregate(h['dates'],st)
    H=s57.hydro_feature(h['dates'],h['return_flow'],P['hydro_window_d'])
    G=s57.aggregate(h['dates'],peat_loss(h['dates'],h['V'],P))
    corr=float(np.corrcoef(S,s57.YEARS)[0,1]) if np.std(S)>1e-12 else 1.
    return h,S,H,G,corr


def central_coefficients():
    h,S,H,G,corr=states(CENTRAL)
    sc=s57.fit_scenarios(S,H,G)
    return {n:{'Kc':float(kc),'Kh':float(kh)} for n,kc,kh,*_ in sc},(h,S,H,G,corr)


def predict(name,S,H,G,kc,kh):
    if name=='Baseline Model': return s57.A0+kh*H
    if name=='Hydrosere Only Model': return s57.A0-kc*S+kh*H
    if name=='Eco-Geo Only Model': return s57.A0-G+kh*H
    if name=='Integrated Model': return s57.A0-kc*S-G+kh*H
    raise KeyError(name)


def rows_for(parameter,value,mode,cc):
    P=dict(CENTRAL); P[parameter]=value
    h,S,H,G,corr=states(P)
    if mode=='fixed':
        sc=[]
        for name,b in cc.items():
            pr=predict(name,S,H,G,b['Kc'],b['Kh']); rm,nr=s57.metric(pr)
            sc.append((name,b['Kc'],b['Kh'],pr,rm,nr))
    else:
        sc=s57.fit_scenarios(S,H,G)
    ranks={z[0]:i+1 for i,z in enumerate(sorted(sc,key=lambda z:z[5]))}
    out=[]
    for name,kc,kh,pr,rm,nr in sc:
        out.append({
          'mode':mode,'parameter':parameter,'value':float(value),
          'is_central_value':bool(abs(float(value)-float(CENTRAL[parameter]))<1e-12),
          'Scenario':name,'RMSE_m2':float(rm),'nRMSE_pct':float(nr),'rank':int(ranks[name]),
          'K_colonizable_m2':float(kc),'K_hydro_m_inv':float(kh),'state_year_corr':corr,
          'mass_error_m3':float(h['mass_error']),'area_partition_error_m2':float(h['area_partition_error']),
          'precip_partition_error_m3':float(h['precip_partition_error']),
          **{f'pred_{int(y)}':float(pr[i]) for i,y in enumerate(s57.YEARS)},
        })
    return out


def main():
    cc,central_state=central_coefficients(); h0,S0,H0,G0,corr0=central_state
    rows=[]
    for p,vals in OAT.items():
        for v in vals:
            rows += rows_for(p,v,'fixed',cc)
            rows += rows_for(p,v,'profile_refit',cc)
    df=pd.DataFrame(rows)
    df.to_csv(OUT/'stage58_oat_all.csv',index=False)
    df[df['mode']=='fixed'].to_csv(OUT/'stage58_oat_fixed.csv',index=False)
    df[df['mode']=='profile_refit'].to_csv(OUT/'stage58_oat_profile_refit.csv',index=False)

    prov=pd.DataFrame(PROVENANCE,columns=['parameter','central_value','unit','classification'])
    prov['central_at_edge_of_internal_oat_support']=prov['parameter'].map({p: bool(np.isclose(CENTRAL[p],min(v)) or np.isclose(CENTRAL[p],max(v))) for p,v in OAT.items()}).fillna(False)
    prov.to_csv(OUT/'stage58_parameter_provenance.csv',index=False)

    nc=df[~df.is_central_value]
    fi=nc[(nc['mode']=='fixed')&(nc.Scenario=='Integrated Model')]
    pi=nc[(nc['mode']=='profile_refit')&(nc.Scenario=='Integrated Model')]

    reversals=[]
    for mode in ['fixed','profile_refit']:
        x=nc[nc['mode']==mode]
        for (p,v),g in x.groupby(['parameter','value']):
            top=g.sort_values('nRMSE_pct').iloc[0]
            integ=g[g.Scenario=='Integrated Model'].iloc[0]
            if int(integ['rank'])!=1:
                reversals.append({
                  'mode':mode,'parameter':p,'value':float(v),
                  'top_scenario':str(top.Scenario),'top_nRMSE_pct':float(top.nRMSE_pct),
                  'Integrated_nRMSE_pct':float(integ.nRMSE_pct),
                  'difference_pp':float(integ.nRMSE_pct-top.nRMSE_pct),
                })
    pd.DataFrame(reversals).to_csv(OUT/'stage58_rank_reversals.csv',index=False)

    central=[]
    for name,b in cc.items():
        pr=predict(name,S0,H0,G0,b['Kc'],b['Kh']); rm,nr=s57.metric(pr)
        central.append({'Scenario':name,'RMSE_m2':rm,'nRMSE_pct':nr,'Kc':b['Kc'],'Kh':b['Kh']})
    central.sort(key=lambda z:z['nRMSE_pct'])

    summary={
      'status':'PASS_STAGE58_ANALYSIS','observation_support':'April-May','pond_area_observation_2022':'ABSENT',
      'central_process_parameters':CENTRAL,'central_peat_rate_mm_yr':PEAT_RATE,
      'oat_values_role':'internal admissible calibration-search support; not independent physical uncertainty intervals',
      'noncentral_setting_count':int(len(fi)),
      'fixed_integrated_rank1_count':int((fi['rank']==1).sum()),
      'profile_integrated_rank1_count':int((pi['rank']==1).sum()),
      'rank_reversals':reversals,'central_metrics':central,
      'parameters_central_at_edge_of_internal_oat_support':[p for p,v in OAT.items() if np.isclose(CENTRAL[p],min(v)) or np.isclose(CENTRAL[p],max(v))],
      'central_state_year_corr':corr0,
      'scenario_rank_not_acceptance_gate':True,
      'physical_closure':{'mass_error_m3':float(h0['mass_error']),'area_partition_error_m2':float(h0['area_partition_error']),'precip_partition_error_m3':float(h0['precip_partition_error'])},
    }
    (OUT/'stage58_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
