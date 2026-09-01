#!/usr/bin/env python3
"""Stage61b — test deterministic rational-power geometry across runners.

No calibration is performed.  The Stage56/60 selected hydrologic/ecologic
structure is held fixed.  We compare the legacy libm-pow hydro trajectory with
an otherwise identical trajectory using eghm_deterministic_geometry.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
from pathlib import Path

import numpy as np
import pandas as pd

from stage31_topmodel_vsa import forcing
from stage35c_mass_balance_state_operator import A0, A_WET, SOIL_DEPTH, ET_EXT, FAST_FRAC, TAU_SLOW
from stage38_domain_corrected import hydro as hydro_legacy
from eghm_deterministic_geometry import area_v_deterministic, nth_root_ieee

OUT = Path('stage61b_outputs')
OUT.mkdir(exist_ok=True)

A_EXT_2011 = 8483.0
A_WET_MARGIN_2011 = A_WET - A0
A_UPLAND = A_EXT_2011 - A_WET_MARGIN_2011
A_DOMAIN = A_UPLAND + A_WET
C_UPLAND = SOIL_DEPTH * A_UPLAND
C_WET = SOIL_DEPTH * A_WET
YEARS = np.array([2013, 2015, 2017, 2019, 2021, 2023], int)
MONTHS = [4, 5]

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
    a = np.asarray(a, dtype='<f8')
    return hashlib.sha256(a.tobytes(order='C')).hexdigest()


def hydro_det(F, p):
    pre = np.asarray(F['pre'], float)
    eto = np.asarray(F['eto'], float)
    ep = np.asarray(F['ep'], float)
    dt = pd.to_datetime(F['date'])
    n = len(pre)
    su = 0.5 * C_UPLAND
    sw = 0.5 * C_WET
    fast = slow = 0.0
    surf = float(p['V0'])
    prev = su + sw + fast + slow + surf
    area = np.empty(n)
    V = np.empty(n)
    qret = np.empty(n)
    qgw = np.empty(n)
    qout = np.empty(n)
    qev = np.empty(n)
    maxerr = max_area_err = max_p_err = 0.0

    def av(v):
        return area_v_deterministic(v, p['V0'], p['p_shape'], A0=A0, A_WET=A_WET)

    for i in range(n):
        ap = av(surf)
        aw = max(A_WET - ap, 0.0)
        pup = pre[i] * A_UPLAND / 1000.0
        pwet = pre[i] * aw / 1000.0
        popen = pre[i] * ap / 1000.0
        area_err = abs((A_UPLAND + aw + ap) - A_DOMAIN)
        max_area_err = max(max_area_err, area_err)
        p_err = abs((pup + pwet + popen) - pre[i] * A_DOMAIN / 1000.0)
        max_p_err = max(max_p_err, p_err)

        su += pup
        e1 = min(su, ET_EXT * eto[i] * A_UPLAND / 1000.0)
        su -= e1
        dex = max(su - C_UPLAND, 0.0)
        su -= dex

        sw += pwet
        e2 = min(sw, eto[i] * aw / 1000.0)
        sw -= e2
        dw = max(sw - C_WET, 0.0)
        sw -= dw

        local = dex * p['local_frac']
        deep = dex - local
        fast += local * FAST_FRAC
        slow += local * (1.0 - FAST_FRAC)
        qf = min(fast, fast / p['tau_fast'])
        qs = min(slow, slow / TAU_SLOW)
        fast -= qf
        slow -= qs
        qr = qf + qs
        surf += popen + dw + qr

        aloss = av(surf)
        eo_p = ep[i] * aloss / 1000.0
        qo_p = surf / p['tau_surf']
        qg_p = p['k_gw_mm_d'] * aloss / 1000.0
        loss_p = eo_p + qo_p + qg_p
        fac = min(1.0, surf / loss_p) if loss_p > 0.0 else 1.0
        eo = eo_p * fac
        qo = qo_p * fac
        qg = qg_p * fac
        surf -= eo + qo + qg
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


def features(h):
    dt = pd.to_datetime(h['dates'])
    yr = dt.year.to_numpy()
    mo = dt.month.to_numpy()
    a = np.asarray(h['area'], float)
    exposed = np.clip((A0 - a) / A0, 0.0, 1.0)
    ew = int(SELECTED['est_window_d'])
    E = pd.Series(exposed).rolling(ew, min_periods=ew).min().fillna(0.0).to_numpy()
    rate = float(SELECTED['r_est_yr']) / 365.0
    q = np.clip(1.0 - rate * E, 0.0, 1.0)
    state = 1.0 - np.cumprod(q)
    S = np.array([
        float(np.mean(state[(yr == y) & np.isin(mo, MONTHS)])) for y in YEARS
    ])

    hw = int(SELECTED['hydro_window_d'])
    rr = pd.Series(np.asarray(h['return_flow'], float), index=dt).rolling(hw, min_periods=1).sum().to_numpy()
    ref = float(np.mean(rr[(yr == 2011) & np.isin(mo, MONTHS)]))
    H = np.array([
        float(np.mean(rr[(yr == y) & np.isin(mo, MONTHS)]) - ref) for y in YEARS
    ])
    return exposed, E, state, S, H


def pack(h):
    exposed, E, state, S, H = features(h)
    return {
        'fingerprints': {
            'V': sha(h['V']),
            'area': sha(h['area']),
            'return_flow': sha(h['return_flow']),
            'exposed': sha(exposed),
            'E7': sha(E),
            'state': sha(state),
            'S': sha(S),
            'H': sha(H),
        },
        'S': [float(x) for x in S],
        'H': [float(x) for x in H],
        'physical_closure': {
            'mass_error_m3': float(h['mass_error']),
            'area_partition_error_m2': float(h['area_partition_error']),
            'precip_partition_error_m3': float(h['precip_partition_error']),
        },
    }


def main():
    F, missing, _ = forcing()
    hp = {k: SELECTED[k] for k in ['V0', 'p_shape', 'tau_surf', 'local_frac', 'tau_fast', 'k_gw_mm_d']}
    legacy = hydro_legacy(F, hp)
    det = hydro_det(F, hp)
    legacy_pack = pack(legacy)
    det_pack = pack(det)

    ratios = [
        2.0**-40, 2.0**-20, 2.0**-10, 0.125, 0.5, 0.75, 1.0,
        1.25, 2.0, 4.0, 16.0, 256.0, 2.0**20, 2.0**40,
    ]
    residuals = []
    for n in (4, 7, 10):
        for x in ratios:
            r = nth_root_ieee(x, n)
            residuals.append(abs((r ** n) - x) / x)

    result = {
        'status': 'PASS_STAGE61B_DETERMINISTIC_GEOMETRY_FORENSICS',
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
        'scientific_equation_changed': False,
        'general_fractional_pow_removed': True,
        'newton_iterations_fixed': 12,
        'legacy': legacy_pack,
        'deterministic': det_pack,
        'legacy_vs_deterministic': {
            'max_abs_V_m3': float(np.max(np.abs(np.asarray(legacy['V']) - np.asarray(det['V'])))),
            'max_abs_area_m2': float(np.max(np.abs(np.asarray(legacy['area']) - np.asarray(det['area'])))),
            'max_abs_return_flow_m3': float(np.max(np.abs(np.asarray(legacy['return_flow']) - np.asarray(det['return_flow'])))),
        },
        'root_equation_max_relative_residual': float(max(residuals)),
    }
    (OUT / 'stage61b_summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if max(result['deterministic']['physical_closure'].values()) > 1e-8:
        raise SystemExit('deterministic geometry broke physical closure')
    if result['root_equation_max_relative_residual'] > 5e-15:
        raise SystemExit('deterministic integer-root residual is too large')


if __name__ == '__main__':
    main()
