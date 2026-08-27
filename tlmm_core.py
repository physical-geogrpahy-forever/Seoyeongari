#!/usr/bin/env python3
"""Published Twin Limit Marsh Model (TLMM) transition equations.

Source
------
Keddy, P.A. & Campbell, D. (2020). The Twin Limit Marsh Model: A
Non-equilibrium Approach to Predicting Marsh Vegetation on Shorelines and in
Floodplains. Wetlands 40, 667–680. DOI: 10.1007/s13157-019-01229-9.

This module intentionally contains only processes stated in the paper:
* one growing season of dewatering is sufficient for marsh establishment on
  newly exposed sediment;
* exponential marsh loss under continuous flooding using f and cmin;
* exponential marsh loss under continuous dewatering/woody succession using
  s and wmin;
* annual growing-season water-level history supplies the site-specific
  durations dt and xt.

No EGHM pond-area fit parameter, exposure score, GDD score, logistic curve, or
hybrid succession law is introduced here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence

C_MIN_DEFAULT = 0.01
W_MIN_DEFAULT = 0.001
F_TEMPERATE_YR = 4.0
S_TEMPERATE_YR = 30.0
S_GREAT_LAKES_EXAMPLE_YR = 15.0


def _validate_positive(name: str, x: float) -> float:
    x=float(x)
    if not math.isfinite(x) or x <= 0.0:
        raise ValueError(f"{name} must be finite and >0")
    return x


def _validate_minimum(name: str, x: float) -> float:
    x=float(x)
    if not math.isfinite(x) or not (0.0 < x < 1.0):
        raise ValueError(f"{name} must be in (0,1)")
    return x


def marsh_remaining_after_flooding(dt_yr: float, f_yr: float = F_TEMPERATE_YR,
                                    cmin: float = C_MIN_DEFAULT) -> float:
    """Relative marsh remaining after continuous flooding (TLMM lower limit).

    Paper definitions: f is the number of years of continuous flooding needed
    to eliminate marsh; dt is the site-specific duration of continuous
    flooding at an elevation. The paper defines the relative decline cd on a
    log10 scale and rescales remaining marsh by (1-cd)/(1-cmin).
    """
    f=_validate_positive("f_yr",f_yr); cmin=_validate_minimum("cmin",cmin)
    dt=max(float(dt_yr),0.0)
    if dt >= f:
        return 0.0
    # cd runs from cmin at dt=0 to 1 at dt=f.
    cd = 10.0 ** ((-math.log10(cmin)) * ((dt - f) / f))
    return min(max((1.0 - cd) / (1.0 - cmin),0.0),1.0)


def marsh_remaining_after_dewatering(xt_yr: float, s_yr: float = S_TEMPERATE_YR,
                                      wmin: float = W_MIN_DEFAULT) -> float:
    """Relative marsh remaining during woody succession (TLMM upper limit).

    Paper definitions: s is years from dewatering to closed-canopy woody
    vegetation; xt is years the elevation has been dewatered and subject to
    woody succession. wx is the published log-scale relative marsh decline,
    rescaled by (1-wx)/(1-wmin).
    """
    s=_validate_positive("s_yr",s_yr); wmin=_validate_minimum("wmin",wmin)
    xt=max(float(xt_yr),0.0)
    if xt >= s:
        return 0.0
    wx = 10.0 ** ((-math.log10(wmin)) * ((xt - s) / s))
    return min(max((1.0 - wx) / (1.0 - wmin),0.0),1.0)


@dataclass(frozen=True)
class TLMMBandYear:
    year: int
    flooded: bool
    dt_flood_yr: float
    xt_dewater_yr: float
    marsh_fraction: float
    aquatic_fraction: float
    woody_fraction: float


def band_history(years: Sequence[int], growing_season_water_levels: Sequence[float],
                 elevation: float, *, f_yr: float = F_TEMPERATE_YR,
                 s_yr: float = S_TEMPERATE_YR,
                 cmin: float = C_MIN_DEFAULT, wmin: float = W_MIN_DEFAULT,
                 initially_open_water: bool = True) -> List[TLMMBandYear]:
    """Apply the TLMM annual water-level rules to one elevation.

    For a study initialized from a mapped open-water pond, `initially_open_water`
    sets pre-model flooding duration to at least f, so the mapped 2011 aquatic
    state is respected. Once a growing season is dewatered, the paper's rule
    that one growing season is sufficient for marsh establishment applies.

    Consecutive annual flooding/dewatering durations are the TLMM site-specific
    dt/xt terms derived from water-level history. They are reset when the water
    level crosses the elevation; no fractional winter exposure is accumulated.
    """
    if len(years) != len(growing_season_water_levels):
        raise ValueError("years and water levels must have equal length")
    f=_validate_positive("f_yr",f_yr); s=_validate_positive("s_yr",s_yr)
    z=float(elevation)
    dt=f if initially_open_water else 0.0
    xt=0.0
    out=[]
    first=True
    for y,wl in zip(years,growing_season_water_levels):
        flooded=float(wl) >= z
        if flooded:
            # If the band was initially mapped as open water, preserve that
            # state until a dewatering event occurs. Thereafter, flooding acts
            # on marsh according to the published lower-limit curve.
            if first and initially_open_water:
                dt=f
            else:
                dt = dt + 1.0 if xt == 0.0 else 1.0
            xt=0.0
            m=marsh_remaining_after_flooding(dt,f,cmin)
            aq=1.0-m; wood=0.0
        else:
            xt = xt + 1.0 if dt == 0.0 else 1.0
            dt=0.0
            # One growing season of drawdown creates marsh; the same first
            # dewatered year is xt=1 in the published upper-limit succession
            # clock, whose exponential curve is nearly unity at its start.
            m=marsh_remaining_after_dewatering(xt,s,wmin)
            wood=1.0-m; aq=0.0
        out.append(TLMMBandYear(int(y),flooded,dt,xt,m,aq,wood))
        first=False
    return out


def assert_partition(rows: Iterable[TLMMBandYear], tol: float = 1e-12) -> None:
    for r in rows:
        if abs((r.marsh_fraction+r.aquatic_fraction+r.woody_fraction)-1.0)>tol:
            raise AssertionError(f"TLMM cover partition failed in {r.year}")
