#!/usr/bin/env python3
"""Stage64 — official deterministic OAT robustness for April-May EGHM.

Recomputes the Stage58 one-at-a-time process sensitivity using only the
cross-runner deterministic numerical kernel established in Stages61d-63.

Two diagnostics remain strictly separated:
  1) fixed: central Stage63 observation-operator coefficients Kc/Kh are locked;
  2) profile_refit: only Kc/Kh are recalibrated after each process perturbation.

OAT values are inherited internal admissible calibration-search support. They
are not claimed as independently measured physical uncertainty intervals.
Scenario rank is reported as an outcome and is never an acceptance criterion.
"""
from __future__ import annotations

from decimal import Decimal, localcontext
import json
from pathlib import Path
from typing import Dict, List, Sequence

import pandas as pd

from eghm_deterministic_fit import D
from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_kernel import (
    A0, EVAL_YEARS, OBS_MONTHS, SELECTED_STRUCTURE,
    annual_support, build_features,
)
from eghm_deterministic_scenarios import (
    fit_four_scenarios, metrics_fixed, peat_geomorphic_loss, predict_fixed,
)

OUT = Path('stage64_outputs')
OUT.mkdir(exist_ok=True)
PEAT_RATE = 0.38
CENTRAL = dict(SELECTED_STRUCTURE)
OBS = {
    2013: 2154.430,
    2015: 2147.678,
    2017: 2051.218,
    2019: 2045.159,
    2021: 1965.256,
    2023: 1882.700,
}
Y = [float(OBS[y]) for y in EVAL_YEARS]

OAT = {
    'V0': [1000.0, 1600.0, 2200.0],
    'p_shape': [6.0, 12.0, 18.0],
    'tau_surf': [60.0, 120.0, 240.0],
    'local_frac': [0.15, 0.30, 0.45],
    'tau_fast': [30.0, 60.0, 120.0],
    'k_gw_mm_d': [0.05, 0.10, 0.25, 1.0, 2.0, 4.0],
    'r_est_yr': [0.025, 0.05, 0.10, 0.25],
    'hydro_window_d': [14, 30, 60, 90, 180],
    'est_window_d': [7, 14, 21],
}

PROVENANCE = [
    ('V0', 1000.0, 'm3', 'calibrated effective geometry/storage scale'),
    ('p_shape', 18.0, 'dimensionless', 'calibrated hypsometric shape parameter'),
    ('tau_surf', 60.0, 'day', 'calibrated effective surface drainage/storage timescale'),
    ('local_frac', 0.45, 'fraction', 'calibrated local perched-return routing fraction'),
    ('tau_fast', 30.0, 'day', 'calibrated effective fast-return reservoir timescale'),
    ('k_gw_mm_d', 4.0, 'mm day-1', 'calibrated effective area-proportional subsurface loss; not Ksat'),
    ('r_est_yr', 0.05, 'yr-1', 'calibrated persistent occupation/establishment rate'),
    ('hydro_window_d', 14, 'day', 'calibrated causal antecedent return-flow feature window after April-May alignment'),
    ('est_window_d', 7, 'day', 'calibrated/literature-bounded continuous exposure timing parameter'),
    ('peat_rate_persistent', PEAT_RATE, 'mm yr-1', 'field-derived long-term persistent-net central estimate'),
]

EXPECTED_CENTRAL = {
    'Integrated Model': 1.4113250129695185,
    'Hydrosere Only Model': 1.5865682357652557,
    'Eco-Geo Only Model': 10.558291389812902,
    'Baseline Model': 10.897125695439739,
}


def corr_fixed(x: Sequence[float], y: Sequence[float]) -> float:
    """80-digit deterministic Pearson correlation."""
    if len(x) != len(y) or len(x) < 2:
        raise ValueError('correlation inputs must have equal length >=2')
    with localcontext() as ctx:
        ctx.prec = 80
        xd = [D(v) for v in x]; yd = [D(v) for v in y]
        n = Decimal(len(xd))
        mx = sum(xd, Decimal(0)) / n; my = sum(yd, Decimal(0)) / n
        sx = sum(((v-mx)*(v-mx) for v in xd), Decimal(0))
        sy = sum(((v-my)*(v-my) for v in yd), Decimal(0))
        if sx == 0 or sy == 0:
            return 1.0
        cov = sum(((xd[i]-mx)*(yd[i]-my) for i in range(len(xd))), Decimal(0))
        return float(cov / (sx*sy).sqrt())


