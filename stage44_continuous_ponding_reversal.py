#!/usr/bin/env python3
"""Stage44 — bidirectional ecology with 100-d continuously inundated fraction.

Stage40-43 applied reversal pressure from ordinary inundation. Wetland ecology
literature indicates duration/continuity of inundation is a key discriminator:
Casanova & Brock (2000; doi:10.1023/A:1009875226637) found lowest biomass and
richness under continuous flooding and emphasized individual flood duration;
Slusher et al. (2014; doi:10.2134/jeq2013.06.0227) explicitly contrasted 100-d
continuous ponding with 14-d intermittent ponding and found high mortality in
less tolerant taxa under the 100-d treatment.

For a nested wetted footprint, min(I) over the trailing 100 d, where
I=clip(A/A0,0,1), is the fraction of the 2011 reference footprint that remained
continuously inundated for the entire interval. No arbitrary depth threshold is
introduced. Establishment remains driven by trailing 28-d exposed fraction.
Hydrology, observation operator, strict gates, nested CV, and 2022 sealing are
unchanged from Stage40/42.
"""
import json, shutil
from pathlib import Path
import numpy as np
import pandas as pd
import stage40_bidirectional_hydroperiod as s40
from stage35c_mass_balance_state_operator import A0

OUT=Path('stage44_outputs');OUT.mkdir(exist_ok=True)
CONTINUOUS_PONDING_D=100
GRIDS={
 'V0':[1000.,1600.,2200.], 'p_shape':[6.,12.,18.],
 'tau_surf':[60.,120.,240.], 'local_frac':[.15,.30,.45],
 'tau_fast':[30.,60.,120.],
 'k_gw_mm_d':[.02,.05,.10,.25,1.,2.,4.],
 'r_est_yr':[.01,.025,.05,.10,.25,.50],
 'r_flood_yr':[.002,.005,.01,.025,.05,.10,.25,.50,1.,2.,4.],
 'hydro_window_d':[7,14,30,60,90,180,365],
}

def continuous_ponding_state(area,r_est_yr,r_flood_yr,lag_d=28):
    a=np.asarray(area,float)
    E=pd.Series(np.clip((A0-a)/A0,0,1)).rolling(int(lag_d),min_periods=1).mean().to_numpy()
    I=np.clip(a/A0,0,1)
    # Fraction continuously inundated throughout the previous 100 days.
    Fc=(pd.Series(I).rolling(CONTINUOUS_PONDING_D,min_periods=CONTINUOUS_PONDING_D)
        .min().fillna(0.).to_numpy())
    x=0.;st=np.empty(len(a));upv=np.empty(len(a));dnv=np.empty(len(a))
    ae=float(r_est_yr)/365.;af=float(r_flood_yr)/365.
    for i,(e,f) in enumerate(zip(E,Fc)):
        up=ae*e*(1.-x);dn=af*f*x;x=float(np.clip(x+up-dn,0,1))
        st[i]=x;upv[i]=up;dnv[i]=dn
    return {'state':st,'exposure':E,'flood':Fc,'establishment_flux':upv,'reversal_flux':dnv,
      'total_establishment':float(upv.sum()),'total_reversal':float(dnv.sum()),
      'max_reversal_daily':float(dnv.max())}

def relabel():
    src=OUT/'stage40_summary.json'
    if not src.exists():return
    d=json.loads(src.read_text(encoding='utf-8'))
    d['model']='Stage44 100-day continuous-ponding reversal hydroperiod ecology'
    d['continuous_ponding_days']=CONTINUOUS_PONDING_D
    d['stage44_change']='reversal stress = trailing-100d minimum inundated fraction; all hydrology/gates unchanged'
    d['holdout_2022_used']=False
    (OUT/'stage44_summary.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    p=OUT/'stage40_rejection_diagnostics.csv'
    if p.exists():shutil.copy2(p,OUT/'stage44_rejection_diagnostics.csv')

def main():
    s40.GRIDS=GRIDS;s40.OUT=OUT;s40.bidirectional_hydroperiod_state=continuous_ponding_state
    code=None
    try:s40.main()
    except SystemExit as e:code=e
    finally:relabel()
    if code is not None:raise code

if __name__=='__main__':main()
