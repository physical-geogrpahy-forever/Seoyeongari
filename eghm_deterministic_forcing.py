#!/usr/bin/env python3
"""Deterministic meteorological forcing for the Seoyeongari EGHM model.

This module reproduces the Stage30 forcing equations while eliminating CPU-
dispatched NumPy transcendental functions.  Raw decimal strings are parsed
exactly, missing AWS temperature/wind values are linearly interpolated in fixed
order, and FAO-56 / Penman terms are evaluated with mpmath at fixed precision.
Only the final daily forcing values are rounded to IEEE-754 binary64.

Scientific equations and meteorological constants are unchanged.  Numerical
implementation is changed solely to make the forcing reproducible across
heterogeneous runners.
"""
from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import mpmath as mp
import numpy as np
import pandas as pd

AWS = Path('OBS_AWS_DD_20250930013603.csv')
ASOS = Path('OBS_ASOS_DD_20250930041037.csv')

LAT = Decimal('33.30456')
ALT = Decimal('188.42')
CN = Decimal('68')
MP_DPS = 80


def _open_text_fallback(path: Path):
    raw = path.read_bytes()
    for enc in ('cp949', 'utf-8-sig', 'utf-8'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    raise RuntimeError(f'cannot decode {path}')


def _dec(s: Optional[str]) -> Optional[Decimal]:
    if s is None:
        return None
    s = str(s).strip()
    if s == '' or s.lower() in {'nan', 'na', 'null', 'none'}:
        return None
    return Decimal(s)


def _interp_fixed(vals: List[Optional[Decimal]]) -> List[Decimal]:
    """Equivalent intent to pandas interpolate(limit_direction='both')."""
    known = [i for i, v in enumerate(vals) if v is not None]
    if not known:
        raise ValueError('cannot interpolate an all-missing meteorological series')
    out: List[Optional[Decimal]] = list(vals)
    first, last = known[0], known[-1]
    for i in range(0, first):
        out[i] = vals[first]
    for i in range(last + 1, len(vals)):
        out[i] = vals[last]
    with localcontext() as ctx:
        ctx.prec = 50
        for left, right in zip(known[:-1], known[1:]):
            vl = vals[left]
            vr = vals[right]
            assert vl is not None and vr is not None
            gap = right - left
            if gap <= 1:
                continue
            dv = vr - vl
            den = Decimal(gap)
            for i in range(left + 1, right):
                out[i] = vl + dv * Decimal(i - left) / den
    return [v if v is not None else Decimal('0') for v in out]


def _read_raw() -> Tuple[List[datetime], Dict[str, List[Decimal]], Dict[str, int]]:
    aws_text = _open_text_fallback(AWS)
    reader = csv.DictReader(aws_text.splitlines())
    rows = []
    for r in reader:
        dt = datetime.strptime(r['time'].strip(), '%Y-%m-%d')
        if datetime(2011, 1, 1) <= dt <= datetime(2023, 12, 31):
            rows.append((dt, r))
    rows.sort(key=lambda z: z[0])

    # ASOS daily sunshine: exact decimal average per date, then zero when absent.
    asos_text = _open_text_fallback(ASOS)
    ar = csv.DictReader(asos_text.splitlines())
    sun_sum: Dict[datetime, Decimal] = {}
    sun_n: Dict[datetime, int] = {}
    for r in ar:
        if 'time' not in r or 'hour' not in r:
            continue
        try:
            dt = datetime.strptime(str(r['time']).strip(), '%Y-%m-%d')
        except Exception:
            continue
        # Match legacy Stage30: filter station 189 only when decoded header is '지점'.
        if '지점' in r:
            try:
                if int(str(r['지점']).strip()) != 189:
                    continue
            except Exception:
                continue
        h = _dec(r.get('hour'))
        if h is None:
            continue
        sun_sum[dt] = sun_sum.get(dt, Decimal('0')) + h
        sun_n[dt] = sun_n.get(dt, 0) + 1

    dates = [dt for dt, _ in rows]
    raw: Dict[str, List[Optional[Decimal]]] = {k: [] for k in ('tmean', 'tmin', 'tmax', 'pre', 'wind')}
    for _, r in rows:
        for k in raw:
            raw[k].append(_dec(r.get(k)))

    raw_missing = {k: sum(v is None for v in raw[k]) for k in raw}
    raw_missing['sun'] = sum(dt not in sun_n for dt in dates)

    pre = [(v if v is not None else Decimal('0')) for v in raw['pre']]
    pre = [max(v, Decimal('0')) for v in pre]
    tmean = _interp_fixed(raw['tmean'])
    tmin = _interp_fixed(raw['tmin'])
    tmax = _interp_fixed(raw['tmax'])
    wind = _interp_fixed(raw['wind'])
    sun = [
        (sun_sum[dt] / Decimal(sun_n[dt])) if dt in sun_n else Decimal('0')
        for dt in dates
    ]
    return dates, {
        'tmean': tmean, 'tmin': tmin, 'tmax': tmax,
        'pre': pre, 'wind': wind, 'sun': sun,
    }, raw_missing


def _m(d: Decimal) -> mp.mpf:
    return mp.mpf(str(d))


def _clip_m(x: mp.mpf, lo: mp.mpf, hi: mp.mpf) -> mp.mpf:
    return lo if x < lo else hi if x > hi else x


def deterministic_forcing():
    dates, x, raw_missing = _read_raw()
    mp.mp.dps = MP_DPS

    pi = mp.pi
    lat = _m(LAT) * pi / mp.mpf('180')
    alt = _m(ALT)
    P = mp.mpf('101.3') * ((mp.mpf('293') - mp.mpf('0.0065') * alt) / mp.mpf('293')) ** mp.mpf('5.26')
    ga = mp.mpf('0.000665') * P
    lam = mp.mpf('2.45')
    sig = mp.mpf('4.903e-9')
    S_cn = mp.mpf('25400') / mp.mpf('68') - mp.mpf('254')
    IA = mp.mpf('0.2') * S_cn
    wind_height_log = mp.log(mp.mpf('67.8') * mp.mpf('2') - mp.mpf('5.42'))

    def e0(t: mp.mpf) -> mp.mpf:
        return mp.mpf('0.6108') * mp.exp(mp.mpf('17.27') * t / (t + mp.mpf('237.3')))

    def delta(t: mp.mpf) -> mp.mpf:
        return mp.mpf('4098') * e0(t) / (t + mp.mpf('237.3')) ** 2

    pre_out: List[float] = []
    pes_out: List[float] = []
    eto_out: List[float] = []
    ep_out: List[float] = []
    pp_out: List[float] = []

    for dt, tmean_d, tmin_d, tmax_d, pre_d, wind_d, sun_d in zip(
        dates, x['tmean'], x['tmin'], x['tmax'], x['pre'], x['wind'], x['sun']
    ):
        doy = mp.mpf(str(dt.timetuple().tm_yday))
        tm = _m(tmean_d); tn = _m(tmin_d); tx = _m(tmax_d)
        pr = _m(pre_d); wi = _m(wind_d); su = _m(sun_d)

        dr = mp.mpf('1') + mp.mpf('0.033') * mp.cos(mp.mpf('2') * pi * doy / mp.mpf('365'))
        dec = mp.mpf('0.409') * mp.sin(mp.mpf('2') * pi * doy / mp.mpf('365') - mp.mpf('1.39'))
        arg = -mp.tan(lat) * mp.tan(dec)
        arg = _clip_m(arg, mp.mpf('-1'), mp.mpf('1'))
        ws = mp.acos(arg)
        ra = (mp.mpf('24') * mp.mpf('60') / pi) * mp.mpf('0.082') * dr * (
            ws * mp.sin(lat) * mp.sin(dec) + mp.cos(lat) * mp.cos(dec) * mp.sin(ws)
        )
        N = (mp.mpf('24') / pi) * ws
        u2 = wi * mp.mpf('4.87') / wind_height_log
        rso = (mp.mpf('0.75') + mp.mpf('2e-5') * alt) * ra
        nN = _clip_m(su / max(N, mp.mpf('1e-6')), mp.mpf('0'), mp.mpf('1'))
        rs = (mp.mpf('0.25') + mp.mpf('0.50') * nN) * ra

        es = (e0(tx) + e0(tn)) / mp.mpf('2')
        ea = e0(tn)
        D = delta(tm)
        f = _clip_m(rs / max(rso, mp.mpf('1e-6')), mp.mpf('0'), mp.mpf('1'))
        rnl = sig * (((tx + mp.mpf('273.16')) ** 4 + (tn + mp.mpf('273.16')) ** 4) / mp.mpf('2')) * (
            mp.mpf('0.34') - mp.mpf('0.14') * mp.sqrt(max(ea, mp.mpf('0')))
        ) * (mp.mpf('1.35') * f - mp.mpf('0.35'))
        rnveg = (mp.mpf('1') - mp.mpf('0.23')) * rs - rnl
        rnwat = (mp.mpf('1') - mp.mpf('0.08')) * rs - rnl

        eto = (
            mp.mpf('0.408') * D * rnveg
            + ga * (mp.mpf('900') / (tm + mp.mpf('273'))) * u2 * (es - ea)
        ) / (D + ga * (mp.mpf('1') + mp.mpf('0.34') * u2))
        eto = max(eto, mp.mpf('0'))
        ep = (
            (D / (D + ga)) * (rnwat / lam)
            + (ga / (D + ga)) * (mp.mpf('6.43') * (mp.mpf('1') + mp.mpf('0.536') * u2) / lam) * (es - ea)
        )
        ep = max(ep, mp.mpf('0'))

        pes = mp.mpf('0') if pr <= IA else (pr - IA) ** 2 / (pr + mp.mpf('0.8') * S_cn)
        pre_out.append(float(pr))
        pes_out.append(float(pes))
        eto_out.append(float(eto))
        ep_out.append(float(ep))
        pp_out.append(float(mp.mpf('0.87') * pr))

    years = np.asarray([d.year for d in dates], dtype=int)
    months = np.asarray([d.month for d in dates], dtype=int)
    date_arr = np.asarray(dates, dtype='datetime64[ns]')
    F = {
        'pre': np.asarray(pre_out, dtype=float),
        'pes': np.asarray(pes_out, dtype=float),
        'eto': np.asarray(eto_out, dtype=float),
        'ep': np.asarray(ep_out, dtype=float),
        'pp': np.asarray(pp_out, dtype=float),
        'year': years,
        'month': months,
        'date': date_arr,
    }

    annual: Dict[int, float] = {}
    with localcontext() as ctx:
        ctx.prec = 50
        for y in range(2011, 2024):
            annual[y] = float(sum((x['pre'][i] for i, d in enumerate(dates) if d.year == y), Decimal('0')))
    cleaned = {
        k: np.asarray([float(v) for v in x[k]], dtype=float)
        for k in ('tmean', 'tmin', 'tmax', 'pre', 'wind', 'sun')
    }
    return F, raw_missing, annual, cleaned


# Compatibility alias for code that expects forcing().
def forcing():
    F, missing, annual, _ = deterministic_forcing()
    return F, missing, annual
