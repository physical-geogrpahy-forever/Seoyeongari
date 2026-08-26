#!/usr/bin/env python3
"""Numerically equivalent vectorized runner for Stage41.

Only the affine daily recurrence evaluation is vectorized. Candidate grids,
physical model, observation operator, fitting, and every acceptance gate remain
unchanged from stage41_direct_area_operator.py.
"""
import numpy as np
import pandas as pd
import stage41_direct_area_operator as s41
from stage35c_mass_balance_state_operator import A0


def fast_bidirectional_hydroperiod_state(area,r_est_yr,r_flood_yr,lag_d=28):
    a=np.asarray(area,float)
    E=pd.Series(np.clip((A0-a)/A0,0,1)).rolling(int(lag_d),min_periods=1).mean().to_numpy()
    F=pd.Series(np.clip(a/A0,0,1)).rolling(int(lag_d),min_periods=1).mean().to_numpy()
    ae=float(r_est_yr)/365.;af=float(r_flood_yr)/365.
    # x_i = q_i*x_(i-1)+b_i, x_-1=0; exact affine form of Stage40 recursion.
    q=1.-ae*E-af*F;b=ae*E
    P=np.cumprod(q)
    x=P*np.cumsum(b/P)
    x=np.clip(x,0.,1.)
    xp=np.r_[0.,x[:-1]]
    up=ae*E*(1.-xp);dn=af*F*xp
    return {'state':x,'exposure':E,'flood':F,'establishment_flux':up,
      'reversal_flux':dn,'total_establishment':float(up.sum()),
      'total_reversal':float(dn.sum()),'max_reversal_daily':float(dn.max())}

# build_candidates resolves this module-global name at runtime.
s41.bidirectional_hydroperiod_state=fast_bidirectional_hydroperiod_state

if __name__=='__main__':
    s41.main()
