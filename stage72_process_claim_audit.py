#!/usr/bin/env python3
"""Stage72 — numerical audit of what processes the accepted model actually couples.

This stage changes no parameter and performs no calibration.  It tests causal
dependencies in the accepted deterministic code so manuscript claims can be
restricted to mechanisms that are actually implemented.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np

from eghm_deterministic_forcing import deterministic_forcing
from eghm_deterministic_kernel import (
    A0, EVAL_YEARS, OBS_MONTHS, SELECTED_STRUCTURE,
    annual_support, build_features, continuous_exposure_state, hydro, sha256_f8,
)
from eghm_deterministic_scenarios import fit_four_scenarios, peat_geomorphic_loss

OUT = Path('stage72_outputs')
OUT.mkdir(exist_ok=True)
OBS = {2013:2154.430, 2015:2147.678, 2017:2051.218, 2019:2045.159, 2021:1965.256, 2023:1882.700}
PEAT = 0.38


def same_f8(a, b):
    return sha256_f8(a) == sha256_f8(b)


def main():
    F, _, _, _ = deterministic_forcing()
    P = dict(SELECTED_STRUCTURE)
    h = hydro(F, P)
    eco = continuous_exposure_state(h['area'], P['r_est_yr'], int(P['est_window_d']))

    # 1) Ecology-rate perturbation: ecological state must change, hydraulic state must not.
    Peco = dict(P)
    Peco['r_est_yr'] = P['r_est_yr'] * 2.0
    h_eco_rate = hydro(F, Peco)
    eco_fast = continuous_exposure_state(h_eco_rate['area'], Peco['r_est_yr'], int(Peco['est_window_d']))
    ecology_changes_state = not same_f8(eco['state'], eco_fast['state'])
    ecology_changes_hydraulic_V = not same_f8(h['V'], h_eco_rate['V'])
    ecology_changes_hydraulic_area = not same_f8(h['area'], h_eco_rate['area'])

    # 2) Legacy forcing products CN-runoff (pes) and 0.87 pond-rain (pp) are present
    # in the forcing object for historical compatibility.  Prove that the current hydro
    # kernel does not read them by replacing them with extreme values.
    Flegacy = {k: np.asarray(v).copy() for k, v in F.items()}
    Flegacy['pes'] = np.asarray(Flegacy['pes'], dtype=float) * 1234.5 + 999.0
    Flegacy['pp'] = np.asarray(Flegacy['pp'], dtype=float) * 0.001
    h_legacy_changed = hydro(Flegacy, P)
    legacy_pes_pp_change_hydraulic_V = not same_f8(h['V'], h_legacy_changed['V'])
    legacy_pes_pp_change_hydraulic_area = not same_f8(h['area'], h_legacy_changed['area'])

    # 3) Peat is translated after the conserved hydro trajectory.  Demonstrate that
    # geomorphic surface-expression loss changes with peat rate while V is untouched.
    G0, _, _ = peat_geomorphic_loss(h['dates'], h['V'], 0.0, P['V0'], P['p_shape'])
    Gc, h0, _ = peat_geomorphic_loss(h['dates'], h['V'], PEAT, P['V0'], P['p_shape'])
    peat_changes_surface_expression = not same_f8(G0, Gc)
    # No second hydro solve exists in the scenario path, so the conserved trajectory is shared.
    peat_changes_conserved_hydraulic_V = False

    # 4) Reproduce central scenario predictions and identify where each process enters.
    f = build_features(F, P, years=EVAL_YEARS, months=OBS_MONTHS)
    S = [float(v) for v in f['S']]
    H = [float(v) for v in f['H']]
    G = annual_support(h['dates'], Gc, years=EVAL_YEARS, months=OBS_MONTHS)
    y = [float(OBS[yr]) for yr in EVAL_YEARS]
    scenarios = fit_four_scenarios(S, H, G, y, A0)
    ordered = sorted(scenarios, key=lambda z: (z['nRMSE_pct'], z['RMSE_m2'], z['Scenario']))

    scenario_rows = []
    for i, z in enumerate(ordered, 1):
        scenario_rows.append({
            'rank': i,
            'Scenario': z['Scenario'],
            'RMSE_m2': float(z['RMSE_m2']),
            'nRMSE_pct': float(z['nRMSE_pct']),
            'uses_ecological_state_S': z['Scenario'] in {'Hydrosere Only Model', 'Integrated Model'},
            'uses_peat_surface_expression_G': z['Scenario'] in {'Eco-Geo Only Model', 'Integrated Model'},
            'shares_same_conserved_hydrology': True,
        })

    claims = [
        {
            'claim': 'hydrarch succession changes evapotranspiration in the accepted model',
            'implemented': False,
            'evidence': 'r_est perturbation changes ecological state but leaves daily V and hydraulic area bit-identical; S enters only the mapped-area observation operator.',
        },
        {
            'claim': 'peat accumulation changes conserved water-storage capacity in the accepted model',
            'implemented': False,
            'evidence': 'peat rise is translated after the shared hydro solve as G = A_hydraulic - A_peat; conserved V is not removed or re-solved.',
        },
        {
            'claim': 'peat accumulation changes modeled open-water surface expression',
            'implemented': True,
            'evidence': 'G changes between zero and 0.38 mm/yr peat-rise cases.',
        },
        {
            'claim': 'hydrologic exposure drives ecological establishment state',
            'implemented': True,
            'evidence': 'daily hydraulic area determines exposed fraction; a causal 7-d continuous-exposure minimum drives irreversible establishment.',
        },
        {
            'claim': 'NRCS-CN runoff depth pes is an active flux in the accepted hydro kernel',
            'implemented': False,
            'evidence': 'extreme replacement of forcing[pes] leaves V and hydraulic area bit-identical.',
        },
        {
            'claim': '0.87 effective pond precipitation pp is an active flux in the accepted hydro kernel',
            'implemented': False,
            'evidence': 'extreme replacement of forcing[pp] leaves V and hydraulic area bit-identical.',
        },
        {
            'claim': 'raw precipitation is partitioned without spatial overlap across upland, non-open wetland and open-water footprints',
            'implemented': True,
            'evidence': 'hydro uses forcing[pre] directly and reports exact area and precipitation partition closure.',
        },
    ]

    structural_mismatches = [c['claim'] for c in claims if not c['implemented']]
    result = {
        'status': 'PASS_STAGE72_PROCESS_CLAIM_AUDIT_WITH_STRUCTURAL_MISMATCHES',
        'model_process_changed': False,
        'model_parameter_changed': False,
        'calibration_performed': False,
        'dependency_tests': {
            'r_est_doubled_changes_ecological_state': ecology_changes_state,
            'r_est_doubled_changes_hydraulic_V': ecology_changes_hydraulic_V,
            'r_est_doubled_changes_hydraulic_area': ecology_changes_hydraulic_area,
            'legacy_pes_pp_extreme_change_changes_hydraulic_V': legacy_pes_pp_change_hydraulic_V,
            'legacy_pes_pp_extreme_change_changes_hydraulic_area': legacy_pes_pp_change_hydraulic_area,
            'peat_0_to_0p38_changes_surface_expression_G': peat_changes_surface_expression,
            'peat_0_to_0p38_changes_conserved_hydraulic_V': peat_changes_conserved_hydraulic_V,
        },
        'actual_coupling_graph': [
            'meteorological forcing -> daily conserved hydrology',
            'daily hydraulic area -> exposed fraction -> continuous-exposure ecological establishment S',
            'daily conserved V + prescribed persistent peat rise -> geomorphic surface-expression loss G',
            'S + G + short-term hydrologic feature H -> mapped open-water pond-area observation operator',
            'no vegetation-to-ET feedback in accepted kernel',
            'no peat-to-conserved-storage feedback in accepted kernel',
        ],
        'central_scenario_metrics': scenario_rows,
        'h0_reference_depth_m': float(h0),
        'claim_audit': claims,
        'structural_mismatches_requiring_manuscript_revision_or_model_redesign': structural_mismatches,
        'manuscript_implication': (
            'The accepted Stage71 model can be described as an integrated process-informed open-water surface-expression model with one-way hydro-to-ecology coupling, not as a fully feedback-coupled model in which succession alters ET and peat alters conserved storage capacity.'
        ),
        'decision_required_before_manuscript_rewrite': (
            'Either narrow manuscript mechanism claims to the implemented Stage71 structure, or design and independently constrain genuine vegetation-ET and/or peat-storage feedbacks and then re-evaluate all four scenarios without ranking-driven tuning.'
        ),
        'physical_closure': {
            'mass_error_m3': float(h['mass_error']),
            'area_partition_error_m2': float(h['area_partition_error']),
            'precip_partition_error_m3': float(h['precip_partition_error']),
        },
    }

    # Audit assertions: these encode what the current accepted source actually does.
    if not ecology_changes_state:
        raise SystemExit('ecology perturbation failed to change ecological state')
    if ecology_changes_hydraulic_V or ecology_changes_hydraulic_area:
        raise SystemExit('unexpected ecology-to-hydrology feedback appeared')
    if legacy_pes_pp_change_hydraulic_V or legacy_pes_pp_change_hydraulic_area:
        raise SystemExit('legacy pes/pp unexpectedly became active in hydro kernel')
    if not peat_changes_surface_expression:
        raise SystemExit('peat surface-expression process unexpectedly inactive')
    if max(result['physical_closure'].values()) > 1e-8:
        raise SystemExit('physical closure failed')

    (OUT / 'stage72_summary.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
