#!/usr/bin/env python3
"""Stage55 — observation temporal-support / aggregation-window robustness.

Why this stage exists
---------------------
The mapped pond areas come from NGII orthorectified airborne-image snapshots
acquired in April or May, but the current Stage49-52 observation features are
aggregated over May-June because exact year-specific flight dates were not
available during model reconstruction.

This stage does NOT select a new window and does NOT add/recalibrate hydrologic
process parameters. It asks whether the scenario comparison is robust to the
uncertain temporal support of the historical image snapshots.

Tested windows:
- April
- May
- April-May
- May-June (current reference)
- April-June

Two diagnostics are kept separate:
A) fixed-transfer: lock the May-June central Stage52 observation coefficients
   and transfer them to features aggregated over each alternative window;
B) profile-refit: fit only Kc/Kh for each window, keeping every process parameter
   fixed. This tests whether the same process states can support the observations
   under a different aggregation convention; it is not independent validation.

No window or scenario ranking is an acceptance gate. 2022 remains absent as a
pond-area observation.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import stage50_four_scenario_peat_sensitivity as m
import stage51_persistent_peat_sensitivity as s51
import stage52_oat_provenance as s52
from stage49_six_observation_irreversible_recruitment import irreversible_state

OUT = Path('stage55_outputs')
OUT.mkdir(exist_ok=True)

WINDOWS = {
    'April': [4],
    'May': [5],
    'April-May': [4, 5],
    'May-June': [5, 6],
    'April-June': [4, 5, 6],
}
CURRENT_WINDOW = 'May-June'
PEAT_RATE = float(s51.CENTRAL_RATE)


def aggregate_eval(dt, x, months):
    dt = pd.to_datetime(dt)
    yr = dt.year.to_numpy()
    mo = dt.month.to_numpy()
    x = np.asarray(x, float)
    return np.array([
        float(np.mean(x[(yr == y) & np.isin(mo, months)]))
        for y in m.YEARS
    ])


def hydro_feature(dt, q, rolling_days, months):
    dt = pd.to_datetime(dt)
    yr = dt.year.to_numpy()
    mo = dt.month.to_numpy()
    rr = pd.Series(np.asarray(q, float), index=dt).rolling(int(rolling_days), min_periods=1).sum().to_numpy()
    ref_mask = (yr == 2011) & np.isin(mo, months)
    ref = float(np.mean(rr[ref_mask]))
    out = np.array([
        float(np.mean(rr[(yr == y) & np.isin(mo, months)]) - ref)
        for y in m.YEARS
    ])
    return out, ref


def make_daily_states():
    F, _, _ = m.forcing()
    hp = {k: m.P49[k] for k in ['V0', 'p_shape', 'tau_surf', 'local_frac', 'tau_fast', 'k_gw_mm_d']}
    h = m.hydro(F, hp)

    exposed = np.clip((m.A0 - np.asarray(h['area'], float)) / m.A0, 0.0, 1.0)
    ew = int(m.P49['est_window_d'])
    E = pd.Series(exposed).rolling(ew, min_periods=ew).min().fillna(0.0).to_numpy()
    state = irreversible_state(E, m.P49['r_est_yr'])
    Gd = s52.geomorphic_loss(h['dates'], h['V'], PEAT_RATE, m.P49['V0'], m.P49['p_shape'])
    return h, state, Gd


def features_for_window(h, state, Gd, months):
    S = aggregate_eval(h['dates'], state, months)
    H, Href = hydro_feature(h['dates'], h['return_flow'], m.P49['hydro_window_d'], months)
    G = aggregate_eval(h['dates'], Gd, months)
    Ahyd = aggregate_eval(h['dates'], h['area'], months)
    return S, H, G, Ahyd, Href


def fixed_scenarios(S, H, G, central_coeff):
    out = []
    for name, b in central_coeff.items():
        pred = s52.predict_with_coeff(name, S, H, G, b['Kc'], b['Kh'])
        rm, nr = m.metric(pred)
        out.append((name, float(b['Kc']), float(b['Kh']), pred, rm, nr))
    return out


def rows_for(window, months, mode, scenarios, S, H, G, Ahyd, Href):
    ordered = sorted(scenarios, key=lambda z: z[5])
    ranks = {z[0]: i + 1 for i, z in enumerate(ordered)}
    rows = []
    for name, kc, kh, pred, rm, nr in scenarios:
        rows.append({
            'window': window,
            'months': '-'.join(str(x) for x in months),
            'mode': mode,
            'is_current_window': window == CURRENT_WINDOW,
            'Scenario': name,
            'RMSE_m2': float(rm),
            'nRMSE_pct': float(nr),
            'rank': int(ranks[name]),
            'K_colonizable_m2': float(kc),
            'K_hydro_m_inv': float(kh),
            'H_reference_2011_window_m3': float(Href),
            **{f'S_{int(y)}': float(S[i]) for i, y in enumerate(m.YEARS)},
            **{f'H_{int(y)}_m3': float(H[i]) for i, y in enumerate(m.YEARS)},
            **{f'G_{int(y)}_m2': float(G[i]) for i, y in enumerate(m.YEARS)},
            **{f'hydraulic_area_{int(y)}_m2': float(Ahyd[i]) for i, y in enumerate(m.YEARS)},
            **{f'pred_{int(y)}': float(pred[i]) for i, y in enumerate(m.YEARS)},
        })
    return rows


def main():
    h, state, Gd = make_daily_states()
    central_coeff, _ = s52.central_coefficients()

    all_rows = []
    direct_rows = []
    for window, months in WINDOWS.items():
        S, H, G, Ahyd, Href = features_for_window(h, state, Gd, months)

        fixed = fixed_scenarios(S, H, G, central_coeff)
        prof = m.fit_scenarios(S, H, G)
        all_rows.extend(rows_for(window, months, 'fixed_transfer', fixed, S, H, G, Ahyd, Href))
        all_rows.extend(rows_for(window, months, 'profile_refit', prof, S, H, G, Ahyd, Href))

        # Pure hydraulic footprint diagnostic, with no observation-operator fit.
        hrm, hnr = m.metric(Ahyd)
        direct_rows.append({
            'window': window,
            'months': '-'.join(str(x) for x in months),
            'hydraulic_area_RMSE_m2': float(hrm),
            'hydraulic_area_nRMSE_pct': float(hnr),
            **{f'hydraulic_area_{int(y)}_m2': float(Ahyd[i]) for i, y in enumerate(m.YEARS)},
        })

    df = pd.DataFrame(all_rows)
    dd = pd.DataFrame(direct_rows)
    df.to_csv(OUT / 'stage55_window_scenario_all.csv', index=False)
    df[df.mode == 'fixed_transfer'].to_csv(OUT / 'stage55_window_fixed_transfer.csv', index=False)
    df[df.mode == 'profile_refit'].to_csv(OUT / 'stage55_window_profile_refit.csv', index=False)
    dd.to_csv(OUT / 'stage55_window_direct_hydraulic_area.csv', index=False)

    summary_rows = []
    for window in WINDOWS:
        for mode in ['fixed_transfer', 'profile_refit']:
            x = df[(df.window == window) & (df.mode == mode)]
            integ = x[x.Scenario == 'Integrated Model'].iloc[0]
            hyd = x[x.Scenario == 'Hydrosere Only Model'].iloc[0]
            summary_rows.append({
                'window': window,
                'mode': mode,
                'Integrated_nRMSE_pct': float(integ.nRMSE_pct),
                'Integrated_rank': int(integ['rank']),
                'Hydrosere_nRMSE_pct': float(hyd.nRMSE_pct),
                'Integrated_minus_Hydrosere_nRMSE_pp': float(integ.nRMSE_pct - hyd.nRMSE_pct),
                'top_scenario': str(x.sort_values('nRMSE_pct').iloc[0].Scenario),
            })
    sd = pd.DataFrame(summary_rows)
    sd.to_csv(OUT / 'stage55_window_summary.csv', index=False)

    current = sd[sd.window == CURRENT_WINDOW]
    alt = sd[sd.window != CURRENT_WINDOW]

    summary = {
        'status': 'PASS_STAGE55_TEMPORAL_SUPPORT_AUDIT',
        'pond_area_observation_2022': 'ABSENT',
        'image_temporal_support': 'NGII orthorectified airborne-image snapshots acquired in April or May; exact year-specific dates not recovered in current archive',
        'current_model_window': CURRENT_WINDOW,
        'tested_windows': WINDOWS,
        'window_selection_used_for_acceptance_or_optimization': False,
        'process_parameters_refit': False,
        'fixed_transfer_definition': 'May-June Stage52 Kc/Kh locked and transferred to alternative temporal feature aggregations',
        'profile_refit_definition': 'only Kc/Kh refit within each window; process parameters fixed',
        'current_window_summary': current.to_dict('records'),
        'alternative_window_summary': alt.to_dict('records'),
        'fixed_transfer_integrated_rank1_window_count': int(((sd.mode == 'fixed_transfer') & (sd.Integrated_rank == 1)).sum()),
        'profile_refit_integrated_rank1_window_count': int(((sd.mode == 'profile_refit') & (sd.Integrated_rank == 1)).sum()),
        'n_windows': len(WINDOWS),
        'direct_hydraulic_area': dd.to_dict('records'),
        'physical_closure': {
            'mass_error_m3': float(h['mass_error']),
            'area_partition_error_m2': float(h['area_partition_error']),
            'precip_partition_error_m3': float(h['precip_partition_error']),
        },
        'interpretation_rule': 'No alternative window is adopted solely because it reduces RMSE. Exact acquisition dates, if recovered, have methodological priority over fit ranking.',
    }
    (OUT / 'stage55_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