def state_for(P: Dict[str, float], forcing):
    f = build_features(forcing, P, years=EVAL_YEARS, months=OBS_MONTHS)
    h = f['hydro']
    Gd, _, _ = peat_geomorphic_loss(h['dates'], h['V'], PEAT_RATE, P['V0'], P['p_shape'])
    G = annual_support(h['dates'], Gd, years=EVAL_YEARS, months=OBS_MONTHS)
    corr = corr_fixed(f['S'], [float(y) for y in EVAL_YEARS])
    return h, [float(v) for v in f['S']], [float(v) for v in f['H']], [float(v) for v in G], corr


def central_coefficients(forcing):
    h, S, H, G, corr = state_for(CENTRAL, forcing)
    sc = fit_four_scenarios(S, H, G, Y, a0=A0)
    cc = {
        r['Scenario']: {
            'Kc': float(r['K_colonizable_m2']),
            'Kh': float(r['K_hydro_m2_per_m3']),
        }
        for r in sc
    }
    return cc, (h, S, H, G, corr, sc)


def predict(name: str, S: Sequence[float], H: Sequence[float], G: Sequence[float], kc: float, kh: float) -> List[float]:
    base = [A0] * len(Y)
    negS = [-float(v) for v in S]
    if name == 'Baseline Model':
        return predict_fixed(base, H, kh)
    if name == 'Hydrosere Only Model':
        return predict_fixed(base, negS, kc, H, kh)
    geom = [A0 - float(G[i]) for i in range(len(Y))]
    if name == 'Eco-Geo Only Model':
        return predict_fixed(geom, H, kh)
    if name == 'Integrated Model':
        return predict_fixed(geom, negS, kc, H, kh)
    raise KeyError(name)


def rows_for(parameter: str, value: float, mode: str, cc, forcing):
    P = dict(CENTRAL); P[parameter] = value
    h, S, H, G, corr = state_for(P, forcing)
    if mode == 'fixed':
        sc = []
        for name, b in cc.items():
            pr = predict(name, S, H, G, b['Kc'], b['Kh'])
            m = metrics_fixed(pr, Y)
            sc.append({
                'Scenario': name, 'K_colonizable_m2': b['Kc'],
                'K_hydro_m2_per_m3': b['Kh'], 'pred': pr, **m,
            })
    elif mode == 'profile_refit':
        sc = fit_four_scenarios(S, H, G, Y, a0=A0)
    else:
        raise ValueError(mode)

    ordered = sorted(sc, key=lambda z: z['nRMSE_pct'])
    ranks = {z['Scenario']: i+1 for i, z in enumerate(ordered)}
    central_v = float(CENTRAL[parameter])
    out = []
    for z in sc:
        pr = z['pred']
        out.append({
            'mode': mode,
            'parameter': parameter,
            'value': float(value),
            'is_central_value': abs(float(value)-central_v) < 1e-12,
            'Scenario': z['Scenario'],
            'RMSE_m2': float(z['RMSE_m2']),
            'nRMSE_pct': float(z['nRMSE_pct']),
            'rank': int(ranks[z['Scenario']]),
            'K_colonizable_m2': float(z['K_colonizable_m2']),
            'K_hydro_m2_per_m3': float(z['K_hydro_m2_per_m3']),
            'state_year_corr': float(corr),
            'mass_error_m3': float(h['mass_error']),
            'area_partition_error_m2': float(h['area_partition_error']),
            'precip_partition_error_m3': float(h['precip_partition_error']),
            **{f'pred_{y}': float(pr[i]) for i, y in enumerate(EVAL_YEARS)},
        })
    return out


