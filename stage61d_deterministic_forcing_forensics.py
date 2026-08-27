#!/usr/bin/env python3
"""Stage61d — deterministic raw meteorology -> forcing -> scalar hydro audit."""
from __future__ import annotations

import hashlib
import json
import os
import platform
from pathlib import Path

import numpy as np
import pandas as pd

from eghm_deterministic_forcing import deterministic_forcing, MP_DPS
from stage61c_scalar_recurrence_forensics import hydro_scalar, features_scalar, SELECTED

OUT = Path('stage61d_outputs')
OUT.mkdir(exist_ok=True)


def sha(a):
    arr = np.asarray(a, dtype='<f8')
    return hashlib.sha256(arr.tobytes(order='C')).hexdigest()


def main():
    F, missing, annual, cleaned = deterministic_forcing()
    hp = {k: SELECTED[k] for k in ['V0', 'p_shape', 'tau_surf', 'local_frac', 'tau_fast', 'k_gw_mm_d']}
    h = hydro_scalar(F, hp)
    exposed, E, state, S, H = features_scalar(h)

    result = {
        'status': 'PASS_STAGE61D_DETERMINISTIC_FORCING_FORENSICS',
        'runner': {
            'platform': platform.platform(),
            'machine': platform.machine(),
            'replica': os.environ.get('REPLICA', ''),
            'python': platform.python_version(),
            'numpy': np.__version__,
            'pandas': pd.__version__,
        },
        'mpmath_decimal_digits': MP_DPS,
        'scientific_forcing_equations_changed': False,
        'raw_missing': missing,
        'annual_precip_mm': annual,
        'selected_structure_fixed_not_refit': SELECTED,
        'fingerprints': {
            'clean_tmean': sha(cleaned['tmean']),
            'clean_tmin': sha(cleaned['tmin']),
            'clean_tmax': sha(cleaned['tmax']),
            'clean_pre': sha(cleaned['pre']),
            'clean_wind': sha(cleaned['wind']),
            'clean_sun': sha(cleaned['sun']),
            'forcing_pre': sha(F['pre']),
            'forcing_pes': sha(F['pes']),
            'forcing_eto': sha(F['eto']),
            'forcing_ep': sha(F['ep']),
            'forcing_pp': sha(F['pp']),
            'V': sha(h['V']),
            'area': sha(h['area']),
            'return_flow': sha(h['return_flow']),
            'exposed': sha(exposed),
            'E7': sha(E),
            'state': sha(state),
            'S': sha(S),
            'H': sha(H),
        },
        'S': [float(x) for x in S],
        'H': [float(x) for x in H],
        'physical_closure': {
            'mass_error_m3': float(h['mass_error']),
            'area_partition_error_m2': float(h['area_partition_error']),
            'precip_partition_error_m3': float(h['precip_partition_error']),
        },
    }
    (OUT / 'stage61d_summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if max(result['physical_closure'].values()) > 1e-8:
        raise SystemExit('Stage61d physical closure failed')


if __name__ == '__main__':
    main()
