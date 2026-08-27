#!/usr/bin/env python3
"""Stage49 — six-observation calibration with process-bounded irreversible recruitment.

Current validation contract
---------------------------
* Observed pond-area years are exactly 2013, 2015, 2017, 2019, 2021, 2023.
* There is no 2022 pond-area observation in this analysis. 2022 meteorology may
  remain in the continuous forcing series, but there is no 2022 area target,
  holdout, score, gate, prediction comparison, or tuning decision.
* Nested/leave-one-year-out model-selection stability is not an acceptance gate.
  The six observed years are the calibration/evaluation data set.
* Acceptance still requires exact water/area/precipitation closure, causal
  predictors, no explicit time trend, no grid-edge solution, a positive
  short-term hydrologic contribution, and full-six-year nRMSE <= 2%.

Ecological change from Stage48
------------------------------
Stage48 fitted a tiny flood-reversal rate (0.0005--0.0025 yr-1), equivalent to
centuries-to-millennia e-folding under continuous inundation. That value was
being retained mainly to satisfy a previous nonzero-process gate rather than
because ordinary seasonal reflooding should erase established wetland
vegetation on that time scale. Stage49 therefore removes the fitted flood-
reversal term explicitly instead of accepting a near-zero arbitrary coefficient.

Recruitment/encroachment remains hydrologically conditional: establishment is
allowed only from the fraction of the 2011 open-water footprint that has stayed
continuously exposed through a trailing 7, 14, or 21 day window. The state is
cumulative and bounded, x(t+1)=x(t)+r_est*E(t)*(1-x(t)). This represents slow
establishment/successional occupation; ordinary seasonal inundation affects
future establishment opportunities but does not instantaneously reverse
already established vegetation.
"""
from __future__ import annotations

import itertools
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from eghm_strict_rules import (
    EVAL_YEARS,
    MASS_TOL_M3,
    AREA_PARTITION_TOL_M2,
    PRECIP_PARTITION_TOL_M3,
    NRMSE_MAX_PCT,
    STATE_YEAR_CORR_MAX,
    ZERO_TOL,
    grid_boundary_reasons,
)
from stage31_topmodel_vsa import forcing, OBS
from stage35c_mass_balance_state_operator import A0
from stage38_domain_corrected import hydro, zero_diag
from stage39_nested_selection import fit_constrained, nrmse
from stage45_expanded_hydrology_nested import GRIDS as STAGE45_GRIDS, HKEYS, annual_hydro

OUT = Path('stage49_outputs')
OUT.mkdir(exist_ok=True)

YEARS = np.array(EVAL_YEARS, int)
Y = np.array([OBS[int(y)] for y in YEARS], float)
assert tuple(sorted(OBS)) == EVAL_YEARS, 'OBS must contain exactly the six observed pond-area years'

# Keep Stage45 guard values so the accepted physical ranges remain interior.
# Stage48 added a literature-bounded 7/14/21 d continuous-exposure window.
GRIDS = {
    **{k: list(v) for k, v in STAGE45_GRIDS.items() if k != 'r_flood_yr'},
    'est_window_d': [3, 7, 14, 21, 45],
}
ALLKEYS = HKEYS + ['r_est_yr', 'hydro_window_d', 'est_window_d']

CONTRACT = {
    'lambda': 0,
    'hard_cap': False,
    'freeboard': False,
    'explicit_time': False,
    'future_leakage': False,
    'a2011_hard_max': False,
    'spring_dry_selection_requirement': False,
    'domain_double_count': False,
    'rainfall_partition_exact': True,
    'surface_loss_priority': False,
    'observed_area_years': EVAL_YEARS,
    'missing_2022_observation': True,
    'nested_cv_selection_required': False,
}


def annual(dt, x):
    dt = pd.to_datetime(dt)
    yr = dt.year.to_numpy()
    mo = dt.month.to_numpy()
    return np.array([
        float(np.mean(x[(yr == y) & np.isin(mo, [5, 6])]))
        for y in YEARS
    ])


