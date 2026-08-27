#!/usr/bin/env python3
"""Official deterministic numerical kernel for the Seoyeongari EGHM model.

Scientific structure is the Stage49/56 mass-conserved hydro-ecology model.
This module only fixes numerical evaluation order so the same source data and
parameters produce the same binary64 trajectory on heterogeneous CPUs.

Key implementation rules
------------------------
* forcing: eghm_deterministic_forcing (80-digit transcendental evaluation)
* storage-area geometry: exact rational roots, no platform fractional libm pow
* daily recurrence: CPython binary64 scalar arithmetic in fixed order
* ecology: fixed-order 7-d continuous-exposure minimum and irreversible state
* hydrologic feature: fixed-order trailing return-flow sum relative to 2011
* temporal support: April-May for the current mapped-area observation contract

No rounding lattice, relaxation, time trend, future leakage, 2022 area target,
or fitted numerical stabilizer is introduced here.
"""
from __future__ import annotations

from collections import deque
import hashlib
import math
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_geometry import area_v_deterministic

# Fixed physical/domain constants inherited from the accepted Stage38/49 path.
A0 = 2241.762
A_WET = 5939.5
A_EXT_2011 = 8483.0
A_WET_MARGIN_2011 = A_WET - A0
A_UPLAND = A_EXT_2011 - A_WET_MARGIN_2011
A_DOMAIN = A_UPLAND + A_WET
SOIL_DEPTH = 0.294 * 0.55
C_UPLAND = SOIL_DEPTH * A_UPLAND
C_WET = SOIL_DEPTH * A_WET
ET_UPLAND = 0.95
FAST_FRAC = 0.75
TAU_SLOW_D = 365.0

EVAL_YEARS: Tuple[int, ...] = (2013, 2015, 2017, 2019, 2021, 2023)
OBS_MONTHS: Tuple[int, ...] = (4, 5)
REFERENCE_YEAR = 2011

