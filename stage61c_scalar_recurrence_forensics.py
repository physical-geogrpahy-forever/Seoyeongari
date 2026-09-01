#!/usr/bin/env python3
"""Stage61c — remove NumPy scalar/reduction paths from the frozen EGHM trajectory.

Stage61b showed that replacing fractional libm pow alone was insufficient:
even upland return flow (which is independent of pond geometry) split between
heterogeneous runners.  The cause is that forcing values were kept as
np.float64 scalars, so the daily recurrence inherited NumPy CPU-dispatched
scalar arithmetic.

This forensic implementation keeps the scientific equations unchanged but:
- converts each forcing datum once to CPython float (binary64),
- uses the deterministic rational-power geometry,
- evaluates all daily state recurrences with CPython float operations,
- evaluates the 7-d rolling minimum and 14-d rolling sum in fixed order,
- evaluates annual April-May means with math.fsum,
- evaluates irreversible recruitment as a fixed-order scalar cumulative product.

No calibration or parameter selection is performed here.
"""
from __future__ import annotations

from collections import deque
import hashlib
import json
import math
import os
import platform
from pathlib import Path

import numpy as np
import pandas as pd

from stage31_topmodel_vsa import forcing
from stage35c_mass_balance_state_operator import A0, A_WET, SOIL_DEPTH, ET_EXT, FAST_FRAC, TAU_SLOW
from eghm_deterministic_geometry import area_v_deterministic

OUT = Path('stage61c_outputs')
OUT.mkdir(exist_ok=True)

A_EXT_2011 = 8483.0
A_WET_MARGIN_2011 = A_WET - A0
A_UPLAND = A_EXT_2011 - A_WET_MARGIN_2011
A_DOMAIN = A_UPLAND + A_WET
C_UPLAND = SOIL_DEPTH * A_UPLAND
C_WET = SOIL_DEPTH * A_WET
YEARS = (2013, 2015, 2017, 2019, 2021, 2023)
MONTHS = (4, 5)

SELECTED = {
    'V0': 1000.0,
    'p_shape': 18.0,
    'tau_surf': 60.0,
    'local_frac': 0.45,
    'tau_fast': 30.0,
    'k_gw_mm_d': 4.0,
    'r_est_yr': 0.05,
    'est_window_d': 7,
    'hydro_window_d': 14,
}


def sha(a):
    arr = np.asarray(a, dtype='<f8')
    return hashlib.sha256(arr.tobytes(order='C')).hexdigest()


def mean_fsum(values):
    vals = [float(v) for v in values]
    if not vals:
        raise ValueError('empty deterministic mean')
    return math.fsum(vals) / float(len(vals))


def rolling_min_fixed(values, window):
    values = [float(x) for x in values]
    w = int(window)
    out = [0.0] * len(values)
    # Exact Stage49 support: min_periods=window, then missing -> 0.
    for i in range(w - 1, len(values)):
        out[i] = min(values[i - w + 1:i + 1])
    return out


def rolling_sum_fixed(values, window):
    values = [float(x) for x in values]
    w = int(window)
    out = [0.0] * len(values)
    q = deque()
    s = 0.0
    for i, x in enumerate(values):
        q.append(x)
        s = s + x
        if len(q) > w:
            s = s - q.popleft()
        out[i] = s
    return out


def hydro_scalar(F, p):
    # Critical determinism step: Python float lists, not np.float64 scalar views.
    pre = [float(x) for x in F['pre']]
    eto = [float(x) for x in F['eto']]
    ep = [float(x) for x in F['ep']]
    dt = pd.to_datetime(F['date'])
    n = len(pre)

    su = float(0.5 * C_UPLAND)
    sw = float(0.5 * C_WET)
    fast = 0.0
    slow = 0.0
    surf = float(p['V0'])
    prev = su + sw + fast + slow + surf

    area = [0.0] * n
    V = [0.0] * n
    qret = [0.0] * n
    qgw = [0.0] * n
    qout = [0.0] * n
    qev = [0.0] * n
    maxerr = 0.0
    max_area_err = 0.0
    max_p_err = 0.0

    def av(v):
        return area_v_deterministic(
            float(v), float(p['V0']), float(p['p_shape']), A0=float(A0), A_WET=float(A_WET)
        )

    for i in range(n):
        pi = pre[i]
        etoi = eto[i]
        epi = ep[i]

        ap = av(surf)
        aw = max(float(A_WET) - ap, 0.0)
        pup = pi * float(A_UPLAND) / 1000.0
        pwet = pi * aw / 1000.0
        popen = pi * ap / 1000.0
        area_err = abs((float(A_UPLAND) + aw + ap) - float(A_DOMAIN))
        max_area_err = max(max_area_err, area_err)
        p_err = abs((pup + pwet + popen) - pi * float(A_DOMAIN) / 1000.0)
        max_p_err = max(max_p_err, p_err)

        su = su + pup
        e1 = min(su, float(ET_EXT) * etoi * float(A_UPLAND) / 1000.0)
        su = su - e1
        dex = max(su - float(C_UPLAND), 0.0)
        su = su - dex

        sw = sw + pwet
        e2 = min(sw, etoi * aw / 1000.0)
        sw = sw - e2
        dw = max(sw - float(C_WET), 0.0)
        sw = sw - dw

        local = dex * float(p['local_frac'])
        deep = dex - local
        fast = fast + local * float(FAST_FRAC)
        slow = slow + local * (1.0 - float(FAST_FRAC))
        qf = min(fast, fast / float(p['tau_fast']))
        qs = min(slow, slow / float(TAU_SLOW))
        fast = fast - qf
        slow = slow - qs
        qr = qf + qs
        surf = surf + popen + dw + qr

        aloss = av(surf)
        eo_p = epi * aloss / 1000.0
        qo_p = surf / float(p['tau_surf'])
        qg_p = float(p['k_gw_mm_d']) * aloss / 1000.0
        loss_p = eo_p + qo_p + qg_p
        fac = min(1.0, surf / loss_p) if loss_p > 0.0 else 1.0
        eo = eo_p * fac
        qo = qo_p * fac
        qg = qg_p * fac
        surf = surf - (eo + qo + qg)
        if surf < 0.0 and surf > -1e-12:
            surf = 0.0

        an = av(surf)
        total = su + sw + fast + slow + surf
        inputs = pup + pwet + popen
        outputs = e1 + e2 + eo + deep + qo + qg
        err = prev + inputs - outputs - total
        maxerr = max(maxerr, abs(err))
        prev = total

        area[i] = an
        V[i] = surf
        qret[i] = qr
        qgw[i] = qg
        qout[i] = qo
        qev[i] = eo

    return {
        'dates': dt,
        'area': area,
        'V': V,
        'return_flow': qret,
        'groundwater_loss': qgw,
        'surface_outflow': qout,
        'surface_evaporation': qev,
        'mass_error': maxerr,
        'area_partition_error': max_area_err,
        'precip_partition_error': max_p_err,
    }


