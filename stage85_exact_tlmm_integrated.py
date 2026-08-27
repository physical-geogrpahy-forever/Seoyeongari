#!/usr/bin/env python3
"""Stage85 — exact TLMM MLL/MUL recursion coupled to the accepted EGHM daily balance.

Purpose
-------
Unify the exact Keddy & Campbell supplementary-workbook TLMM boundary recurrence
with the already accepted EGHM daily hydrology, vegetation-specific ET feedback,
peat surface-expression coupling, and the six-year mapped-open-water evaluation.

No pond-area observation is used to fit f, s, cmin, wmin, ET coefficients, peat
rate, or hydrologic parameters.

Canonical ecology
-----------------
TLMM state is represented only by Marsh Lower Limit (MLL) and Marsh Upper Limit
(MUL).  No additive exposure score and no independent elevation-band succession
state is used.  Daily class areas are geometric intersections between the
current hydraulic waterline and the annual TLMM zones.

Site coupling
-------------
The present canonical ecological area conversion remains the mapped 2011 pond
footprint A0, because independent topography for extending TLMM boundaries into
the full 5939.5 m2 vegetation/transition footprint has not yet been accepted.
This is an explicit EGHM spatial-domain limitation, not TLMM biology.
"""
from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_geometry import (
    area_h_deterministic,
    area_v_deterministic,
    depth_v_deterministic,
    reference_depth,
)
from tlmm_core import (
    C_MIN_DEFAULT,
    W_MIN_DEFAULT,
    F_TEMPERATE_YR,
    S_TEMPERATE_YR,
    S_GREAT_LAKES_EXAMPLE_YR,
    lower_limit_step,
    upper_limit_step,
)

# Accepted EGHM constants.
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

V0 = 1000.0
P_SHAPE = 18.0
TAU_SURF = 60.0
LOCAL_FRAC = 0.45
TAU_FAST = 30.0
K_GW_MM_D = 4.0

# Historical vegetation ET coefficients retained from the accepted implementation.
K_BG = 0.95
K_BARE = 0.30
K_MARSH = 0.90
K_WOODY = 0.95

# TLMM published parameters.  s=15 is sensitivity only.
F_YR = F_TEMPERATE_YR
S_YR = S_TEMPERATE_YR
CMIN = C_MIN_DEFAULT
WMIN = W_MIN_DEFAULT

# Local peat surface-rise rate retained from the accepted EGHM implementation.
PEAT_RATE_MM_YR = 0.38

EVAL_YEARS = (2013, 2015, 2017, 2019, 2021, 2023)
OBS_MONTHS = (4, 5)
OBS = {
    2013: 2154.430,
    2015: 2147.678,
    2017: 2051.218,
    2019: 2045.159,
    2021: 1965.256,
    2023: 1882.700,
}

H0 = reference_depth(V0, P_SHAPE, A0=A0)
OUT = Path("stage85_outputs")


def area_v(v: float) -> float:
    return area_v_deterministic(v, V0, P_SHAPE, A0=A0, A_WET=A_WET)


def depth_v(v: float) -> float:
    return depth_v_deterministic(v, V0, P_SHAPE, A0=A0)


def area_original(h: float) -> float:
    """Area inside the canonical 2011 ecological domain only."""
    z = min(max(float(h), 0.0), H0)
    return area_h_deterministic(z, H0, P_SHAPE, A0=A0, A_WET=A0)


def depth_from_original_area(a: float) -> float:
    """Invert A(h)=A0*(h/H0)^(1/9) for p=18 inside A0."""
    aa = min(max(float(a), 0.0), A0)
    if aa <= 0.0:
        return 0.0
    x = aa / A0
    return H0 * (x ** 9)