SELECTED_STRUCTURE: Dict[str, float] = {
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


def sha256_f8(values: Iterable[float]) -> str:
    arr = np.asarray(list(values), dtype='<f8')
    return hashlib.sha256(arr.tobytes(order='C')).hexdigest()


def mean_fsum(values: Iterable[float]) -> float:
    vals = [float(v) for v in values]
    if not vals:
        raise ValueError('empty deterministic mean')
    return math.fsum(vals) / float(len(vals))


def rolling_min_complete(values: Sequence[float], window: int) -> List[float]:
    """Trailing minimum with min_periods=window; pre-window values are zero."""
    vals = [float(v) for v in values]
    w = int(window)
    if w < 1:
        raise ValueError('window must be >=1')
    out = [0.0] * len(vals)
    for i in range(w - 1, len(vals)):
        out[i] = min(vals[i - w + 1:i + 1])
    return out


def rolling_sum_fixed(values: Sequence[float], window: int) -> List[float]:
    """Trailing sum with min_periods=1 in a fixed scalar add/subtract order."""
    vals = [float(v) for v in values]
    w = int(window)
    if w < 1:
        raise ValueError('window must be >=1')
    out = [0.0] * len(vals)
    q: deque[float] = deque()
    acc = 0.0
    for i, x in enumerate(vals):
        q.append(x)
        acc = acc + x
        if len(q) > w:
            acc = acc - q.popleft()
        out[i] = acc
    return out


def hydro(forcing: Mapping[str, Sequence[float]], p: Mapping[str, float]) -> Dict[str, object]:
    """Exact non-overlap daily water balance in a fixed binary64 scalar order."""
    pre = [float(x) for x in forcing['pre']]
    eto = [float(x) for x in forcing['eto']]
    ep = [float(x) for x in forcing['ep']]
    dates = pd.to_datetime(forcing['date'])
    n = len(pre)
    if not (len(eto) == len(ep) == len(dates) == n):
        raise ValueError('forcing arrays must have equal length')

    required = ('V0', 'p_shape', 'tau_surf', 'local_frac', 'tau_fast', 'k_gw_mm_d')
    hp = {k: float(p[k]) for k in required}

    su = float(0.5 * C_UPLAND)
    sw = float(0.5 * C_WET)
    fast = 0.0
    slow = 0.0
    surf = hp['V0']
    prev = su + sw + fast + slow + surf

    area = [0.0] * n
    volume = [0.0] * n
    qret = [0.0] * n
    qgw = [0.0] * n
    qout = [0.0] * n
    qev = [0.0] * n
    max_mass_error = 0.0
    max_area_error = 0.0
    max_precip_error = 0.0

    def av(v: float) -> float:
        return area_v_deterministic(v, hp['V0'], hp['p_shape'], A0=A0, A_WET=A_WET)

    for i in range(n):
        pi = pre[i]
        etoi = eto[i]
        epi = ep[i]

        ap = av(surf)
        aw = max(A_WET - ap, 0.0)
        pup = pi * A_UPLAND / 1000.0
        pwet = pi * aw / 1000.0
        popen = pi * ap / 1000.0
        max_area_error = max(max_area_error, abs((A_UPLAND + aw + ap) - A_DOMAIN))
        max_precip_error = max(
            max_precip_error,
            abs((pup + pwet + popen) - pi * A_DOMAIN / 1000.0),
        )

        su = su + pup
        e1 = min(su, ET_UPLAND * etoi * A_UPLAND / 1000.0)
        su = su - e1
        dex = max(su - C_UPLAND, 0.0)
        su = su - dex

        sw = sw + pwet
        e2 = min(sw, etoi * aw / 1000.0)
        sw = sw - e2
        dw = max(sw - C_WET, 0.0)
        sw = sw - dw

        local = dex * hp['local_frac']
        deep = dex - local
        fast = fast + local * FAST_FRAC
        slow = slow + local * (1.0 - FAST_FRAC)
        qf = min(fast, fast / hp['tau_fast'])
        qs = min(slow, slow / TAU_SLOW_D)
        fast = fast - qf
        slow = slow - qs
        qr = qf + qs
        surf = surf + popen + dw + qr

        # Concurrent surface losses from the same pre-loss state.
        aloss = av(surf)
        eo_p = epi * aloss / 1000.0
        qo_p = surf / hp['tau_surf']
        qg_p = hp['k_gw_mm_d'] * aloss / 1000.0
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
        max_mass_error = max(max_mass_error, abs(err))
        prev = total

        area[i] = an
        volume[i] = surf
        qret[i] = qr
        qgw[i] = qg
        qout[i] = qo
        qev[i] = eo

    return {
        'dates': dates,
        'area': area,
        'V': volume,
        'return_flow': qret,
        'groundwater_loss': qgw,
        'surface_outflow': qout,
        'surface_evaporation': qev,
        'mass_error': max_mass_error,
        'area_partition_error': max_area_error,
        'precip_partition_error': max_precip_error,
    }


def continuous_exposure_state(
    area: Sequence[float],
    r_est_yr: float,
    window_d: int,
) -> Dict[str, List[float]]:
    """Irreversible establishment driven by continuous antecedent exposure."""
    exposed = [min(max((A0 - float(a)) / A0, 0.0), 1.0) for a in area]
    exposure_window = rolling_min_complete(exposed, int(window_d))
    rate_d = float(r_est_yr) / 365.0
    survival = 1.0
    state = [0.0] * len(exposure_window)
    for i, e in enumerate(exposure_window):
        q = min(max(1.0 - rate_d * e, 0.0), 1.0)
        survival = survival * q
        state[i] = 1.0 - survival
    return {'exposed': exposed, 'exposure_window': exposure_window, 'state': state}


def annual_support(
    dates: Sequence[object],
    values: Sequence[float],
    years: Sequence[int] = EVAL_YEARS,
    months: Sequence[int] = OBS_MONTHS,
) -> List[float]:
    dt = pd.to_datetime(dates)
    yy = [int(x) for x in dt.year]
    mm = [int(x) for x in dt.month]
    months_set = set(int(m) for m in months)
    vals = [float(v) for v in values]
    out: List[float] = []
    for y in years:
        subset = [vals[i] for i in range(len(vals)) if yy[i] == int(y) and mm[i] in months_set]
        out.append(mean_fsum(subset))
    return out


def hydrologic_feature(
    dates: Sequence[object],
    flux: Sequence[float],
    window_d: int,
    years: Sequence[int] = EVAL_YEARS,
    months: Sequence[int] = OBS_MONTHS,
    reference_year: int = REFERENCE_YEAR,
) -> List[float]:
    dt = pd.to_datetime(dates)
    yy = [int(x) for x in dt.year]
    mm = [int(x) for x in dt.month]
    months_set = set(int(m) for m in months)
    roll = rolling_sum_fixed(flux, int(window_d))
    ref = mean_fsum(
        roll[i] for i in range(len(roll))
        if yy[i] == int(reference_year) and mm[i] in months_set
    )
    out: List[float] = []
    for y in years:
        subset = [roll[i] for i in range(len(roll)) if yy[i] == int(y) and mm[i] in months_set]
        out.append(mean_fsum(subset) - ref)
    return out


def build_features(
    forcing: Mapping[str, Sequence[float]],
    p: Mapping[str, float],
    years: Sequence[int] = EVAL_YEARS,
    months: Sequence[int] = OBS_MONTHS,
) -> Dict[str, object]:
    h = hydro(forcing, p)
    eco = continuous_exposure_state(h['area'], float(p['r_est_yr']), int(p['est_window_d']))
    S = annual_support(h['dates'], eco['state'], years=years, months=months)
    H = hydrologic_feature(
        h['dates'], h['return_flow'], int(p['hydro_window_d']),
        years=years, months=months, reference_year=REFERENCE_YEAR,
    )
    return {'hydro': h, 'ecology': eco, 'S': S, 'H': H}


def selected_run() -> Tuple[Mapping[str, Sequence[float]], Dict[str, object]]:
    forcing, _, _, _ = deterministic_forcing()
    return forcing, build_features(forcing, SELECTED_STRUCTURE)


def zero_storage_diagnostics(dates: Sequence[object], volume: Sequence[float]) -> Dict[str, object]:
    dt = pd.to_datetime(dates)
    yy = [int(x) for x in dt.year]
    mm = [int(x) for x in dt.month]
    z = [float(v) <= 1e-9 for v in volume]
    total = sum(1 for q in z if q)
    spring = sum(1 for i, q in enumerate(z) if q and mm[i] in (3, 4))
    by_year = {}
    for y in range(2011, 2024):
        by_year[str(y)] = {
            'zero_storage_days': sum(1 for i, q in enumerate(z) if q and yy[i] == y),
            'mar_apr_zero_storage_days': sum(
                1 for i, q in enumerate(z) if q and yy[i] == y and mm[i] in (3, 4)
            ),
        }
    return {
        'zero_storage_days_total': total,
        'mar_apr_zero_storage_days_total': spring,
        'spring_share_of_zero_days': (spring / total if total else None),
        'by_year': by_year,
    }
