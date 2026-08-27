#!/usr/bin/env python3
"""Stage50B runner for the strict four-scenario peat sensitivity.

This is the corrected execution entry point for Stage50. It reuses the Stage50
process functions unchanged and fixes only the local-name collision between the
imported hydro() function and the Hydrosere-result dataframe variable.
"""
from __future__ import annotations

import json
import numpy as np
import pandas as pd

import stage50_four_scenario_peat_sensitivity as m


def main():
    F, _, _ = m.forcing()
    hp = {k: m.P49[k] for k in ['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']}
    h = m.hydro(F, hp)

    assert h['mass_error'] <= m.MASS_TOL_M3
    assert h['area_partition_error'] <= m.AREA_PARTITION_TOL_M2
    assert h['precip_partition_error'] <= m.PRECIP_PARTITION_TOL_M3

    exposed = np.clip((m.A0 - np.asarray(h['area'], float)) / m.A0, 0.0, 1.0)
    e = (pd.Series(exposed)
         .rolling(m.P49['est_window_d'], min_periods=m.P49['est_window_d'])
         .min().fillna(0.0).to_numpy())
    st = m.irreversible_state(e, m.P49['r_est_yr'])
    S = m.annual(h['dates'], st)
    H = m.annual_hydro(h['dates'], h['return_flow'], m.P49['hydro_window_d'])

    all_rows = []
    geometry_rows = []
    reference_predictions = []

    for rate in m.PEAT_RATES_MM_YR:
        Gd, depth, B, Ah, Ap, h0 = m.peat_geomorphic_loss(h['dates'], h['V'], rate)
        G = m.annual(h['dates'], Gd)
        scenarios = m.fit_scenarios(S, H, G)
        rank = {name: i + 1 for i, (name, *_rest) in enumerate(sorted(scenarios, key=lambda z: z[5]))}
        for name, kc, kh, pred, rm, nr in scenarios:
            all_rows.append({
                'peat_rate_mm_yr': rate,
                'Scenario': name,
                'RMSE_m2': rm,
                'nRMSE_pct': nr,
                'rank_within_rate': rank[name],
                'K_colonizable_m2': kc,
                'K_hydro': kh,
                **{f'pred_{int(y)}': float(pred[i]) for i, y in enumerate(m.YEARS)},
            })
            if abs(rate - m.REFERENCE_PEAT_RATE) < 1e-12:
                for i, y in enumerate(m.YEARS):
                    reference_predictions.append({
                        'Scenario': name,
                        'year': int(y),
                        'observed_m2': float(m.Y[i]),
                        'predicted_m2': float(pred[i]),
                        'error_m2': float(pred[i] - m.Y[i]),
                    })

        ymask2023 = pd.to_datetime(h['dates']).year.to_numpy() == 2023
        geometry_rows.append({
            'peat_rate_mm_yr': rate,
            'h0_reference_depth_m': h0,
            'peat_rise_2023_end_m': float(B[ymask2023][-1]),
            'mean_geomorphic_openwater_loss_eval_m2': float(np.mean(G)),
            **{f'G_{int(y)}_m2': float(G[i]) for i, y in enumerate(m.YEARS)},
        })

    df = pd.DataFrame(all_rows)
    gd = pd.DataFrame(geometry_rows)
    rp = pd.DataFrame(reference_predictions)
    df.to_csv(m.OUT / 'stage50_four_scenario_peat_sensitivity.csv', index=False)
    gd.to_csv(m.OUT / 'stage50_geomorphic_translation.csv', index=False)
    rp.to_csv(m.OUT / 'stage50_reference_3mm_predictions.csv', index=False)

    ref = df[np.isclose(df['peat_rate_mm_yr'], m.REFERENCE_PEAT_RATE)].sort_values('nRMSE_pct')
    integ = df[df['Scenario'] == 'Integrated Model'].sort_values('peat_rate_mm_yr')
    hydrosere = df[df['Scenario'] == 'Hydrosere Only Model'].sort_values('peat_rate_mm_yr')
    ecogeo = df[df['Scenario'] == 'Eco-Geo Only Model'].sort_values('peat_rate_mm_yr')
    baseline = df[df['Scenario'] == 'Baseline Model'].sort_values('peat_rate_mm_yr')

    summary = {
        'status': 'PASS_STAGE50',
        'execution_entry_point': 'stage50b_four_scenario_peat_sensitivity.py',
        'observed_area_years': [int(y) for y in m.YEARS],
        'pond_area_observation_2022': 'ABSENT',
        'water_balance': {
            'max_mass_error_m3': float(h['mass_error']),
            'max_area_partition_error_m2': float(h['area_partition_error']),
            'max_precip_partition_error_m3': float(h['precip_partition_error']),
        },
        'stage49_locked_parameters': m.P49,
        'hypsometric_translation': {
            'h0_reference_depth_m': float(gd['h0_reference_depth_m'].iloc[0]),
            'formula': 'h0=V0*(p+2)/(A0*p); A_peat=A0*(max(h-B,0)/h0)^(2/p); G=A_hydraulic-A_peat',
            'fitted_peat_scaling': False,
            'old_bottom_relax_0p08_used': False,
            'old_peat_scaling_0p70_used': False,
            'old_depth_relax_0p035_used': False,
        },
        'peat_rates_mm_yr': m.PEAT_RATES_MM_YR,
        'reference_3mm_metrics': ref[['Scenario','RMSE_m2','nRMSE_pct','rank_within_rate','K_colonizable_m2','K_hydro']].to_dict('records'),
        'integrated_rank1_for_all_tested_peat_rates': bool((integ['rank_within_rate'] == 1).all()),
        'integrated_nrmse_range_pct': [float(integ['nRMSE_pct'].min()), float(integ['nRMSE_pct'].max())],
        'hydrosere_nrmse_pct': float(hydrosere['nRMSE_pct'].iloc[0]),
        'ecogeo_nrmse_range_pct': [float(ecogeo['nRMSE_pct'].min()), float(ecogeo['nRMSE_pct'].max())],
        'baseline_nrmse_pct': float(baseline['nRMSE_pct'].iloc[0]),
        'best_integrated_peat_rate_mm_yr': float(integ.loc[integ['nRMSE_pct'].idxmin(), 'peat_rate_mm_yr']),
        'best_integrated_nrmse_pct': float(integ['nRMSE_pct'].min()),
        'interpretation': 'Scenario-neutral ranking at each externally prescribed peat rate; no penalty or objective term favors Integrated.',
    }
    (m.OUT / 'stage50_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
