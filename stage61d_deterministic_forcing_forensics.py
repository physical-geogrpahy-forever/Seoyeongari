#!/usr/bin/env python3
"""Stage61d — deterministic raw meteorology -> forcing -> scalar hydro audit.

The EXPECTED fingerprints below were independently reproduced bit-for-bit on
8 heterogeneous GitHub-hosted runners (Ubuntu 22.04/24.04, four replicas each)
on 2026-08-27.  This script now acts as a regression contract: any change in
cleaned meteorology, forcing, daily hydro, or April-May ecological/hydrologic
features fails the run rather than silently creating a new numerical branch.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
from pathlib import Path

import numpy as np
import pandas as pd

from eghm_deterministic_forcing import deterministic_forcing, source_missing_before_fill, MP_DPS
from stage61c_scalar_recurrence_forensics import hydro_scalar, features_scalar, SELECTED

OUT = Path('stage61d_outputs')
OUT.mkdir(exist_ok=True)

EXPECTED = {
    'clean_tmean': '8e9f4c499d61d257f551ac73a0e9b6a3ee1ecc55a3cab02dc72204ebc603bf52',
    'clean_tmin': 'c3d63da006c132870cfedabc1966b3bb7b93b5fb7d8382685ebb75998bdc5565',
    'clean_tmax': '26265a6d0769cbf34adf8cae25299dac1b6acea8bc6ef62c32063b6e38f4811a',
    'clean_pre': '4e46da169e1f3d7d525b33e3640f65eb145828c6e0062a73c97a9c34236142f0',
    'clean_wind': '493d169dc7e7a32e90deacd074f49a85c1de866c4dad654943e70ea28243bc63',
    'clean_sun': '178285509a887740957839590dfe8db7663f148f59ac6a95fa546a05c84ae3df',
    'forcing_pre': '4e46da169e1f3d7d525b33e3640f65eb145828c6e0062a73c97a9c34236142f0',
    'forcing_pes': '0ea37bab0ed2f0befca9ad7fb396540cfa548b4265136379c52b753caa5408c4',
    'forcing_eto': '7757d113b1a1d836f608c0cd920e7ecd95fe5c2633c387d1e062005ab935dafc',
    'forcing_ep': 'a2b1153cd92cf74bda7b87c80231f5e08c7aaa1440aa4e73641a8852518fee5f',
    'forcing_pp': '448e0103b04eaf0e43a928fec88a4f129e388731d02e8861c930fca5aeca6ee3',
    'V': 'dede5d3295413c303c662f07a774d832f3e6524592c4e5ffe4b34efaeff4fd94',
    'area': '7c8d7dd1c5bb738cb2fa8ff89d1b06e6ede11b866b15484518ebf7a445fc934e',
    'return_flow': '4b97f284f0ce8ee8da01559e02421ccbf04eabe0315b92aad5b246173869bb33',
    'exposed': '355e83f77f2c7955445fd1649c38b1d5fdf25e1b9df99f1a463b662d20e9a3de',
    'E7': 'd84e1ebf9ea5856376e14a8c1afa2dad1809fcf21d728ad665c9cf84ad21f447',
    'state': '193e19256ab994290d455f26b84c38c671314b42c90e10d665a95f33e26a0dc8',
    'S': '354cf1f966e9fd370e01e62ff5374821a8e49003621d002b56959c053fb2f71f',
    'H': '4e0fc0144514a0734c7fb849b1b356855b8eb54123db725b7a1a5db86ed2a169',
}


def sha(a):
    arr = np.asarray(a, dtype='<f8')
    return hashlib.sha256(arr.tobytes(order='C')).hexdigest()


def main():
    F, forcing_missing, annual, cleaned = deterministic_forcing()
    source_missing = source_missing_before_fill()
    hp = {k: SELECTED[k] for k in ['V0', 'p_shape', 'tau_surf', 'local_frac', 'tau_fast', 'k_gw_mm_d']}
    h = hydro_scalar(F, hp)
    exposed, E, state, S, H = features_scalar(h)

    fingerprints = {
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
    }
    mismatches = {k: {'expected': EXPECTED[k], 'actual': fingerprints[k]}
                  for k in EXPECTED if fingerprints.get(k) != EXPECTED[k]}

    result = {
        'status': 'PASS_CROSS_RUN_BITWISE_DETERMINISM' if not mismatches else 'FAIL_DETERMINISM_REGRESSION',
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
        'source_missing_before_fill': source_missing,
        'forcing_missing_legacy_stage30_semantics': forcing_missing,
        'annual_precip_mm': annual,
        'selected_structure_fixed_not_refit': SELECTED,
        'fingerprints': fingerprints,
        'expected_fingerprints': EXPECTED,
        'fingerprint_mismatches': mismatches,
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

    if mismatches:
        raise SystemExit(f'Stage61d bitwise determinism regression: {mismatches}')
    if max(result['physical_closure'].values()) > 1e-8:
        raise SystemExit('Stage61d physical closure failed')


if __name__ == '__main__':
    main()
