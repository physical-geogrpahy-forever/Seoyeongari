#!/usr/bin/env python3
"""Non-negotiable acceptance gates for Seoyeongari EGHM experiments.

Current observation contract (Stage70, 2026-08-27)
--------------------------------------------------
The active R1 Methods define the historical area observations as manually
digitized water-body boundaries from 0.5-m orthorectified airborne images, used
to quantify open-water pond surface area. The current target set contains six
observed years: 2013, 2015, 2017, 2019, 2021 and 2023. There is no 2022 mapped
pond-area observation in the current analysis; 2022 meteorology remains in the
continuous forcing series only.

Archived acquisition metadata place the historical images in April or May, so
the current observation-operator process support is April-May until exact dates
are recovered. The historical mapped pond area must be distinguished from the
daily conserved hydraulic state (surface storage and hydraulic wetted area) and
from the binary/qualitative seasonal observation of visible-pool presence or
disappearance. Numerical V==0 is not silently treated as visible-pool absence.

Historical undergraduate-thesis wording described the same polygon series more
broadly as wetland-area change during terrestrialization. That provenance is
retained, but the current R1 water-body digitization definition controls the
active EGHM observation contract.
"""
from __future__ import annotations

EVAL_YEARS = (2013, 2015, 2017, 2019, 2021, 2023)
OBS_MONTHS = (4, 5)
OBSERVATION_VARIABLE = 'mapped_open_water_pond_surface_area'
HYDRAULIC_STATE_VARIABLE = 'daily_surface_storage_and_hydraulic_wetted_area'
HYDROPERIOD_VALIDATION_VARIABLE = 'visible_surface_pool_presence_or_exposure'
MASS_TOL_M3 = 1e-8
AREA_PARTITION_TOL_M2 = 1e-8
PRECIP_PARTITION_TOL_M3 = 1e-8
NRMSE_MAX_PCT = 2.0
STATE_YEAR_CORR_MAX = 0.99
ZERO_TOL = 1e-12

# Retained only so historical Stage39-48 scripts remain importable. These are
# diagnostic reference thresholds, not current acceptance criteria.
LOOCV_NRMSE_MAX_PCT = 2.0
NESTED_LOOCV_NRMSE_MAX_PCT = 2.0

REQUIRED_CONTRACT = {
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


def contract_reasons(contract: dict) -> list[str]:
    r = []
    for k, v in REQUIRED_CONTRACT.items():
        if contract.get(k) != v:
            r.append(f'contract:{k}={contract.get(k)!r}, required={v!r}')
    return r


def grid_boundary_reasons(candidate: dict, grids: dict[str, list[float]]) -> list[str]:
    r = []
    for k, vals in grids.items():
        if k not in candidate or len(vals) < 3:
            continue
        x = float(candidate[k])
        lo = float(min(vals))
        hi = float(max(vals))
        if abs(x - lo) <= ZERO_TOL or abs(x - hi) <= ZERO_TOL:
            r.append(f'grid_boundary:{k}={x} on [{lo},{hi}]')
    return r


def candidate_reasons(
    candidate: dict,
    grids: dict[str, list[float]],
    contract: dict,
    *,
    require_new_process: str | None = None,
    require_short_hydro: bool = True,
    require_loocv_score: bool = False,
    require_nested_score: bool = False,
) -> list[str]:
    """Return current acceptance failures.

    Full-six-year mapped open-water pond-area nRMSE remains a gate. LOOCV and
    nested CV are opt-in diagnostics only. Seasonal visible-pool timing is a
    separate external hydroperiod diagnostic and is not reduced to V==0 or an
    arbitrary fitted depth threshold here.
    """
    r = contract_reasons(contract)
    if float(candidate.get('max_mass_error_m3', float('inf'))) > MASS_TOL_M3:
        r.append('mass_balance')
    if float(candidate.get('max_area_partition_error_m2', float('inf'))) > AREA_PARTITION_TOL_M2:
        r.append('spatial_area_partition')
    if float(candidate.get('max_precip_partition_error_m3', float('inf'))) > PRECIP_PARTITION_TOL_M3:
        r.append('precipitation_partition')
    if float(candidate.get('nrmse', candidate.get('nrmse_pct', float('inf')))) > NRMSE_MAX_PCT:
        r.append('nrmse>2pct')
    if require_loocv_score and float(candidate.get('loocv_nrmse', float('inf'))) > LOOCV_NRMSE_MAX_PCT:
        r.append('candidate_loocv_nrmse>2pct')
    if require_nested_score and float(candidate.get('nested_loocv_nrmse', float('inf'))) > NESTED_LOOCV_NRMSE_MAX_PCT:
        r.append('nested_selection_loocv_nrmse>2pct')
    if abs(float(candidate.get('state_year_corr', 1.0))) >= STATE_YEAR_CORR_MAX:
        r.append('state_year_corr>=0.99')
    kc = float(candidate.get('K_colonizable_m2', 0.0))
    a0 = float(candidate.get('A0_m2', 2241.762))
    if kc <= ZERO_TOL or kc >= a0 - ZERO_TOL:
        r.append('K_colonizable_at_bound')
    if require_short_hydro and float(candidate.get('K_hydro', 0.0)) <= ZERO_TOL:
        r.append('short_hydrology_not_identified')
    if require_new_process and float(candidate.get(require_new_process, 0.0)) <= ZERO_TOL:
        r.append(f'new_process_not_identified:{require_new_process}')
    r.extend(grid_boundary_reasons(candidate, grids))
    return r


def accepted(*args, **kwargs) -> bool:
    return not candidate_reasons(*args, **kwargs)
