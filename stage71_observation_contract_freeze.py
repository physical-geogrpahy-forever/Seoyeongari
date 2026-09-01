#!/usr/bin/env python3
"""Stage71 — freeze the active observation contract without changing the model.

Purpose
-------
This stage is a semantic/reproducibility gate, not a calibration stage.  It
locks the active Round-1 observation definition to manually digitized
open-water pond surface area from 0.5-m orthorectified airborne images acquired
in April or May, while preserving the official deterministic Stage63 numerical
result exactly.

The exact acquisition day for each historical image has not been recovered in
the currently archived model inputs.  Therefore no exact date is invented: the
existing April-May process-support mean remains an explicit approximation until
per-image dates are independently recovered.

The seasonal field observation of visible-pool exposure/disappearance is a
separate hydroperiod variable.  It is not defined by numerical V == 0 and no
arbitrary depth threshold is introduced here.
"""
from __future__ import annotations

from datetime import datetime
import json
import math
from pathlib import Path

import numpy as np

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_kernel import (
    A0, EVAL_YEARS, OBS_MONTHS, SELECTED_STRUCTURE,
    annual_support, build_features, hydro, sha256_f8,
)
from eghm_deterministic_scenarios import fit_four_scenarios, peat_geomorphic_loss
from eghm_reproducibility_contract import EXPECTED_FINGERPRINTS
from eghm_strict_rules import (
    OBSERVATION_VARIABLE, HYDRAULIC_STATE_VARIABLE,
    HYDROPERIOD_VALIDATION_VARIABLE,
)

OUT = Path('stage71_outputs')
OUT.mkdir(exist_ok=True)

OBS = {
    2013: 2154.430,
    2015: 2147.678,
    2017: 2051.218,
    2019: 2045.159,
    2021: 1965.256,
    2023: 1882.700,
}
CENTRAL_PEAT_MM_YR = 0.38
EXPECTED_INTEGRATED_NRMSE = 1.4113250129695185


def concat_forcing(a, b):
    keys = ('pre', 'pes', 'eto', 'ep', 'pp', 'year', 'month', 'date')
    return {k: np.concatenate([np.asarray(a[k]), np.asarray(b[k])]) for k in keys}


