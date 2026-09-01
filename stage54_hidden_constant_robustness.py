#!/usr/bin/env python3
"""Stage54 — hidden inherited constants + independent hydroperiod diagnostics.

Purpose
-------
Stage52 perturbed the explicit Stage49 calibration axes, but the current daily
hydrology also inherits three fixed quantities from Stage35c/38:

1) effective soil-water storage depth = 0.294 * 0.55 = 0.1617 m water;
2) FAST_FRAC = 0.75;
3) TAU_SLOW = 365 d.

This stage does NOT optimize them. It performs a small one-at-a-time robustness
audit using independently motivated or pre-existing values only:

- active/root depth: 0.42 / 0.55 / 0.65 m while retaining the unresolved legacy
  AWC fraction 0.294. The 0.42 and 0.65 m endpoints correspond to boundaries in
  the RDA Jungmun-series representative pedon, where roots remain common through
  the 42-65 cm Bw horizon and become sparse below 65 cm. This does not validate
  the exact AWC fraction 0.294.
- FAST_FRAC: 0.25 / 0.50 / 0.75, the pre-existing Stage26/31 conceptual search
  values.
- TAU_SLOW: 180 / 365 / 730 / 1460 d, the pre-existing Stage26/31 conceptual
  slow-reservoir search support.

For each perturbation two questions are separated:

A) FIXED observation-operator coefficients: central Stage52 Kc/Kh are locked.
B) PROFILE REFIT: Kc/Kh are refitted to the six mapped pond-area years. This is
   a calibration diagnostic only, not a fixed-model robustness result.

Daily zero-surface-storage diagnostics are also exported. They are independent
process diagnostics and are never used as an objective or acceptance gate.
2022 meteorology remains in the continuous simulation, but no 2022 pond-area
observation exists.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import stage38_domain_corrected as h38
import stage50_four_scenario_peat_sensitivity as m
import stage51_persistent_peat_sensitivity as s51
import stage52_oat_provenance as s52

OUT = Path('stage54_outputs')
OUT.mkdir(exist_ok=True)

AWC_FRACTION_LEGACY = 0.294
CENTRAL_ROOT_ACTIVE_DEPTH_M = 0.55
CENTRAL_FAST_FRAC = 0.75
CENTRAL_TAU_SLOW_D = 365.0

OAT = {
    'root_active_depth_m': [0.42, 0.55, 0.65],
    'fast_frac': [0.25, 0.50, 0.75],
    'tau_slow_d': [180.0, 365.0, 730.0, 1460.0],
}
CENTRAL = {
    'root_active_depth_m': CENTRAL_ROOT_ACTIVE_DEPTH_M,
    'fast_frac': CENTRAL_FAST_FRAC,
    'tau_slow_d': CENTRAL_TAU_SLOW_D,
}


def set_hidden(parameter: str, value: float) -> None:
    """Set exactly one inherited Stage38 global while keeping all else central."""
    # Reset every hidden constant first, making each setting true OAT.
    h38.SOIL_DEPTH = AWC_FRACTION_LEGACY * CENTRAL_ROOT_ACTIVE_DEPTH_M
    h38.C_UPLAND = h38.SOIL_DEPTH * h38.A_UPLAND
    h38.C_WET = h38.SOIL_DEPTH * h38.A_WET
    h38.FAST_FRAC = CENTRAL_FAST_FRAC
    h38.TAU_SLOW = CENTRAL_TAU_SLOW_D

    if parameter == 'root_active_depth_m':
        h38.SOIL_DEPTH = AWC_FRACTION_LEGACY * float(value)
        h38.C_UPLAND = h38.SOIL_DEPTH * h38.A_UPLAND
        h38.C_WET = h38.SOIL_DEPTH * h38.A_WET
    elif parameter == 'fast_frac':
        h38.FAST_FRAC = float(value)
    elif parameter == 'tau_slow_d':
        h38.TAU_SLOW = float(value)
    else:
        raise KeyError(parameter)


def reset_hidden() -> None:
    set_hidden('root_active_depth_m', CENTRAL_ROOT_ACTIVE_DEPTH_M)


def longest_true_run(mask: np.ndarray) -> int:
    best = cur = 0
    for z in np.asarray(mask, bool):
        if z:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return int(best)


def hydroperiod_rows(parameter: str, value: float, h) -> list[dict]:
    dt = pd.to_datetime(h['dates'])
    v = np.asarray(h['V'], float)
    zero = v <= 1e-9
    rows = []
    for year in range(2011, 2024):
        y = dt.year.to_numpy() == year
        spring = y & np.isin(dt.month.to_numpy(), [3, 4])
        annual_zero = int(np.sum(zero & y))
        spring_zero = int(np.sum(zero & spring))
        zyear = zero[y]
        dyear = dt[y]
        zero_dates = dyear[zyear]
        rows.append({
            'parameter': parameter,
            'value': float(value),
            'year': year,
            'zero_storage_days': annual_zero,
            'mar_apr_zero_storage_days': spring_zero,
            'mar_apr_share_of_zero_days': (spring_zero / annual_zero if annual_zero else np.nan),
            'longest_zero_run_days': longest_true_run(zyear),
            'first_zero_date': (str(zero_dates[0].date()) if len(zero_dates) else ''),
            'last_zero_date': (str(zero_dates[-1].date()) if len(zero_dates) else ''),
        })
    return rows


def state_for_current_hidden():
    P = dict(m.P49)
    h, S, H, G, corr = s52.states_for(P)
    return h, S, H, G, corr


def fixed_scenarios(S, H, G, central_coeff):
    out = []
    for name, b in central_coeff.items():
        pred = s52.predict_with_coeff(name, S, H, G, b['Kc'], b['Kh'])
        rm, nr = m.metric(pred)
        out.append((name, float(b['Kc']), float(b['Kh']), pred, rm, nr))
    return out


def scenario_rows(parameter, value, mode, scenarios, corr, h):
    ordered = sorted(scenarios, key=lambda z: z[5])
    ranks = {z[0]: i + 1 for i, z in enumerate(ordered)}
    rows = []
    for name, kc, kh, pred, rm, nr in scenarios:
        rows.append({
            'mode': mode,
            'parameter': parameter,
            'value': float(value),
            'is_central_value': bool(abs(float(value) - float(CENTRAL[parameter])) < 1e-12),
            'Scenario': name,
            'RMSE_m2': float(rm),
            'nRMSE_pct': float(nr),
            'rank': int(ranks[name]),
            'K_colonizable_m2': float(kc),
            'K_hydro_m_inv': float(kh),
            'state_year_corr': float(corr),
            'mass_error_m3': float(h['mass_error']),
            'area_partition_error_m2': float(h['area_partition_error']),
            'precip_partition_error_m3': float(h['precip_partition_error']),
            **{f'pred_{int(y)}': float(pred[i]) for i, y in enumerate(m.YEARS)},
        })
    return rows


def main():
    reset_hidden()
    central_coeff, central_state = s52.central_coefficients()
    h0, S0, H0, G0, corr0 = central_state

    rows = []
    hp_rows = []

    for parameter, values in OAT.items():
        for value in values:
            set_hidden(parameter, value)
            h, S, H, G, corr = state_for_current_hidden()

            fixed = fixed_scenarios(S, H, G, central_coeff)
            prof = m.fit_scenarios(S, H, G)
            rows.extend(scenario_rows(parameter, value, 'fixed', fixed, corr, h))
            rows.extend(scenario_rows(parameter, value, 'profile_refit', prof, corr, h))
            hp_rows.extend(hydroperiod_rows(parameter, value, h))

    reset_hidden()

    df = pd.DataFrame(rows)
    hp = pd.DataFrame(hp_rows)
    df.to_csv(OUT / 'stage54_hidden_oat_all.csv', index=False)
    df[df['mode'] == 'fixed'].to_csv(OUT / 'stage54_hidden_oat_fixed.csv', index=False)
    df[df['mode'] == 'profile_refit'].to_csv(OUT / 'stage54_hidden_oat_profile_refit.csv', index=False)
    hp.to_csv(OUT / 'stage54_hydroperiod_by_year.csv', index=False)

    # One row per hidden-parameter setting for easier interpretation.
    diag_rows = []
    for parameter, values in OAT.items():
        for value in values:
            z = hp[(hp.parameter == parameter) & np.isclose(hp.value, float(value))]
            eval_z = z[z.year.between(2012, 2023)]
            fixed_i = df[(df['mode'] == 'fixed') & (df.parameter == parameter) & np.isclose(df.value, float(value)) & (df.Scenario == 'Integrated Model')].iloc[0]
            prof_i = df[(df['mode'] == 'profile_refit') & (df.parameter == parameter) & np.isclose(df.value, float(value)) & (df.Scenario == 'Integrated Model')].iloc[0]
            diag_rows.append({
                'parameter': parameter,
                'value': float(value),
                'is_central_value': bool(abs(float(value) - float(CENTRAL[parameter])) < 1e-12),
                'effective_soil_storage_mm': (1000.0 * AWC_FRACTION_LEGACY * float(value) if parameter == 'root_active_depth_m' else 1000.0 * AWC_FRACTION_LEGACY * CENTRAL_ROOT_ACTIVE_DEPTH_M),
                'fixed_integrated_nRMSE_pct': float(fixed_i.nRMSE_pct),
                'fixed_integrated_rank': int(fixed_i['rank']),
                'profile_integrated_nRMSE_pct': float(prof_i.nRMSE_pct),
                'profile_integrated_rank': int(prof_i['rank']),
                'mean_zero_storage_days_2012_2023': float(eval_z.zero_storage_days.mean()),
                'median_zero_storage_days_2012_2023': float(eval_z.zero_storage_days.median()),
                'mean_mar_apr_zero_days_2012_2023': float(eval_z.mar_apr_zero_storage_days.mean()),
                'overall_mar_apr_share_of_zero_days_2012_2023': float(eval_z.mar_apr_zero_storage_days.sum() / eval_z.zero_storage_days.sum()) if eval_z.zero_storage_days.sum() else np.nan,
                'max_zero_storage_days_any_year_2012_2023': int(eval_z.zero_storage_days.max()),
                'max_longest_zero_run_days_2012_2023': int(eval_z.longest_zero_run_days.max()),
            })
    diag = pd.DataFrame(diag_rows)
    diag.to_csv(OUT / 'stage54_setting_summary.csv', index=False)

    # Noncentral counts only, so repeated central settings on each axis do not inflate robustness counts.
    noncentral = df[~df.is_central_value]
    fixed_i = noncentral[(noncentral['mode'] == 'fixed') & (noncentral['Scenario'] == 'Integrated Model')]
    prof_i = noncentral[(noncentral['mode'] == 'profile_refit') & (noncentral['Scenario'] == 'Integrated Model')]

    central_hp = hp[(hp.parameter == 'root_active_depth_m') & np.isclose(hp.value, CENTRAL_ROOT_ACTIVE_DEPTH_M)]
    central_hp_eval = central_hp[central_hp.year.between(2012, 2023)]

    central_metrics = []
    for name, b in central_coeff.items():
        pred = s52.predict_with_coeff(name, S0, H0, G0, b['Kc'], b['Kh'])
        rm, nr = m.metric(pred)
        central_metrics.append({'Scenario': name, 'RMSE_m2': rm, 'nRMSE_pct': nr, 'Kc': b['Kc'], 'Kh': b['Kh']})
    central_metrics.sort(key=lambda r: r['nRMSE_pct'])

    summary = {
        'status': 'PASS_STAGE54_DIAGNOSTIC',
        'pond_area_observation_2022': 'ABSENT',
        'peat_rate_mm_yr': float(s51.CENTRAL_RATE),
        'purpose': 'robustness audit of inherited fixed constants; no hidden constant is selected by optimization',
        'legacy_awc_fraction': AWC_FRACTION_LEGACY,
        'legacy_awc_fraction_provenance': 'unresolved; retained only to isolate active-depth sensitivity',
        'root_depth_basis': 'RDA Jungmun representative pedon: root abundance remains common through 42-65 cm and becomes sparse below 65 cm; 0.42/0.65 m are bracketing diagnostic depths, not site root measurements',
        'oat_values': OAT,
        'central_values': CENTRAL,
        'central_metrics': central_metrics,
        'noncentral_setting_count': int(len(fixed_i)),
        'fixed_integrated_rank1_count': int((fixed_i['rank'] == 1).sum()),
        'profile_integrated_rank1_count': int((prof_i['rank'] == 1).sum()),
        'central_hydroperiod_2012_2023': {
            'mean_zero_storage_days': float(central_hp_eval.zero_storage_days.mean()),
            'median_zero_storage_days': float(central_hp_eval.zero_storage_days.median()),
            'mean_mar_apr_zero_days': float(central_hp_eval.mar_apr_zero_storage_days.mean()),
            'overall_mar_apr_share_of_zero_days': float(central_hp_eval.mar_apr_zero_storage_days.sum() / central_hp_eval.zero_storage_days.sum()),
            'max_zero_storage_days_any_year': int(central_hp_eval.zero_storage_days.max()),
            'max_longest_zero_run_days': int(central_hp_eval.longest_zero_run_days.max()),
        },
        'hydroperiod_role': 'independent process diagnostic only; not a fit/acceptance objective',
        'physical_closure_central': {
            'mass_error_m3': float(h0['mass_error']),
            'area_partition_error_m2': float(h0['area_partition_error']),
            'precip_partition_error_m3': float(h0['precip_partition_error']),
        },
    }
    (OUT / 'stage54_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