@dataclass
class BoundaryState:
    lower: float = H0
    upper: float = H0
    dt_flood: int = 0
    xt_dry: int = 0

    def validate(self) -> None:
        if self.lower > self.upper + 1e-10:
            raise RuntimeError(f"TLMM MLL>MUL: {self.lower} > {self.upper}")

    def update(self, september_level: float, *, f_yr: float, s_yr: float) -> None:
        dt, fr, lower = lower_limit_step(
            september_level, self.lower, self.dt_flood, f_yr=f_yr, cmin=CMIN
        )
        xt, wr, upper = upper_limit_step(
            september_level, self.upper, self.xt_dry, s_yr=s_yr, wmin=WMIN
        )
        self.lower = float(lower)
        self.upper = float(upper)
        self.dt_flood = int(dt)
        self.xt_dry = int(xt)
        self.validate()

    def zone_areas(self) -> Dict[str, float]:
        a_lower = area_original(self.lower)
        a_upper = area_original(self.upper)
        aquatic = a_lower
        marsh = max(a_upper - a_lower, 0.0)
        woody = max(A0 - a_upper, 0.0)
        return {
            "aquatic_m2": aquatic,
            "marsh_m2": marsh,
            "woody_m2": woody,
            "established_m2": marsh + woody,
            "MLL_m": self.lower,
            "MUL_m": self.upper,
        }

    def exposed_classes(self, hydraulic_level: float) -> Dict[str, float]:
        """Intersect TLMM zones with the daily exposed part of A0."""
        a_wl = area_original(hydraulic_level)
        a_lower = area_original(self.lower)
        a_upper = area_original(self.upper)
        bare = max(a_lower - a_wl, 0.0)
        marsh = max(a_upper - max(a_wl, a_lower), 0.0)
        woody = max(A0 - max(a_wl, a_upper), 0.0)
        exposed = max(A0 - a_wl, 0.0)
        err = abs((bare + marsh + woody) - exposed)
        if err > 1e-8:
            raise RuntimeError(f"exposed partition error {err}")
        return {
            "bare_m2": bare,
            "marsh_m2": marsh,
            "woody_m2": woody,
            "exposed_m2": exposed,
        }

    def flooded_classes(self, hydraulic_level: float) -> Dict[str, float]:
        a_wl = area_original(hydraulic_level)
        a_lower = area_original(self.lower)
        a_upper = area_original(self.upper)
        nonveg = min(a_wl, a_lower)
        marsh = max(min(a_wl, a_upper) - a_lower, 0.0)
        woody = max(a_wl - a_upper, 0.0)
        err = abs((nonveg + marsh + woody) - a_wl)
        if err > 1e-8:
            raise RuntimeError(f"flooded partition error {err}")
        return {"nonveg_m2": nonveg, "marsh_m2": marsh, "woody_m2": woody}

    def mapped_open_water(self, effective_level: float) -> float:
        # Flooded non-vegetated zone below MLL; inundated marsh/woody is excluded.
        return min(area_original(effective_level), area_original(self.lower))


def forcing_frame() -> pd.DataFrame:
    F, missing, annual, cleaned = deterministic_forcing()
    df = pd.DataFrame({
        "DATE": pd.to_datetime(F["date"]),
        "PRE": np.asarray(F["pre"], dtype=float),
        "ETo": np.asarray(F["eto"], dtype=float),
        "E_P": np.asarray(F["ep"], dtype=float),
    })
    if df.DATE.min() != pd.Timestamp("2011-01-01") or df.DATE.max() != pd.Timestamp("2023-12-31"):
        raise RuntimeError("forcing period contract changed")
    if df[["PRE", "ETo", "E_P"]].isna().any().any():
        raise RuntimeError("NaN in deterministic forcing")
    return df


