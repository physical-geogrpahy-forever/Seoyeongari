#!/usr/bin/env python3
"""Stage56 — rerun the unchanged Stage49 calibration with April-May support.

Scientific change
-----------------
Only the temporal support of the observation features changes:
    Stage49 legacy/current: May-June mean
    Stage56: April-May mean

Reason: archived NGII image metadata states that every historical airborne image
used for pond delineation was acquired in April or May. Exact year-specific
flight dates are not yet recovered. April-May is therefore adopted provisionally
from external observation metadata, NOT because Stage55 found a lower RMSE.

Everything else remains Stage49:
- same six observed pond-area years (2013,15,17,19,21,23)
- 2011 initial/reference only
- no 2022 pond-area observation
- same parameter grids and interior/closure/ecological gates
- same exact daily mass-conserved hydrology
- same irreversible exposure-conditioned persistent occupation formulation
- same selection rule: valid candidates -> minimum full-six-year nRMSE
- no scenario-rank gate and no LOOCV/nested-CV gate.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

import stage49_six_observation_irreversible_recruitment as s49

OUT = Path('stage56_outputs')
OUT.mkdir(exist_ok=True)
MONTHS = [4, 5]


def annual_aprmay(dt, x):
    dt = pd.to_datetime(dt)
    yr = dt.year.to_numpy()
    mo = dt.month.to_numpy()
    x = np.asarray(x, float)
    return np.array([
        float(np.mean(x[(yr == y) & np.isin(mo, MONTHS)]))
        for y in s49.YEARS
    ])


def annual_hydro_aprmay(dt, q, w):
    dt = pd.to_datetime(dt)
    yr = dt.year.to_numpy()
    mo = dt.month.to_numpy()
    rr = pd.Series(np.asarray(q, float), index=dt).rolling(int(w), min_periods=1).sum().to_numpy()
    ref = float(np.mean(rr[(yr == 2011) & np.isin(mo, MONTHS)]))
    return np.array([
        float(np.mean(rr[(yr == y) & np.isin(mo, MONTHS)]) - ref)
        for y in s49.YEARS
    ])


def main():
    # Patch only temporal aggregation functions and output directory.
    s49.OUT = OUT
    s49.annual = annual_aprmay
    s49.annual_hydro = annual_hydro_aprmay

    s49.main()

    src = OUT / 'stage49_summary.json'
    d = json.loads(src.read_text(encoding='utf-8'))
    d['model'] = 'Stage56 metadata-aligned April-May six-observation integrated hydro-ecology calibration'
    d['stage56_change_only'] = 'observation-feature aggregation changed from May-June to April-May based on NGII image acquisition metadata'
    d['evaluation_months'] = MONTHS
    d['evaluation_window_label'] = 'April-May'
    d['evaluation_window_selected_by_fit'] = False
    d['evaluation_window_basis'] = 'all historical NGII orthorectified airborne images were documented as acquired in April or May; exact dates unavailable'
    d['parameter_grids_changed_from_stage49'] = False
    d['physical_process_structure_changed_from_stage49'] = False
    d['pond_area_observation_2022'] = 'ABSENT_NOT_HOLDOUT'
    (OUT / 'stage56_summary.json').write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')

    # Preserve original Stage49-named files for exact regression trace and add
    # Stage56 aliases for easier downstream discovery.
    aliases = {
        'stage49_candidate_diagnostics.csv': 'stage56_candidate_diagnostics.csv',
        'stage49_year_predictions.csv': 'stage56_year_predictions.csv',
    }
    for a, b in aliases.items():
        p = OUT / a
        if p.exists():
            shutil.copy2(p, OUT / b)

    print(json.dumps(d, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
