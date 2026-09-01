#!/usr/bin/env python3
"""Stage62 — official deterministic April-May central hydro-ecology fit.

This is the first central calibration result produced entirely through the
frozen deterministic EGHM path:
  raw meteorology -> deterministic forcing -> deterministic daily water balance
  -> continuous-exposure ecology -> April-May S/H -> 80-digit constrained fit.

2022 is meteorological forcing only and is not an area target.
"""
from __future__ import annotations

from decimal import Decimal, localcontext
import json
from pathlib import Path
from typing import Iterable, Sequence

from eghm_deterministic_forcing import deterministic_forcing, source_missing_before_fill
from eghm_deterministic_fit import D, fit_constrained_state_fixed
from eghm_deterministic_kernel import (
    A0, EVAL_YEARS, OBS_MONTHS, SELECTED_STRUCTURE,
    build_features, sha256_f8, zero_storage_diagnostics,
)
from eghm_reproducibility_contract import EXPECTED_FINGERPRINTS

OUT = Path('stage62_outputs')
OUT.mkdir(exist_ok=True)

OBS = {
    2013: 2154.430,
    2015: 2147.678,
    2017: 2051.218,
    2019: 2045.159,
    2021: 1965.256,
    2023: 1882.700,
}


def metrics_decimal(pred: Sequence[float], obs: Sequence[float]):
    with localcontext() as ctx:
        ctx.prec = 80
        pd = [D(v) for v in pred]
        od = [D(v) for v in obs]
        n = Decimal(len(pd))
        sse = sum(((pd[i] - od[i]) ** 2 for i in range(len(pd))), Decimal(0))
        sae = sum((abs(pd[i] - od[i]) for i in range(len(pd))), Decimal(0))
        rmse = (sse / n).sqrt()
        mean_obs = sum(od, Decimal(0)) / n
        nrmse = Decimal(100) * rmse / mean_obs
        mae = sae / n
        return {
            'rmse_m2': float(rmse),
            'nrmse_pct': float(nrmse),
            'mae_m2': float(mae),
            'rmse_decimal': str(rmse),
            'nrmse_decimal': str(nrmse),
            'mae_decimal': str(mae),
        }


def pearson_decimal(x: Sequence[float], y: Sequence[float]) -> float:
    with localcontext() as ctx:
        ctx.prec = 80
        xd = [D(v) for v in x]
        yd = [D(v) for v in y]
        n = Decimal(len(xd))
        mx = sum(xd, Decimal(0)) / n
        my = sum(yd, Decimal(0)) / n
        sx = sum(((v - mx) ** 2 for v in xd), Decimal(0))
        sy = sum(((v - my) ** 2 for v in yd), Decimal(0))
        if sx == 0 or sy == 0:
            return 1.0
        cov = sum(((xd[i] - mx) * (yd[i] - my) for i in range(len(xd))), Decimal(0))
        return float(cov / (sx * sy).sqrt())


def main():
    years = tuple(EVAL_YEARS)
    assert years == (2013, 2015, 2017, 2019, 2021, 2023)
    assert 2022 not in years and 2022 not in OBS
    assert tuple(sorted(OBS)) == years
    assert tuple(OBS_MONTHS) == (4, 5)

    F, forcing_missing, annual_precip, cleaned = deterministic_forcing()
    run = build_features(F, SELECTED_STRUCTURE, years=years, months=OBS_MONTHS)
    h = run['hydro']
    eco = run['ecology']
    S = [float(v) for v in run['S']]
    H = [float(v) for v in run['H']]

    fingerprints = {
        'clean_tmean': sha256_f8(cleaned['tmean']),
        'clean_tmin': sha256_f8(cleaned['tmin']),
        'clean_tmax': sha256_f8(cleaned['tmax']),
        'clean_pre': sha256_f8(cleaned['pre']),
        'clean_wind': sha256_f8(cleaned['wind']),
        'clean_sun': sha256_f8(cleaned['sun']),
        'forcing_pre': sha256_f8(F['pre']),
        'forcing_pes': sha256_f8(F['pes']),
        'forcing_eto': sha256_f8(F['eto']),
        'forcing_ep': sha256_f8(F['ep']),
        'forcing_pp': sha256_f8(F['pp']),
        'V': sha256_f8(h['V']),
        'area': sha256_f8(h['area']),
        'return_flow': sha256_f8(h['return_flow']),
        'exposed': sha256_f8(eco['exposed']),
        'E7': sha256_f8(eco['exposure_window']),
        'state': sha256_f8(eco['state']),
        'S': sha256_f8(S),
        'H': sha256_f8(H),
    }
    mismatches = {
        k: {'expected': EXPECTED_FINGERPRINTS[k], 'actual': fingerprints[k]}
        for k in EXPECTED_FINGERPRINTS
        if fingerprints.get(k) != EXPECTED_FINGERPRINTS[k]
    }
    if mismatches:
        raise SystemExit(f'deterministic-kernel fingerprint regression: {mismatches}')

    y = [float(OBS[yr]) for yr in years]
    (kc, kh), pred = fit_constrained_state_fixed(S, H, y, A0)
    score = metrics_decimal(pred, y)
    state_year_corr = pearson_decimal(S, [float(v) for v in years])
    dry = zero_storage_diagnostics(h['dates'], h['V'])

    rows = []
    for i, yr in enumerate(years):
        rows.append({
            'year': yr,
            'observed_area_m2': y[i],
            'predicted_area_m2': pred[i],
            'error_m2': pred[i] - y[i],
            'ecological_state_S': S[i],
            'return_flow_anomaly_H_m3': H[i],
        })

    result = {
        'status': 'PASS_STAGE62_OFFICIAL_DETERMINISTIC_CENTRAL_FIT',
        'model': 'Stage49/56 hydro-ecology, deterministic numerical implementation',
        'temporal_support': 'April-May mean',
        'eval_years': list(years),
        '2022_pond_area_used': False,
        '2011_role': 'initial/reference only',
        'selected_structure': dict(SELECTED_STRUCTURE),
        'observation_operator': 'A_pred=A0-Kc*S+Kh*H',
        'K_colonizable_m2': kc,
        'K_colonizable_fraction_of_A0': kc / A0,
        'K_hydro_m2_per_m3': kh,
        'metrics': score,
        'state_year_corr': state_year_corr,
        'predictions': rows,
        'S': S,
        'H': H,
        'physical_closure': {
            'mass_error_m3': float(h['mass_error']),
            'area_partition_error_m2': float(h['area_partition_error']),
            'precip_partition_error_m3': float(h['precip_partition_error']),
        },
        'zero_storage_diagnostics': dry,
        'forcing_source_missing_before_fill': source_missing_before_fill(),
        'forcing_missing_legacy_stage30_semantics': forcing_missing,
        'annual_precip_mm': annual_precip,
        'fingerprints': fingerprints,
        'fingerprint_contract_pass': True,
        'notes': [
            'No 2022 mapped pond-area target exists or is used.',
            'LOOCV/nested CV are not acceptance gates.',
            'Kc and Kh are calibrated observation-operator coefficients; they are not measured constants.',
            'This stage does not include the peat surface-expression G term; four-scenario peat comparison follows separately.',
        ],
    }

    (OUT / 'stage62_summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    import csv
    with (OUT / 'stage62_predictions.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if max(result['physical_closure'].values()) > 1e-8:
        raise SystemExit('physical closure failed')
    if score['nrmse_pct'] > 2.0:
        raise SystemExit('central six-observation nRMSE exceeds the retained 2% calibration screen')


if __name__ == '__main__':
    main()
