#!/usr/bin/env python3
"""Stage61a — test minimal numerical canonicalization of A(V).

The physical hypsometric law is unchanged:
    A = min(A_WET, A0 * (V/V0) ** (2/(p+2))).
Hosted runners can use different libm implementations for fractional power, and
that last-bit difference is recursively fed back through daily area-dependent
fluxes. We test decimal rounding of the *computed area only* at four resolutions
that are all vastly finer than the 0.5-m imagery and mapped-area precision.

This stage does not calibrate anything. The smallest resolution yielding the
same fingerprints across runners will be eligible for the canonical pipeline.
"""
from __future__ import annotations
import hashlib,json,os,platform
from pathlib import Path
import numpy as np
import pandas as pd

import stage38_domain_corrected as h38
from stage31_topmodel_vsa import forcing
from stage35c_mass_balance_state_operator import A0,A_WET
from stage49_six_observation_irreversible_recruitment import irreversible_state,YEARS
from stage56_aprmay_recalibration import annual_aprmay,annual_hydro_aprmay

OUT=Path('stage61a_outputs');OUT.mkdir(exist_ok=True)
P={'V0':1000.0,'p_shape':18.0,'tau_surf':60.0,'local_frac':0.45,'tau_fast':30.0,'k_gw_mm_d':4.0}
TESTS={'raw':None,'round12':12,'round10':10,'round9':9,'round8':8}

def sha(a):
    return hashlib.sha256(np.ascontiguousarray(np.asarray(a,dtype='<f8')).tobytes()).hexdigest()

def make_area(ndigits):
    def f(v,V0,p):
        if v<=0:return 0.0
        raw=min(A_WET,A0*(v/V0)**(2.0/(p+2.0)))
        return raw if ndigits is None else round(raw,ndigits)
    return f

def main():
    F,_,_=forcing();rows=[]
    original=h38.area_v
    try:
        for label,nd in TESTS.items():
            h38.area_v=make_area(nd)
            h=h38.hydro(F,P)
            area=np.asarray(h['area'],float);V=np.asarray(h['V'],float)
            exposed=np.clip((A0-area)/A0,0.0,1.0)
            E=pd.Series(exposed).rolling(7,min_periods=7).min().fillna(0.0).to_numpy()
            st=irreversible_state(E,.05)
            S=annual_aprmay(h['dates'],st);H=annual_hydro_aprmay(h['dates'],h['return_flow'],14)
            rows.append({
              'label':label,'area_decimal_digits':nd,
              'V_sha256':sha(V),'area_sha256':sha(area),'return_flow_sha256':sha(h['return_flow']),
              'S_sha256':sha(S),'H_sha256':sha(H),
              'S':[float(x) for x in S],'H':[float(x) for x in H],
              'mass_error_m3':float(h['mass_error']),'area_partition_error_m2':float(h['area_partition_error']),
              'precip_partition_error_m3':float(h['precip_partition_error'])})
    finally:
        h38.area_v=original
    summary={'status':'PASS_STAGE61A_TEST','runner':{'platform':platform.platform(),'replica':os.environ.get('REPLICA','')},
             'physical_equation_changed':False,
             'rounding_role':'numerical canonicalization after fractional-power evaluation only; not a fitted parameter',
             'tests':rows}
    (OUT/'stage61a_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