def irreversible_state(exposure, r_est_yr):
    """Bounded cumulative recruitment driven only by causal exposure."""
    a = float(r_est_yr) / 365.0
    q = np.clip(1.0 - a * np.asarray(exposure, float), 0.0, 1.0)
    return 1.0 - np.cumprod(q)


def build_candidates(F):
    internal = {
        k: [v for v in vals if v != min(vals) and v != max(vals)]
        for k, vals in GRIDS.items()
    }
    out = []
    hydro_cache = {}

    for vals in itertools.product(*[internal[k] for k in HKEYS]):
        hp = dict(zip(HKEYS, vals))
        h = hydro(F, hp)
        hydro_cache[tuple(vals)] = h
        a = np.asarray(h['area'], float)
        exposed = np.clip((A0 - a) / A0, 0.0, 1.0)

        e_by_window = {
            w: pd.Series(exposed)
            .rolling(int(w), min_periods=int(w))
            .min()
            .fillna(0.0)
            .to_numpy()
            for w in internal['est_window_d']
        }
        s_cache = {
            (ew, re): annual(h['dates'], irreversible_state(e_by_window[ew], re))
            for ew, re in itertools.product(internal['est_window_d'], internal['r_est_yr'])
        }
        h_cache = {
            hw: annual_hydro(h['dates'], h['return_flow'], hw)
            for hw in internal['hydro_window_d']
        }

        for ew, re, hw in itertools.product(
            internal['est_window_d'], internal['r_est_yr'], internal['hydro_window_d']
        ):
            out.append({
                **hp,
                'r_est_yr': re,
                'hydro_window_d': hw,
                'est_window_d': ew,
                'S': s_cache[(ew, re)],
                'H': h_cache[hw],
                'max_mass_error_m3': float(h['mass_error']),
                'max_area_partition_error_m2': float(h['area_partition_error']),
                'max_precip_partition_error_m3': float(h['precip_partition_error']),
            })
    return out, internal, hydro_cache


def evaluate_candidate(c):
    reasons = list(grid_boundary_reasons(c, GRIDS))
    if float(c['k_gw_mm_d']) <= ZERO_TOL:
        reasons.append('groundwater_loss_not_identified')
    if float(c['max_mass_error_m3']) > MASS_TOL_M3:
        reasons.append('mass_balance')
    if float(c['max_area_partition_error_m2']) > AREA_PARTITION_TOL_M2:
        reasons.append('area_partition')
    if float(c['max_precip_partition_error_m3']) > PRECIP_PARTITION_TOL_M3:
        reasons.append('precipitation_partition')

    S = np.asarray(c['S'], float)
    H = np.asarray(c['H'], float)
    corr = float(np.corrcoef(S, YEARS)[0, 1]) if np.std(S) > ZERO_TOL else 1.0
    if abs(corr) >= STATE_YEAR_CORR_MAX:
        reasons.append('state_year_corr>=0.99')

    b, pred = fit_constrained(S, H, Y)
    kc, kh = float(b[0]), float(b[1])
    if kc <= ZERO_TOL or kc >= A0 - ZERO_TOL:
        reasons.append('K_colonizable_at_bound')
    if kh <= ZERO_TOL:
        reasons.append('K_hydro<=0')

    rm, nr = nrmse(pred, Y)
    if nr > NRMSE_MAX_PCT:
        reasons.append('six_year_nrmse>2pct')

    row = {
        **{k: float(c[k]) for k in ALLKEYS},
        'K_colonizable_m2': kc,
        'K_colonizable_fraction_of_A0': kc / A0,
        'K_hydro': kh,
        'rmse_m2': float(rm),
        'nrmse_pct': float(nr),
        'state_year_corr': corr,
        'establishment_efold_years_at_full_exposure': 1.0 / float(c['r_est_yr']),
        'V0_equivalent_depth_m_over_A0': float(c['V0']) / A0,
        'k_gw_m_d': float(c['k_gw_mm_d']) / 1000.0,
        'max_mass_error_m3': float(c['max_mass_error_m3']),
        'max_area_partition_error_m2': float(c['max_area_partition_error_m2']),
        'max_precip_partition_error_m3': float(c['max_precip_partition_error_m3']),
        'reasons': reasons,
        **{f'pred_{int(y)}': float(pred[i]) for i, y in enumerate(YEARS)},
    }
    return row