def simulate(df: pd.DataFrame, succession: bool, peat: bool, *, s_yr: float = S_YR,
             f_yr: float = F_YR) -> Tuple[pd.DataFrame, BoundaryState, float]:
    state = BoundaryState()
    su = 0.5 * C_UPLAND
    sw = 0.5 * C_WET
    fast = 0.0
    slow = 0.0
    surf = V0
    prev = su + sw + fast + slow + surf
    maxerr = 0.0
    rows: List[Dict[str, float]] = []
    current_year = None
    september_levels: Dict[int, List[float]] = {}

    for r in df.itertuples(index=False):
        dt = pd.Timestamp(r.DATE)
        year = int(dt.year)

        if current_year is None:
            current_year = year
        elif year != current_year:
            # Causal coupling: the completed year's September state becomes effective
            # on 1 January of the next year.  The 2011 mapped boundary is the initial
            # state before the first September driver; no future-year information leaks.
            if succession and current_year in september_levels:
                sep = math.fsum(september_levels[current_year]) / len(september_levels[current_year])
                state.update(sep, f_yr=f_yr, s_yr=s_yr)
            current_year = year

        pi = float(r.PRE)
        etoi = float(r.ETo)
        epi = float(r.E_P)

        ap = area_v(surf)
        h = depth_v(surf)
        ah0 = min(ap, A0)

        elapsed = max((dt - pd.Timestamp("2011-01-01")).days / 365.2425, 0.0)
        peat_rise = PEAT_RATE_MM_YR / 1000.0 * elapsed if peat else 0.0
        apeat = area_original(max(h - peat_rise, 0.0)) if peat else ah0
        gross_geomorphic_effect = max(ah0 - apeat, 0.0)

        if peat and succession:
            established = state.zone_areas()["established_m2"]
            peat_forming_fraction = max(1.0 - established / A0, 0.0)
        else:
            peat_forming_fraction = 1.0

        geomorphic_effect = gross_geomorphic_effect * peat_forming_fraction if peat else 0.0
        effective_area = max(ah0 - geomorphic_effect, 0.0)
        effective_h = depth_from_original_area(effective_area)

        aw = max(A_WET - ap, 0.0)
        pup = pi * A_UPLAND / 1000.0
        pwet = pi * aw / 1000.0
        popen = pi * ap / 1000.0

        su += pup
        e1 = min(su, ET_UPLAND * etoi * A_UPLAND / 1000.0)
        su -= e1
        dex = max(su - C_UPLAND, 0.0)
        su -= dex

        sw += pwet
        hdom = min(h, H0) if ap < A0 else H0
        if succession:
            ex = state.exposed_classes(hdom)
        else:
            exp0 = max(A0 - ah0, 0.0)
            ex = {"bare_m2": exp0, "marsh_m2": 0.0, "woody_m2": 0.0, "exposed_m2": exp0}
        bg = max(aw - ex["exposed_m2"], 0.0)
        e2d = etoi * (
            K_BG * bg + K_BARE * ex["bare_m2"] + K_MARSH * ex["marsh_m2"] + K_WOODY * ex["woody_m2"]
        ) / 1000.0
        e2 = min(sw, e2d)
        sw -= e2
        dw = max(sw - C_WET, 0.0)
        sw -= dw

        local = dex * LOCAL_FRAC
        deep = dex - local
        fast += local * FAST_FRAC
        slow += local * (1.0 - FAST_FRAC)
        qf = min(fast, fast / TAU_FAST)
        qs = min(slow, slow / TAU_SLOW_D)
        fast -= qf
        slow -= qs
        qr = qf + qs

        surf += popen + dw + qr
        aloss = area_v(surf)
        eo_p = epi * aloss / 1000.0
        qo_p = surf / TAU_SURF
        qg_p = K_GW_MM_D * aloss / 1000.0
        lp = eo_p + qo_p + qg_p
        fac = min(1.0, surf / lp) if lp > 0.0 else 1.0
        eo = eo_p * fac
        qo = qo_p * fac
        qg = qg_p * fac
        surf -= eo + qo + qg
        if surf < 0.0 and surf > -1e-12:
            surf = 0.0

        total = su + sw + fast + slow + surf
        inputs = pup + pwet + popen
        outputs = e1 + e2 + eo + deep + qo + qg
        err = prev + inputs - outputs - total
        maxerr = max(maxerr, abs(err))
        prev = total

        if succession:
            mapped = state.mapped_open_water(effective_h)
            flooded = state.flooded_classes(hdom)
            zones = state.zone_areas()
        else:
            mapped = effective_area
            flooded = {"nonveg_m2": min(ah0, A0), "marsh_m2": 0.0, "woody_m2": 0.0}
            zones = {"aquatic_m2": A0, "marsh_m2": 0.0, "woody_m2": 0.0,
                     "established_m2": 0.0, "MLL_m": float("nan"), "MUL_m": float("nan")}

        if dt.month == 9:
            september_levels.setdefault(year, []).append(effective_h)

        rows.append({
            "DATE": dt,
            "YEAR": year,
            "V_m3": surf,
            "hydraulic_area_m2": area_v(surf),
            "hydraulic_h_m": depth_v(surf),
            "effective_h_m": effective_h,
            "geomorphic_effect_m2": geomorphic_effect,
            "mapped_open_water_m2": mapped,
            "bare_ET_area_m2": ex["bare_m2"],
            "marsh_ET_area_m2": ex["marsh_m2"],
            "woody_ET_area_m2": ex["woody_m2"],
            "background_ET_area_m2": bg,
            "wetland_ET_m3": e2,
            "TLMM_MLL_m": zones["MLL_m"],
            "TLMM_MUL_m": zones["MUL_m"],
            "TLMM_aquatic_zone_m2": zones["aquatic_m2"],
            "TLMM_marsh_zone_m2": zones["marsh_m2"],
            "TLMM_woody_zone_m2": zones["woody_m2"],
            "TLMM_established_m2": zones["established_m2"],
            "peat_forming_fraction": peat_forming_fraction,
            "flooded_nonveg_diag_m2": flooded["nonveg_m2"],
            "flooded_marsh_diag_m2": flooded["marsh_m2"],
            "flooded_woody_diag_m2": flooded["woody_m2"],
        })

    # Final 2023 September driver for end-state diagnostics only; it cannot affect
    # any 2023 observation or daily flux.
    if succession and current_year in september_levels:
        sep = math.fsum(september_levels[current_year]) / len(september_levels[current_year])
        state.update(sep, f_yr=f_yr, s_yr=s_yr)

    return pd.DataFrame(rows), state, maxerr