def main():
    forcing, missing, annual, _ = deterministic_forcing()
    cc, central_state = central_coefficients(forcing)
    h0, S0, H0, G0, corr0, sc0 = central_state

    central_metrics = {r['Scenario']: float(r['nRMSE_pct']) for r in sc0}
    central_contract = all(abs(central_metrics[k] - EXPECTED_CENTRAL[k]) <= 1e-12 for k in EXPECTED_CENTRAL)
    if not central_contract:
        raise SystemExit(f'Stage64 central Stage63 contract failed: {central_metrics!r}')

    rows = []
    for p, vals in OAT.items():
        for v in vals:
            rows.extend(rows_for(p, v, 'fixed', cc, forcing))
            rows.extend(rows_for(p, v, 'profile_refit', cc, forcing))
    df = pd.DataFrame(rows)
    df.to_csv(OUT/'stage64_oat_all.csv', index=False)
    df[df['mode']=='fixed'].to_csv(OUT/'stage64_oat_fixed.csv', index=False)
    df[df['mode']=='profile_refit'].to_csv(OUT/'stage64_oat_profile_refit.csv', index=False)

    prov = pd.DataFrame(PROVENANCE, columns=['parameter','central_value','unit','classification'])
    edge = {p: (float(CENTRAL[p]) == float(min(v)) or float(CENTRAL[p]) == float(max(v))) for p,v in OAT.items()}
    prov['central_at_edge_of_internal_oat_support'] = prov['parameter'].map(edge).fillna(False)
    prov.to_csv(OUT/'stage64_parameter_provenance.csv', index=False)

    nc = df[~df.is_central_value]
    fi = nc[(nc['mode']=='fixed') & (nc.Scenario=='Integrated Model')]
    pi = nc[(nc['mode']=='profile_refit') & (nc.Scenario=='Integrated Model')]
    reversals = []
    for mode in ('fixed','profile_refit'):
        x = nc[nc['mode']==mode]
        for (p,v), g in x.groupby(['parameter','value'], sort=True):
            top = g.sort_values(['nRMSE_pct','Scenario']).iloc[0]
            integ = g[g.Scenario=='Integrated Model'].iloc[0]
            if int(integ['rank']) != 1:
                reversals.append({
                    'mode': mode, 'parameter': str(p), 'value': float(v),
                    'top_scenario': str(top.Scenario),
                    'top_nRMSE_pct': float(top.nRMSE_pct),
                    'Integrated_nRMSE_pct': float(integ.nRMSE_pct),
                    'difference_pp': float(integ.nRMSE_pct-top.nRMSE_pct),
                })
    pd.DataFrame(reversals).to_csv(OUT/'stage64_rank_reversals.csv', index=False)

    closure = {
        'mass_error_m3': float(h0['mass_error']),
        'area_partition_error_m2': float(h0['area_partition_error']),
        'precip_partition_error_m3': float(h0['precip_partition_error']),
    }
    if max(closure.values()) > 1e-8:
        raise SystemExit(f'Stage64 closure failed: {closure!r}')

    central_rows = sorted(sc0, key=lambda z: z['nRMSE_pct'])
    summary = {
        'status': 'PASS_STAGE64_OFFICIAL_DETERMINISTIC_OAT',
        'observation_support': 'April-May mean',
        'eval_years': list(EVAL_YEARS),
        '2022_pond_area_used': False,
        'central_process_parameters': CENTRAL,
        'central_peat_rate_mm_yr': PEAT_RATE,
        'oat_values_role': 'internal admissible calibration-search support; not independent physical uncertainty intervals',
        'noncentral_setting_count': int(len(fi)),
        'fixed_integrated_rank1_count': int((fi['rank']==1).sum()),
        'profile_integrated_rank1_count': int((pi['rank']==1).sum()),
        'rank_reversals': reversals,
        'central_metrics': [
            {
                'Scenario': r['Scenario'], 'RMSE_m2': float(r['RMSE_m2']),
                'nRMSE_pct': float(r['nRMSE_pct']),
                'K_colonizable_m2': float(r['K_colonizable_m2']),
                'K_hydro_m2_per_m3': float(r['K_hydro_m2_per_m3']),
            }
            for r in central_rows
        ],
        'parameters_central_at_edge_of_internal_oat_support': [p for p in OAT if edge[p]],
        'central_state_year_corr': float(corr0),
        'central_stage63_contract_pass': bool(central_contract),
        'scenario_rank_not_acceptance_gate': True,
        'physical_closure': closure,
        'forcing_source_missing_before_fill': missing,
        'annual_precip_mm': annual,
    }
    (OUT/'stage64_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