def features_scalar(h):
    dt = pd.to_datetime(h['dates'])
    years = [int(x) for x in dt.year]
    months = [int(x) for x in dt.month]
    area = [float(x) for x in h['area']]

    exposed = [min(max((float(A0) - a) / float(A0), 0.0), 1.0) for a in area]
    E = rolling_min_fixed(exposed, int(SELECTED['est_window_d']))

    rate = float(SELECTED['r_est_yr']) / 365.0
    prod = 1.0
    state = [0.0] * len(E)
    for i, e in enumerate(E):
        q = min(max(1.0 - rate * e, 0.0), 1.0)
        prod = prod * q
        state[i] = 1.0 - prod

    S = []
    for y in YEARS:
        vals = [state[i] for i in range(len(state)) if years[i] == y and months[i] in MONTHS]
        S.append(mean_fsum(vals))

    rr = rolling_sum_fixed(h['return_flow'], int(SELECTED['hydro_window_d']))
    ref = mean_fsum([rr[i] for i in range(len(rr)) if years[i] == 2011 and months[i] in MONTHS])
    H = []
    for y in YEARS:
        vals = [rr[i] for i in range(len(rr)) if years[i] == y and months[i] in MONTHS]
        H.append(mean_fsum(vals) - ref)
    return exposed, E, state, S, H


def main():
    F, missing, _ = forcing()
    hp = {k: SELECTED[k] for k in ['V0', 'p_shape', 'tau_surf', 'local_frac', 'tau_fast', 'k_gw_mm_d']}
    h = hydro_scalar(F, hp)
    exposed, E, state, S, H = features_scalar(h)

    result = {
        'status': 'PASS_STAGE61C_SCALAR_RECURRENCE_FORENSICS',
        'runner': {
            'platform': platform.platform(),
            'machine': platform.machine(),
            'replica': os.environ.get('REPLICA', ''),
            'python': platform.python_version(),
            'numpy': np.__version__,
            'pandas': pd.__version__,
        },
        'forcing_missing': missing,
        'selected_structure_fixed_not_refit': SELECTED,
        'scientific_equations_changed': False,
        'implementation_changes': [
            'forcing scalars converted to CPython binary64 float before recurrence',
            'fractional storage-area pow replaced by exact-rational Newton root implementation',
            'rolling minimum/sum evaluated in fixed scalar order',
            'irreversible cumulative product evaluated in fixed scalar order',
            'April-May means evaluated with math.fsum',
        ],
        'fingerprints': {
            'forcing_pre': sha([float(x) for x in F['pre']]),
            'forcing_eto': sha([float(x) for x in F['eto']]),
            'forcing_ep': sha([float(x) for x in F['ep']]),
            'V': sha(h['V']),
            'area': sha(h['area']),
            'return_flow': sha(h['return_flow']),
            'exposed': sha(exposed),
            'E7': sha(E),
            'state': sha(state),
            'S': sha(S),
            'H': sha(H),
        },
        'S': S,
        'H': H,
        'physical_closure': {
            'mass_error_m3': float(h['mass_error']),
            'area_partition_error_m2': float(h['area_partition_error']),
            'precip_partition_error_m3': float(h['precip_partition_error']),
        },
    }
    (OUT / 'stage61c_summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if max(result['physical_closure'].values()) > 1e-8:
        raise SystemExit('Stage61c physical closure failed')


if __name__ == '__main__':
    main()