def main():
    years = tuple(EVAL_YEARS)
    if years != (2013, 2015, 2017, 2019, 2021, 2023):
        raise SystemExit(f'active observation years moved: {years!r}')
    if 2022 in OBS or 2022 in years:
        raise SystemExit('2022 pond-area observation must not exist in the active analysis')
    if tuple(OBS_MONTHS) != (4, 5):
        raise SystemExit(f'April-May support moved: {tuple(OBS_MONTHS)!r}')
    if OBSERVATION_VARIABLE != 'mapped_open_water_pond_surface_area':
        raise SystemExit(f'observation variable moved: {OBSERVATION_VARIABLE!r}')

    # Rebuild the frozen historical forcing and official Stage63 central case.
    Fhist, _, _, _ = deterministic_forcing()
    f = build_features(Fhist, SELECTED_STRUCTURE, years=years, months=OBS_MONTHS)
    h = f['hydro']
    S = [float(v) for v in f['S']]
    H = [float(v) for v in f['H']]
    y = [float(OBS[yr]) for yr in years]

    fingerprint_checks = {
        'V': sha256_f8(h['V']),
        'area': sha256_f8(h['area']),
        'return_flow': sha256_f8(h['return_flow']),
        'exposed': sha256_f8(f['ecology']['exposed']),
        'E7': sha256_f8(f['ecology']['exposure_window']),
        'state': sha256_f8(f['ecology']['state']),
        'S': sha256_f8(S),
        'H': sha256_f8(H),
    }
    bad = {
        k: (EXPECTED_FINGERPRINTS[k], v)
        for k, v in fingerprint_checks.items()
        if EXPECTED_FINGERPRINTS[k] != v
    }
    if bad:
        raise SystemExit(f'deterministic historical contract moved: {bad!r}')

    Gd, h0, B = peat_geomorphic_loss(
        h['dates'], h['V'], CENTRAL_PEAT_MM_YR,
        SELECTED_STRUCTURE['V0'], SELECTED_STRUCTURE['p_shape'],
    )
    G = annual_support(h['dates'], Gd, years=years, months=OBS_MONTHS)
    scenarios = fit_four_scenarios(S, H, G, y, A0)
    ordered = sorted(scenarios, key=lambda z: (z['nRMSE_pct'], z['RMSE_m2'], z['Scenario']))
    rank = {z['Scenario']: i + 1 for i, z in enumerate(ordered)}
    integrated = next(z for z in scenarios if z['Scenario'] == 'Integrated Model')
    if abs(float(integrated['nRMSE_pct']) - EXPECTED_INTEGRATED_NRMSE) > 1e-12:
        raise SystemExit(
            'official Stage63 numerical result moved: '
            f"{integrated['nRMSE_pct']} != {EXPECTED_INTEGRATED_NRMSE}"
        )

    # Forward 2024 hydraulic diagnostic: no 2024 area target and no refit.
    F24, _, annual24, _ = deterministic_forcing(
        start_date=datetime(2024, 1, 1), end_date=datetime(2024, 12, 31)
    )
    if len(F24['date']) != 366:
        raise SystemExit(f'2024 forcing incomplete: {len(F24["date"])} rows')
    Hall = hydro(concat_forcing(Fhist, F24), dict(SELECTED_STRUCTURE))
    ix24 = [i for i, d in enumerate(Hall['dates']) if int(d.year) == 2024]
    V24 = [float(Hall['V'][i]) for i in ix24]
    A24 = [float(Hall['area'][i]) for i in ix24]

    closure = {
        'mass_error_m3': float(Hall['mass_error']),
        'area_partition_error_m2': float(Hall['area_partition_error']),
        'precip_partition_error_m3': float(Hall['precip_partition_error']),
    }
    if max(closure.values()) > 1e-8:
        raise SystemExit(f'physical closure failed: {closure!r}')

    scenario_rows = []
    for z in ordered:
        scenario_rows.append({
            'rank': rank[z['Scenario']],
            'Scenario': z['Scenario'],
            'RMSE_m2': float(z['RMSE_m2']),
            'nRMSE_pct': float(z['nRMSE_pct']),
            'K_colonizable_m2': float(z['K_colonizable_m2']),
            'K_hydro_m2_per_m3': float(z['K_hydro_m2_per_m3']),
        })

    result = {
        'status': 'PASS_STAGE71_OBSERVATION_CONTRACT_FREEZE',
        'model_process_changed': False,
        'model_parameter_changed': False,
        'parameter_refit_performed': False,
        'active_observation_contract': {
            'variable': OBSERVATION_VARIABLE,
            'definition': 'manually digitized water-body polygon surface area from 0.5-m orthorectified airborne imagery',
            'years': list(years),
            'initial_reference_year': 2011,
            '2022_pond_area_observation_exists': False,
            'image_acquisition_support': 'April or May',
            'model_process_support_statistic': 'April-May mean',
            'exact_per_image_acquisition_dates_recovered': False,
            'exact_dates_invented': False,
        },
        'variable_separation': {
            'historical_area_target': OBSERVATION_VARIABLE,
            'daily_hydraulic_state': HYDRAULIC_STATE_VARIABLE,
            'seasonal_visible_pool_validation': HYDROPERIOD_VALIDATION_VARIABLE,
            'V_equals_zero_defines_visible_pool_absence': False,
            'arbitrary_visible_pool_depth_threshold_added': False,
        },
        'official_stage63_central_case': {
            'peat_rate_mm_yr': CENTRAL_PEAT_MM_YR,
            'Integrated_nRMSE_pct': float(integrated['nRMSE_pct']),
            'expected_Integrated_nRMSE_pct': EXPECTED_INTEGRATED_NRMSE,
            'numerically_unchanged': True,
            'scenario_metrics': scenario_rows,
            'h0_reference_depth_m': float(h0),
        },
        'historical_deterministic_fingerprint_pass': True,
        'historical_fingerprints': fingerprint_checks,
        '2024_forward_hydraulic_diagnostic': {
            'pond_area_target_used': False,
            'parameter_refit': False,
            'annual_precip_mm': float(annual24[2024]),
            'hydraulic_zero_days_V_le_1e-9': int(sum(v <= 1e-9 for v in V24)),
            'mean_surface_storage_m3': float(math.fsum(V24) / len(V24)),
            'mean_hydraulic_area_m2': float(math.fsum(A24) / len(A24)),
            'interpretation': 'Hydraulic V and A are process states, not a direct binary visible-pool observation operator.',
        },
        'physical_closure': closure,
        'superseded_semantics_note': (
            'Stage69 wording that called the active target mapped wetland extent is superseded by Stage70/71. '
            'The undergraduate-thesis canopy/transition-boundary interpretation is retained as historical provenance only.'
        ),
        'next_scientific_constraint': (
            'Recover exact historical image acquisition dates and/or independently constrain microtopography/water-level-to-visible-pool mapping before tightening seasonal hydroperiod validation.'
        ),
    }

    (OUT / 'stage71_summary.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
