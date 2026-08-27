#!/usr/bin/env python3
"""Stage50 — strict four-scenario comparison and peat-rate sensitivity.

Purpose
-------
Restore the manuscript's four scenario definitions on top of the Stage49 exact
water-balance core without resurrecting the old annual depth relaxation (0.035),
bottom relaxation (0.08), or empirical peat-elevation scaling (0.70).

Observed pond-area targets are exactly 2013, 2015, 2017, 2019, 2021, 2023.
There is no 2022 pond-area observation or holdout.

Common hydrology
----------------
All scenarios use the locked Stage49 hydrologic parameter set and therefore the
same exactly conserved daily water balance. The Stage49 exposure-conditioned,
irreversible recruitment state is used only when hydrosere succession is on.

Peat/elevation coupling
-----------------------
The Stage38/49 storage-area relation
    A(V) = A0 * (V/V0)^(2/(p+2))
corresponds to the depth-area power law
    A(h) = A0 * (h/h0)^(2/p)
with
    h0 = V0*(p+2)/(A0*p).

For an externally prescribed peat-surface rise B(t), the *surface expression*
of open water is evaluated at the residual surface-water depth max(h-B,0):
    A_peat(t) = A0 * [max(h-B,0)/h0]^(2/p).
The geomorphic open-water loss is G=A_hydraulic-A_peat >= 0.

G does NOT remove water from storage. It represents conversion of part of the
hydraulically wet footprint into a raised peat/vegetated surface while the
underlying saturated water remains within the conserved wetland system. Hence
no water-balance flux is invented and daily Stage49 closure is unchanged.

No fitted geomorphic multiplier is introduced. Peat rise itself is evaluated
at the pre-existing site-informed sensitivity values 0.29--7.00 mm/yr.

Scenario observation operators
------------------------------
Baseline:       A = A0              + Kh H
Hydrosere Only: A = A0 - Kc S       + Kh H
Eco-Geo Only:   A = A0        - G    + Kh H
Integrated:     A = A0 - Kc S - G    + Kh H

Kc and Kh are non-negative constrained observation-operator coefficients; Kc
is absent when hydrosere is off. G is deterministic for each prescribed peat
rate and has no fitted scale coefficient.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd

from eghm_strict_rules import EVAL_YEARS, MASS_TOL_M3, AREA_PARTITION_TOL_M2, PRECIP_PARTITION_TOL_M3
from stage31_topmodel_vsa import forcing, OBS
from stage35c_mass_balance_state_operator import A0, A_WET
from stage38_domain_corrected import hydro
from stage49_six_observation_irreversible_recruitment import irreversible_state, annual
from stage45_expanded_hydrology_nested import annual_hydro

OUT = Path('stage50_outputs')
OUT.mkdir(exist_ok=True)
YEARS = np.array(EVAL_YEARS, int)
Y = np.array([OBS[int(y)] for y in YEARS], float)

# Locked from successful Stage49 run 33028663998.
P49 = {
    'V0': 1000.0,
    'p_shape': 18.0,
    'tau_surf': 60.0,
    'local_frac': 0.45,
    'tau_fast': 30.0,
    'k_gw_mm_d': 4.0,
    'r_est_yr': 0.05,
    'hydro_window_d': 60,
    'est_window_d': 7,
}

# Existing site-informed peat-rate sensitivity set retained from the Round-1
# parameter provenance audit. 3.0 mm/yr is the manuscript reference case.
PEAT_RATES_MM_YR = [0.29, 0.38, 0.47, 1.0, 2.0, 2.89, 3.0, 5.0, 5.91, 7.0]
REFERENCE_PEAT_RATE = 3.0


def fit_nonnegative(X: np.ndarray, target: np.ndarray, upper_kc: float | None = None):
    """Tiny constrained least-squares solver for 1-2 coefficients.

    Columns are already signed as they appear in the prediction. For the two
    column hydrosere case X=[-S,H], coefficient[0]=Kc and coefficient[1]=Kh.
    Both coefficients >=0; Kc<=A0 when present.
    """
    X = np.asarray(X, float)
    target = np.asarray(target, float)
    if X.ndim == 1:
        X = X[:, None]
    ncol = X.shape[1]
    candidates = []

    b = np.linalg.lstsq(X, target, rcond=None)[0]
    ok = np.all(b >= 0)
    if upper_kc is not None and ncol >= 1:
        ok = ok and b[0] <= upper_kc
    if ok:
        candidates.append(b)

    if ncol == 1:
        d = float(X[:, 0] @ X[:, 0])
        z = max(0.0, float(X[:, 0] @ target) / d) if d > 0 else 0.0
        if upper_kc is not None:
            z = min(z, upper_kc)
        candidates += [np.array([z]), np.array([0.0])]
    elif ncol == 2:
        # Kc-only boundary
        d = float(X[:, 0] @ X[:, 0])
        k0 = max(0.0, float(X[:, 0] @ target) / d) if d > 0 else 0.0
        if upper_kc is not None:
            k0 = min(k0, upper_kc)
        candidates.append(np.array([k0, 0.0]))
        # Kh-only boundary
        d = float(X[:, 1] @ X[:, 1])
        k1 = max(0.0, float(X[:, 1] @ target) / d) if d > 0 else 0.0
        candidates.append(np.array([0.0, k1]))
        candidates.append(np.array([0.0, 0.0]))
    else:
        raise ValueError('Only 1-2 coefficients supported')

    return min(candidates, key=lambda z: float(np.sum((X @ z - target) ** 2)))


def metric(pred):
    pred = np.asarray(pred, float)
    rmse = float(np.sqrt(np.mean((pred - Y) ** 2)))
    return rmse, 100.0 * rmse / float(np.mean(Y))


def peat_geomorphic_loss(dt, V, rate_mm_yr):
    """Daily deterministic surface-open-water loss caused by peat elevation."""
    dt = pd.to_datetime(dt)
    V = np.asarray(V, float)
    p = float(P49['p_shape'])
    V0 = float(P49['V0'])
    h0 = V0 * (p + 2.0) / (A0 * p)

    ratio = np.maximum(V, 0.0) / V0
    h = h0 * np.power(ratio, p / (p + 2.0))
    A_hyd = np.where(V > 0, A0 * np.power(ratio, 2.0 / (p + 2.0)), 0.0)
    A_hyd = np.minimum(A_hyd, A_WET)

    elapsed_years = np.maximum((dt - pd.Timestamp('2011-01-01')).days.to_numpy() / 365.2425, 0.0)
    B = float(rate_mm_yr) / 1000.0 * elapsed_years
    h_resid = np.maximum(h - B, 0.0)
    A_peat = np.where(h_resid > 0, A0 * np.power(h_resid / h0, 2.0 / p), 0.0)
    A_peat = np.minimum(A_peat, A_WET)
    G_daily = np.maximum(A_hyd - A_peat, 0.0)
    return G_daily, h, B, A_hyd, A_peat, h0


def fit_scenarios(S, H, G):
    rows = []

    # Baseline: only short-term hydrologic anomaly.
    kh = fit_nonnegative(H, Y - A0)[0]
    pred = A0 + kh * H
    rm, nr = metric(pred)
    rows.append(('Baseline Model', 0.0, kh, pred, rm, nr))

    # Hydrosere: cumulative recruitment + short-term hydrology.
    X = np.c_[-S, H]
    b = fit_nonnegative(X, Y - A0, upper_kc=A0)
    pred = A0 + X @ b
    rm, nr = metric(pred)
    rows.append(('Hydrosere Only Model', float(b[0]), float(b[1]), pred, rm, nr))

    # Eco-Geo: deterministic peat surface expression + short-term hydrology.
    base = A0 - G
    kh = fit_nonnegative(H, Y - base)[0]
    pred = base + kh * H
    rm, nr = metric(pred)
    rows.append(('Eco-Geo Only Model', 0.0, kh, pred, rm, nr))

    # Integrated: deterministic peat surface expression + recruitment + hydrology.
    base = A0 - G
    X = np.c_[-S, H]
    b = fit_nonnegative(X, Y - base, upper_kc=A0)
    pred = base + X @ b
    rm, nr = metric(pred)
    rows.append(('Integrated Model', float(b[0]), float(b[1]), pred, rm, nr))
    return rows


def main():
    F, _, _ = forcing()
    hp = {k: P49[k] for k in ['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']}
    h = hydro(F, hp)

    # Exact water-balance gates remain common to all scenarios.
    assert h['mass_error'] <= MASS_TOL_M3
    assert h['area_partition_error'] <= AREA_PARTITION_TOL_M2
    assert h['precip_partition_error'] <= PRECIP_PARTITION_TOL_M3

    exposed = np.clip((A0 - np.asarray(h['area'], float)) / A0, 0.0, 1.0)
    e = (pd.Series(exposed)
         .rolling(P49['est_window_d'], min_periods=P49['est_window_d'])
         .min().fillna(0.0).to_numpy())
    st = irreversible_state(e, P49['r_est_yr'])
    S = annual(h['dates'], st)
    H = annual_hydro(h['dates'], h['return_flow'], P49['hydro_window_d'])

    all_rows = []
    geometry_rows = []
    reference_predictions = []

    for rate in PEAT_RATES_MM_YR:
        Gd, depth, B, Ah, Ap, h0 = peat_geomorphic_loss(h['dates'], h['V'], rate)
        G = annual(h['dates'], Gd)
        scenarios = fit_scenarios(S, H, G)
        rank = {name: i + 1 for i, (name, *_rest) in enumerate(sorted(scenarios, key=lambda z: z[5]))}
        for name, kc, kh, pred, rm, nr in scenarios:
            row = {
                'peat_rate_mm_yr': rate,
                'Scenario': name,
                'RMSE_m2': rm,
                'nRMSE_pct': nr,
                'rank_within_rate': rank[name],
                'K_colonizable_m2': kc,
                'K_hydro': kh,
                **{f'pred_{int(y)}': float(pred[i]) for i, y in enumerate(YEARS)},
            }
            all_rows.append(row)
            if abs(rate - REFERENCE_PEAT_RATE) < 1e-12:
                for i, y in enumerate(YEARS):
                    reference_predictions.append({
                        'Scenario': name,
                        'year': int(y),
                        'observed_m2': float(Y[i]),
                        'predicted_m2': float(pred[i]),
                        'error_m2': float(pred[i] - Y[i]),
                    })

        geometry_rows.append({
            'peat_rate_mm_yr': rate,
            'h0_reference_depth_m': h0,
            'peat_rise_2023_end_m': float(B[pd.to_datetime(h['dates']).year.to_numpy() == 2023][-1]),
            'mean_geomorphic_openwater_loss_eval_m2': float(np.mean(G)),
            **{f'G_{int(y)}_m2': float(G[i]) for i, y in enumerate(YEARS)},
        })

    df = pd.DataFrame(all_rows)
    gd = pd.DataFrame(geometry_rows)
    rp = pd.DataFrame(reference_predictions)
    df.to_csv(OUT / 'stage50_four_scenario_peat_sensitivity.csv', index=False)
    gd.to_csv(OUT / 'stage50_geomorphic_translation.csv', index=False)
    rp.to_csv(OUT / 'stage50_reference_3mm_predictions.csv', index=False)

    ref = df[np.isclose(df['peat_rate_mm_yr'], REFERENCE_PEAT_RATE)].sort_values('nRMSE_pct')
    integ = df[df['Scenario'] == 'Integrated Model'].sort_values('peat_rate_mm_yr')
    hydro = df[df['Scenario'] == 'Hydrosere Only Model'].sort_values('peat_rate_mm_yr')
    ecogeo = df[df['Scenario'] == 'Eco-Geo Only Model'].sort_values('peat_rate_mm_yr')
    baseline = df[df['Scenario'] == 'Baseline Model'].sort_values('peat_rate_mm_yr')

    integrated_rank1_all = bool((integ['rank_within_rate'] == 1).all())
    summary = {
        'status': 'PASS_STAGE50',
        'observed_area_years': [int(y) for y in YEARS],
        'pond_area_observation_2022': 'ABSENT',
        'water_balance': {
            'max_mass_error_m3': float(h['mass_error']),
            'max_area_partition_error_m2': float(h['area_partition_error']),
            'max_precip_partition_error_m3': float(h['precip_partition_error']),
        },
        'stage49_locked_parameters': P49,
        'hypsometric_translation': {
            'h0_reference_depth_m': float(gd['h0_reference_depth_m'].iloc[0]),
            'formula': 'h0=V0*(p+2)/(A0*p); A_peat=A0*(max(h-B,0)/h0)^(2/p); G=A_hydraulic-A_peat',
            'fitted_peat_scaling': False,
            'old_bottom_relax_0p08_used': False,
            'old_peat_scaling_0p70_used': False,
        },
        'peat_rates_mm_yr': PEAT_RATES_MM_YR,
        'reference_3mm_metrics': ref[['Scenario','RMSE_m2','nRMSE_pct','rank_within_rate','K_colonizable_m2','K_hydro']].to_dict('records'),
        'integrated_rank1_for_all_tested_peat_rates': integrated_rank1_all,
        'integrated_nrmse_range_pct': [float(integ['nRMSE_pct'].min()), float(integ['nRMSE_pct'].max())],
        'hydrosere_nrmse_pct': float(hydro['nRMSE_pct'].iloc[0]),
        'ecogeo_nrmse_range_pct': [float(ecogeo['nRMSE_pct'].min()), float(ecogeo['nRMSE_pct'].max())],
        'baseline_nrmse_pct': float(baseline['nRMSE_pct'].iloc[0]),
        'best_integrated_peat_rate_mm_yr': float(integ.loc[integ['nRMSE_pct'].idxmin(), 'peat_rate_mm_yr']),
        'best_integrated_nrmse_pct': float(integ['nRMSE_pct'].min()),
        'interpretation': 'Scenario-neutral ranking at each externally prescribed peat rate; no penalty or objective term favors Integrated.',
    }
    (OUT / 'stage50_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