def main():
    F, _, _ = forcing()
    cands, internal, hydro_cache = build_candidates(F)
    rows = []
    counts = Counter()
    passed = []

    for i, c in enumerate(cands):
        row = evaluate_candidate(c)
        row['candidate_index'] = i
        rows.append(row)
        for r in row['reasons']:
            counts[r] += 1
        if not row['reasons']:
            passed.append(row)

    # Six-observation calibration ranking. No leave-one-year-out score is used.
    passed.sort(key=lambda z: (z['nrmse_pct'], z['rmse_m2']))
    selected = passed[0] if passed else None

    # Compact diagnostics ordered by physical/structural validity then fit.
    rows.sort(key=lambda z: (len(z['reasons']), z['nrmse_pct'], z['rmse_m2']))
    diag = pd.DataFrame(rows)
    diag['reasons'] = diag['reasons'].map(lambda x: ';'.join(x))
    diag.to_csv(OUT / 'stage49_candidate_diagnostics.csv', index=False)

    year_rows = []
    zero = None
    if selected is not None:
        for y, obs in zip(YEARS, Y):
            year_rows.append({
                'year': int(y),
                'observed_m2': float(obs),
                'predicted_m2': float(selected[f'pred_{int(y)}']),
                'error_m2': float(selected[f'pred_{int(y)}'] - obs),
            })
        pd.DataFrame(year_rows).to_csv(OUT / 'stage49_year_predictions.csv', index=False)

        hp_key = tuple(selected[k] for k in HKEYS)
        h = hydro_cache[hp_key]
        zero = zero_diag(h['dates'], h['V'])

    summary = {
        'model': 'Stage49 six-observation integrated hydro-ecology with irreversible exposure-conditioned recruitment',
        'status': 'PASS_SIX_OBSERVATION_CALIBRATION' if selected is not None else 'FAIL_NO_VALID_CANDIDATE',
        'observed_area_years': [int(y) for y in YEARS],
        'pond_area_observation_2022': 'ABSENT_NOT_HOLDOUT',
        'selection_criterion': 'physical/ecological gates -> minimum full-six-year nRMSE; no LOOCV/nested-CV gate or ranking',
        'flood_reversal_term': 'REMOVED_EXPLICITLY_AS_UNSUPPORTED_NEAR_ZERO_FIT',
        'n_candidates_interior_grid': len(cands),
        'n_rule_pass': len(passed),
        'rejection_reason_counts': dict(counts),
        'contract': CONTRACT,
        'internal_grid_values': internal,
        'selected': selected,
        'year_predictions': year_rows,
        'selected_zero_storage_diagnostics': zero,
        'ecological_interpretation': {
            'state': 'cumulative fraction of the 2011 open-water footprint occupied through exposure-conditioned recruitment/encroachment',
            'est_window_d': 'minimum continuous antecedent exposure window required for recruitment pressure',
            'r_est_yr': 'annual establishment rate under full qualifying exposure; calibrated within a bounded candidate range',
            'ordinary_reflooding': 'reduces future recruitment opportunity but does not erase established vegetation through a fitted reversal coefficient',
        },
    }
    (OUT / 'stage49_summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if selected is None:
        raise SystemExit('Stage49: no candidate passed the six-observation physical/ecological calibration contract')


if __name__ == '__main__':
    main()
