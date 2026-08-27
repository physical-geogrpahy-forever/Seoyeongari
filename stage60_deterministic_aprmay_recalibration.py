#!/usr/bin/env python3
"""Stage60 — deterministic full April-May EGHM recalibration.

This reruns the complete Stage49/56 87,480-candidate calibration with exactly the
same process equations, parameter grids, physical/ecological gates, six mapped
pond-area targets, and April-May temporal support. The ONLY algorithmic change
is replacement of the general LAPACK/NumPy least-squares call used to estimate
Kc/Kh with the deterministic 80-digit Decimal constrained solver.

This is a numerical-reproducibility correction, not a scientific retuning.
2022 pond area remains absent.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np

import stage49_six_observation_irreversible_recruitment as s49
from stage56_aprmay_recalibration import annual_aprmay, annual_hydro_aprmay
from eghm_deterministic_fit import fit_constrained_state

OUT = Path('stage60_outputs')
OUT.mkdir(exist_ok=True)


def deterministic_fit(S, H, y):
    return fit_constrained_state(S, H, y, s49.A0)


def selected_fingerprint(selected: dict) -> str:
    keys = [
        'V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d',
        'r_est_yr','hydro_window_d','est_window_d','K_colonizable_m2',
        'K_hydro','rmse_m2','nrmse_pct',
    ] + [f'pred_{int(y)}' for y in s49.YEARS]
    payload = '\n'.join(f'{k}={float(selected[k]):.17g}' for k in keys)
    return hashlib.sha256(payload.encode('ascii')).hexdigest()


def main():
    # Only these three runtime hooks differ from Stage49:
    # output location, observation temporal support, deterministic coefficient fit.
    s49.OUT = OUT
    s49.annual = annual_aprmay
    s49.annual_hydro = annual_hydro_aprmay
    s49.fit_constrained = deterministic_fit

    s49.main()

    src = OUT / 'stage49_summary.json'
    d = json.loads(src.read_text(encoding='utf-8'))
    selected = d.get('selected') or {}
    if not selected:
        raise SystemExit('Stage60: no selected candidate')

    d['model'] = 'Stage60 deterministic metadata-aligned April-May six-observation EGHM calibration'
    d['stage60_change_only'] = 'replace legacy NumPy/LAPACK Kc/Kh fit with deterministic 80-digit Decimal constrained solver'
    d['observation_support'] = 'April-May'
    d['observation_support_basis'] = 'NGII historical airborne-image metadata; not selected by fit'
    d['evaluation_months'] = [4, 5]
    d['evaluation_window_selected_by_fit'] = False
    d['solver'] = 'eghm_deterministic_fit.fit_constrained_state; Decimal precision 80; exact input-float conversion; feasible-boundary enumeration'
    d['solver_change_is_scientific_parameter_change'] = False
    d['parameter_grids_changed_from_stage56'] = False
    d['physical_process_structure_changed_from_stage56'] = False
    d['pond_area_observation_2022'] = 'ABSENT_NOT_HOLDOUT'
    d['selected_fingerprint_sha256'] = selected_fingerprint(selected)

    # Explicit locked process vector makes cross-run comparison easy.
    d['selected_process_parameters'] = {
        k: float(selected[k]) for k in [
            'V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d',
            'r_est_yr','hydro_window_d','est_window_d'
        ]
    }
    d['selected_operator_and_fit'] = {
        'K_colonizable_m2': float(selected['K_colonizable_m2']),
        'K_hydro_m_inv': float(selected['K_hydro']),
        'RMSE_m2': float(selected['rmse_m2']),
        'nRMSE_pct': float(selected['nrmse_pct']),
        'state_year_corr': float(selected['state_year_corr']),
    }

    (OUT / 'stage60_summary.json').write_text(
        json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8'
    )

    aliases = {
        'stage49_candidate_diagnostics.csv': 'stage60_candidate_diagnostics.csv',
        'stage49_year_predictions.csv': 'stage60_year_predictions.csv',
    }
    for source, alias in aliases.items():
        p = OUT / source
        if p.exists():
            shutil.copy2(p, OUT / alias)

    print(json.dumps(d, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
