#!/usr/bin/env python3
"""Exact Twin Limit Marsh Model (TLMM) boundary-recursion equations.

Source
------
Keddy, P.A. & Campbell, D. (2020). The Twin Limit Marsh Model: A
Non-equilibrium Approach to Predicting Marsh Vegetation on Shorelines and in
Floodplains. Wetlands 40, 667–680. DOI: 10.1007/s13157-019-01229-9.

The implementation below was checked against the authors' official Springer
supplementary workbook (13157_2019_1229_MOESM1_ESM.xlsx). The workbook
recursively updates two elevation boundaries:

* MLL — marsh lower limit, controlled by continuous flooding duration dt;
* MUL — marsh upper limit, controlled by continuous dewatering duration xt.

The exact Excel recursions are reproduced here. No exposure score, GDD score,
logistic transition, pond-area fitting parameter, or hybrid succession rule is
introduced.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence

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
    """Workbook flooding response factor F=(1-cd)/(1-cmin)."""
    f=_validate_positive("f_yr",f_yr); cmin=_validate_minimum("cmin",cmin)
    dt=max(float(dt_yr),0.0)
    log_cd=(-math.log10(cmin))*((dt-f)/f)
    if log_cd >= 0.0:
        log_cd=0.0
    cd=10.0**log_cd
    return min(max((1.0-cd)/(1.0-cmin),0.0),1.0)


def marsh_remaining_after_dewatering(xt_yr: float, s_yr: float = S_TEMPERATE_YR,
                                      wmin: float = W_MIN_DEFAULT) -> float:
    """Workbook woody-succession response factor K=(1-wx)/(1-wmin)."""
    s=_validate_positive("s_yr",s_yr); wmin=_validate_minimum("wmin",wmin)
    xt=max(float(xt_yr),0.0)
    log_wx=(-math.log10(wmin))*((xt-s)/s)
    if log_wx >= 0.0:
        log_wx=0.0
    wx=10.0**log_wx
    return min(max((1.0-wx)/(1.0-wmin),0.0),1.0)


@dataclass(frozen=True)
class TLMMBoundaryYear:
    year: int
    water_level: float
    dt_flood_yr: int
    lower_response: float
    marsh_lower_limit: float
    xt_dewater_yr: int
    upper_response: float
    marsh_upper_limit: float


def lower_limit_step(water_level: float, previous_lower_limit: float,
                     previous_dt: int, *, f_yr: float = F_TEMPERATE_YR,
                     cmin: float = C_MIN_DEFAULT):
    """Exact MLL spreadsheet recurrence.

    C_t = IF(B_t > G_{t-1}, C_{t-1}+1, 0)
    D_t = IF(-LOG10(cmin)*(C_t-f)/f < 0, expression, 0)
    E_t = 10^D_t
    F_t = (1-E_t)/(1-cmin)
    G_t = IF(B_t <= G_{t-1}, B_t, B_t-F_t*(B_t-G_{t-1}))
    """
    wl=float(water_level); prev=float(previous_lower_limit)
    dt=int(previous_dt)+1 if wl>prev else 0
    response=marsh_remaining_after_flooding(dt,f_yr,cmin)
    lower=wl if wl<=prev else wl-response*(wl-prev)
    return dt,response,lower


def upper_limit_step(water_level: float, previous_upper_limit: float,
                     previous_xt: int, *, s_yr: float = S_TEMPERATE_YR,
                     wmin: float = W_MIN_DEFAULT):
    """Exact MUL spreadsheet recurrence.

    H_t = IF(B_t >= L_{t-1}, 0, H_{t-1}+1)
    I_t = IF(-LOG10(wmin)*(H_t-s)/s < 0, expression, 0)
    J_t = 10^I_t
    K_t = (1-J_t)/(1-wmin)
    L_t = IF(B_t >= L_{t-1}, B_t, B_t-K_t*(B_t-L_{t-1}))
    """
    wl=float(water_level); prev=float(previous_upper_limit)
    xt=0 if wl>=prev else int(previous_xt)+1
    response=marsh_remaining_after_dewatering(xt,s_yr,wmin)
    upper=wl if wl>=prev else wl-response*(wl-prev)
    return xt,response,upper


def boundary_history(years: Sequence[int], growing_season_water_levels: Sequence[float],
                     *, f_yr: float = F_TEMPERATE_YR,
                     s_yr: float = S_TEMPERATE_YR,
                     cmin: float = C_MIN_DEFAULT,
                     wmin: float = W_MIN_DEFAULT,
                     initial_lower_limit: Optional[float] = None,
                     initial_upper_limit: Optional[float] = None) -> List[TLMMBoundaryYear]:
    """Run the official workbook recurrence through an annual WL series.

    With no explicit initial limits, the first record initializes MLL=MUL to
    the first water level, exactly matching the supplementary workbook.

    Explicit initial limits are allowed because TLMM is a state-history model:
    a study with an observed starting vegetation boundary can initialize that
    state and use the same published recurrence thereafter. The first annual
    water-level record is then retained only as the driver's reported value;
    recurrence begins with the second record, just as the workbook's first row
    supplies the initial state for later rows.
    """
    if len(years)!=len(growing_season_water_levels):
        raise ValueError("years and water levels must have equal length")
    if not years:
        return []
    _validate_positive("f_yr",f_yr); _validate_positive("s_yr",s_yr)
    _validate_minimum("cmin",cmin); _validate_minimum("wmin",wmin)
    y0=int(years[0]); wl0=float(growing_season_water_levels[0])
    lower0=wl0 if initial_lower_limit is None else float(initial_lower_limit)
    upper0=wl0 if initial_upper_limit is None else float(initial_upper_limit)
    if lower0>upper0:
        raise ValueError("initial_lower_limit must be <= initial_upper_limit")
    out=[TLMMBoundaryYear(y0,wl0,0,marsh_remaining_after_flooding(0,f_yr,cmin),lower0,
                          0,marsh_remaining_after_dewatering(0,s_yr,wmin),upper0)]
    prev_lower=lower0; prev_upper=upper0; prev_dt=0; prev_xt=0
    for y,wl in zip(years[1:],growing_season_water_levels[1:]):
        dt,fl,lower=lower_limit_step(wl,prev_lower,prev_dt,f_yr=f_yr,cmin=cmin)
        xt,fu,upper=upper_limit_step(wl,prev_upper,prev_xt,s_yr=s_yr,wmin=wmin)
        out.append(TLMMBoundaryYear(int(y),float(wl),dt,fl,lower,xt,fu,upper))
        prev_lower,prev_upper,prev_dt,prev_xt=lower,upper,dt,xt
    return out
