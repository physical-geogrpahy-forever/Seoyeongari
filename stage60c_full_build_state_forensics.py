#!/usr/bin/env python3
"""Stage60c — compare direct central features with the exact Stage49 full-build cache path.

Runs build_candidates() but does not fit/rank candidates. The target candidate is
located by the locked Stage60 process parameters, and its stored S/H features are
fingerprinted against a fresh direct calculation before and after the full build.
"""
from __future__ import annotations
import hashlib,json,os,platform
from pathlib import Path
import numpy as np
import pandas as pd

import stage49_six_observation_irreversible_recruitment as s49
from stage31_topmodel_vsa import forcing
from stage38_domain_corrected import hydro
from stage35c_mass_balance_state_operator import A0
from stage56_aprmay_recalibration import annual_aprmay, annual_hydro_aprmay

OUT=Path('stage60c_outputs');OUT.mkdir(exist_ok=True)
TARGET={'V0':1000.0,'p_shape':18.0,'tau_surf':60.0,'local_frac':0.45,'tau_fast':30.0,'k_gw_mm_d':4.0,
        'r_est_yr':0.05,'hydro_window_d':14.0,'est_window_d':7.0}


def sha(a):
    x=np.ascontiguousarray(np.asarray(a,dtype='<f8'));return hashlib.sha256(x.tobytes()).hexdigest()

def direct(F):
    hp={k:TARGET[k] for k in s49.HKEYS};h=hydro(F,hp);a=np.asarray(h['area'],float)
    exposed=np.clip((A0-a)/A0,0.0,1.0)
    e=pd.Series(exposed).rolling(7,min_periods=7).min().fillna(0.0).to_numpy()
    st=s49.irreversible_state(e,.05)
    S=annual_aprmay(h['dates'],st);H=annual_hydro_aprmay(h['dates'],h['return_flow'],14)
    return {'V':sha(h['V']),'area':sha(a),'return_flow':sha(h['return_flow']),'exposed':sha(exposed),'E7':sha(e),'state':sha(st),'S':sha(S),'H':sha(H),
            'S_values':[float(x) for x in S],'H_values':[float(x) for x in H]}

def match(c):
    return all(abs(float(c[k])-float(v))<1e-15 for k,v in TARGET.items())

def main():
    s49.annual=annual_aprmay;s49.annual_hydro=annual_hydro_aprmay
    F,_,_=forcing();before=direct(F)
    cands,internal,hcache=s49.build_candidates(F)
    hits=[c for c in cands if match(c)]
    if len(hits)!=1: raise SystemExit(f'expected one target candidate, got {len(hits)}')
    c=hits[0];stored={'S':sha(c['S']),'H':sha(c['H']),'S_values':[float(x) for x in c['S']],'H_values':[float(x) for x in c['H']]}
    hpkey=tuple(TARGET[k] for k in s49.HKEYS);hc=hcache[hpkey]
    cached_hydro={'V':sha(hc['V']),'area':sha(hc['area']),'return_flow':sha(hc['return_flow'])}
    after=direct(F)
    summary={'status':'PASS_STAGE60C_FULL_BUILD_FORENSICS','runner':{'platform':platform.platform(),'replica':os.environ.get('REPLICA','')},
             'n_candidates':len(cands),'before_direct':before,'stored_target_candidate':stored,'cached_target_hydro':cached_hydro,'after_direct':after,
             'comparisons':{
               'before_vs_stored_S_equal':before['S']==stored['S'],'before_vs_stored_H_equal':before['H']==stored['H'],
               'before_vs_cached_V_equal':before['V']==cached_hydro['V'],'before_vs_cached_area_equal':before['area']==cached_hydro['area'],
               'before_vs_cached_return_equal':before['return_flow']==cached_hydro['return_flow'],
               'before_vs_after_all_equal':all(before[k]==after[k] for k in ['V','area','return_flow','exposed','E7','state','S','H'])}}
    (OUT/'stage60c_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
