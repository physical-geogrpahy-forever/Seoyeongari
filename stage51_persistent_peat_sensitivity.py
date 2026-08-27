#!/usr/bin/env python3
"""Stage51 — process-matched persistent peat accretion sensitivity.

This stage does not recalibrate the Stage49 hydrology and does not add a model
coefficient. It separates two quantities that should not be conflated:

1) persistent net vertical peat accretion, relevant to geomorphic elevation
   change over the modeled interval; the Seoyeongari Clymo-model field report
   gives a long-term lower/central/upper estimate of 0.29/0.38/0.47 mm/yr,
   with the field-derived central estimate 0.38 mm/yr used as reference;
2) recent near-surface apparent accumulation, 2.89--7.00 mm/yr, retained as an
   upper stress test but not interpreted as a persistent net elevation rate.

Scientific rationale: recent/acrotelm peat has undergone less decomposition and
surface peat undergoes substantial early compaction, so recent apparent rates
cannot automatically be propagated as long-term topographic rise. See Young et
al. (2019, Scientific Reports 9:17939, doi:10.1038/s41598-019-53879-8) and
Oekland & Ohlson (1998, Oikos 82:29-36, doi:10.2307/3546914).

No acceptance condition requires Integrated to rank first. The rank is reported
as an outcome, not imposed in the objective.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd

import stage50_four_scenario_peat_sensitivity as m

OUT = Path('stage51_outputs')
OUT.mkdir(exist_ok=True)

# Site-derived Clymo-model long-term peat accumulation estimates reported as
# lower / central / upper values. These are uncertainty-bound estimates from
# sparse radiocarbon control, not three independent replicate measurements.
FIELD_CLYMO_LONG_TERM_RATES_MM_YR = [0.29, 0.38, 0.47]
PRIMARY_RATES = FIELD_CLYMO_LONG_TERM_RATES_MM_YR
CENTRAL_RATE = 0.38
RECENT_STRESS_RATES = [2.89, 3.0, 5.0, 5.91, 7.0]


def setup_states():
    F, _, _ = m.forcing()
    hp = {k: m.P49[k] for k in ['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']}
    h = m.hydro(F, hp)
    exposed = np.clip((m.A0 - np.asarray(h['area'], float)) / m.A0, 0.0, 1.0)
    e = (pd.Series(exposed)
         .rolling(m.P49['est_window_d'], min_periods=m.P49['est_window_d'])
         .min().fillna(0.0).to_numpy())
    st = m.irreversible_state(e, m.P49['r_est_yr'])
    S = m.annual(h['dates'], st)
    H = m.annual_hydro(h['dates'], h['return_flow'], m.P49['hydro_window_d'])
    return h, S, H


def metrics_at_rate(h, S, H, rate):
    Gd, *_ = m.peat_geomorphic_loss(h['dates'], h['V'], rate)
    G = m.annual(h['dates'], Gd)
    scenarios = m.fit_scenarios(S, H, G)
    rows = []
    ordered = sorted(scenarios, key=lambda z: z[5])
    ranks = {z[0]: i + 1 for i, z in enumerate(ordered)}
    for name, kc, kh, pred, rm, nr in scenarios:
        rows.append({
            'peat_rate_mm_yr': float(rate),
            'Scenario': name,
            'RMSE_m2': float(rm),
            'nRMSE_pct': float(nr),
            'rank': int(ranks[name]),
            'K_colonizable_m2': float(kc),
            'K_hydro': float(kh),
            **{f'pred_{int(y)}': float(pred[i]) for i, y in enumerate(m.YEARS)},
        })
    return rows


def integrated_minus_hydrosere_nrmse(h, S, H, rate):
    rows = metrics_at_rate(h, S, H, rate)
    d = {r['Scenario']: r['nRMSE_pct'] for r in rows}
    return d['Integrated Model'] - d['Hydrosere Only Model']


def crossover_bisection(h, S, H, lo=2.0, hi=2.89, n=40):
    flo = integrated_minus_hydrosere_nrmse(h, S, H, lo)
    fhi = integrated_minus_hydrosere_nrmse(h, S, H, hi)
    if flo == 0:
        return lo
    if fhi == 0:
        return hi
    if flo * fhi > 0:
        return None
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        fm = integrated_minus_hydrosere_nrmse(h, S, H, mid)
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)


def main():
    h, S, H = setup_states()
    primary = [r for rate in PRIMARY_RATES for r in metrics_at_rate(h, S, H, rate)]
    stress = [r for rate in RECENT_STRESS_RATES for r in metrics_at_rate(h, S, H, rate)]
    pd.DataFrame(primary).to_csv(OUT / 'stage51_primary_persistent_net_accretion.csv', index=False)
    pd.DataFrame(stress).to_csv(OUT / 'stage51_recent_apparent_rate_stress_test.csv', index=False)

    central = metrics_at_rate(h, S, H, CENTRAL_RATE)
    cdf = pd.DataFrame(central).sort_values('nRMSE_pct')
    cdf.to_csv(OUT / 'stage51_central_0p38_scenario_metrics.csv', index=False)

    p = pd.DataFrame(primary)
    pi = p[p['Scenario'] == 'Integrated Model'].sort_values('peat_rate_mm_yr')
    ph = p[p['Scenario'] == 'Hydrosere Only Model'].sort_values('peat_rate_mm_yr')
    merged = pi[['peat_rate_mm_yr','RMSE_m2','nRMSE_pct','rank']].merge(
        ph[['peat_rate_mm_yr','RMSE_m2','nRMSE_pct']],
        on='peat_rate_mm_yr', suffixes=('_integrated','_hydrosere'))
    merged['rmse_reduction_vs_hydrosere_pct'] = 100.0 * (
        merged['RMSE_m2_hydrosere'] - merged['RMSE_m2_integrated']) / merged['RMSE_m2_hydrosere']
    merged.to_csv(OUT / 'stage51_integrated_increment_primary_range.csv', index=False)

    crossover = crossover_bisection(h, S, H)
    summary = {
        'status': 'PASS_STAGE51_ANALYSIS',
        'observed_area_years': [int(y) for y in m.YEARS],
        'pond_area_observation_2022': 'ABSENT',
        'primary_process_quantity': 'persistent net vertical peat accretion relevant to geomorphic elevation change',
        'field_clymo_long_term_lower_central_upper_mm_yr': FIELD_CLYMO_LONG_TERM_RATES_MM_YR,
        'primary_site_informed_range_mm_yr': PRIMARY_RATES,
        'central_reference_mm_yr': CENTRAL_RATE,
        'central_reference_statistic': 'field-derived Clymo-model central estimate',
        'central_reference_reason': 'central estimate in the Seoyeongari field report (0.29/0.38/0.47 mm/yr lower/central/upper); not selected by pond-area fit optimization',
        'recent_apparent_accumulation_stress_range_mm_yr': RECENT_STRESS_RATES,
        'recent_range_role': 'upper stress test only; not assumed equal to sustained net topographic rise',
        'central_metrics': cdf[['Scenario','RMSE_m2','nRMSE_pct','rank','K_colonizable_m2','K_hydro']].to_dict('records'),
        'integrated_rank1_across_primary_range': bool((pi['rank'] == 1).all()),
        'integrated_primary_nrmse_range_pct': [float(pi['nRMSE_pct'].min()), float(pi['nRMSE_pct'].max())],
        'hydrosere_nrmse_pct': float(ph['nRMSE_pct'].iloc[0]),
        'integrated_rmse_reduction_vs_hydrosere_primary_pct': [
            float(merged['rmse_reduction_vs_hydrosere_pct'].min()),
            float(merged['rmse_reduction_vs_hydrosere_pct'].max()),
        ],
        'integrated_hydrosere_crossover_if_recent_rate_forced_as_persistent_mm_yr': None if crossover is None else float(crossover),
        'rank_was_not_an_acceptance_gate': True,
        'water_balance': {
            'max_mass_error_m3': float(h['mass_error']),
            'max_area_partition_error_m2': float(h['area_partition_error']),
            'max_precip_partition_error_m3': float(h['precip_partition_error']),
        },
        'literature_basis': [
            'Young et al. 2019 Scientific Reports 9:17939 doi:10.1038/s41598-019-53879-8',
            'Oekland & Ohlson 1998 Oikos 82:29-36 doi:10.2307/3546914',
        ],
    }
    (OUT / 'stage51_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