def evaluate(out: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
    rr = []
    for y in EVAL_YEARS:
        sel = out[(out.YEAR == y) & (out.DATE.dt.month.isin(OBS_MONTHS))]
        pred = float(sel.mapped_open_water_m2.mean())
        rr.append((y, pred, OBS[y], pred - OBS[y]))
    tab = pd.DataFrame(rr, columns=["Year", "Pred_m2", "Obs_m2", "Error_m2"])
    rmse = float(np.sqrt(np.mean(np.square(tab.Error_m2.to_numpy(dtype=float)))))
    nrmse = 100.0 * rmse / float(tab.Obs_m2.mean())
    return tab, {"RMSE_m2": rmse, "nRMSE_pct": nrmse}


def annual_diagnostics(name: str, out: pd.DataFrame) -> List[Dict[str, float]]:
    rows = []
    for y, g in out.groupby("YEAR"):
        sep = g[g.DATE.dt.month == 9]
        dec = g.iloc[-1]
        am = g[g.DATE.dt.month.isin(OBS_MONTHS)]
        rows.append({
            "Scenario": name,
            "Year": int(y),
            "AprilMay_mapped_open_water_m2": float(am.mapped_open_water_m2.mean()),
            "September_mean_effective_h_m": float(sep.effective_h_m.mean()),
            "December31_MLL_m": float(dec.TLMM_MLL_m),
            "December31_MUL_m": float(dec.TLMM_MUL_m),
            "December31_marsh_m2": float(dec.TLMM_marsh_zone_m2),
            "December31_woody_m2": float(dec.TLMM_woody_zone_m2),
            "December31_established_m2": float(dec.TLMM_established_m2),
            "annual_mean_wetland_ET_m3_d": float(g.wetland_ET_m3.mean()),
            "annual_max_geomorphic_effect_m2": float(g.geomorphic_effect_m2.max()),
        })
    return rows


def run_all() -> Dict[str, object]:
    OUT.mkdir(exist_ok=True)
    df = forcing_frame()
    scenarios = {
        "Baseline Model": (False, False),
        "Hydrosere Only Model": (True, False),
        "Eco-Geo Only Model": (False, True),
        "Integrated Model": (True, True),
    }
    summary = []
    eval_all = []
    annual_all: List[Dict[str, float]] = []

    for name, (suc, peat) in scenarios.items():
        out, state, me = simulate(df, suc, peat, s_yr=30.0, f_yr=4.0)
        tab, met = evaluate(out)
        tab.insert(0, "Scenario", name)
        eval_all.append(tab)
        annual_all.extend(annual_diagnostics(name, out))
        final = state.zone_areas() if suc else {
            "aquatic_m2": A0, "marsh_m2": 0.0, "woody_m2": 0.0,
            "established_m2": 0.0, "MLL_m": float("nan"), "MUL_m": float("nan")
        }
        summary.append({
            "Scenario": name,
            "s_yr": 30.0,
            "f_yr": 4.0,
            **met,
            "max_mass_error_m3": float(me),
            "final_MLL_m": final["MLL_m"],
            "final_MUL_m": final["MUL_m"],
            "final_marsh_m2": final["marsh_m2"],
            "final_woody_m2": final["woody_m2"],
            "final_established_m2": final["established_m2"],
            "mean_wetland_ET_m3_d": float(out.wetland_ET_m3.mean()),
            "max_geomorphic_effect_m2": float(out.geomorphic_effect_m2.max()),
        })
        stem = name.lower().replace(" ", "_").replace("-", "_")
        out.to_csv(OUT / f"{stem}_daily.csv", index=False)
        tab.to_csv(OUT / f"{stem}_evaluation.csv", index=False)

    summary_df = pd.DataFrame(summary).sort_values("nRMSE_pct")
    eval_df = pd.concat(eval_all, ignore_index=True)
    annual_df = pd.DataFrame(annual_all)
    summary_df.to_csv(OUT / "stage85_four_scenario_summary_s30.csv", index=False)
    eval_df.to_csv(OUT / "stage85_all_evaluation_years.csv", index=False)
    annual_df.to_csv(OUT / "stage85_annual_state_diagnostics.csv", index=False)

    sens = []
    for name, (suc, peat) in {
        "Hydrosere Only Model": (True, False),
        "Integrated Model": (True, True),
    }.items():
        for ss in (15.0, 30.0):
            out, state, me = simulate(df, suc, peat, s_yr=ss, f_yr=4.0)
            tab, met = evaluate(out)
            z = state.zone_areas()
            sens.append({
                "Scenario": name,
                "s_yr": ss,
                **met,
                "max_mass_error_m3": float(me),
                "final_MLL_m": z["MLL_m"],
                "final_MUL_m": z["MUL_m"],
                "final_marsh_m2": z["marsh_m2"],
                "final_woody_m2": z["woody_m2"],
            })
    pd.DataFrame(sens).to_csv(OUT / "stage85_s15_s30_published_sensitivity.csv", index=False)

    audit = {
        "status": "PASS_STAGE85_EXACT_TLMM_INTEGRATED_RUN",
        "ecology_core": "official TLMM MLL/MUL step recurrences from tlmm_core.py",
        "independent_elevation_band_state": False,
        "additive_exposure_score": False,
        "pond_area_parameter_fitting": False,
        "central_parameters": {"f_yr": 4.0, "s_yr": 30.0, "cmin": CMIN, "wmin": WMIN},
        "sensitivity": {"s_yr": 15.0, "role": "published Great Lakes worked-example sensitivity only"},
        "observation_years": list(EVAL_YEARS),
        "observation_months": list(OBS_MONTHS),
        "observation_2022_used": False,
        "ecological_spatial_domain_m2": A0,
        "spatial_domain_note": "A0 retained until independent topography outside the mapped 2011 pond is accepted",
        "forcing": "eghm_deterministic_forcing.py from the two repository-tracked raw AWS/ASOS CSVs",
        "max_mass_error_m3": float(summary_df.max_mass_error_m3.max()),
    }
    (OUT / "stage85_run_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(summary_df.to_string(index=False))
    print(json.dumps(audit, indent=2))
    return {"summary": summary_df, "evaluation": eval_df, "annual": annual_df, "audit": audit}


if __name__ == "__main__":
    run_all()
