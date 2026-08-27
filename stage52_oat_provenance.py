#!/usr/bin/env python3
"""Stage52 — provenance audit and OAT robustness for the Stage51 strict model.

Two sensitivity questions are intentionally separated:

A. FIXED-COEFFICIENT OAT (primary robustness test)
   The central 0.38 mm/yr four-scenario observation-operator coefficients are
   locked once. One hydrologic/ecological process parameter is then changed at
   a time. No Kc/Kh refitting is allowed. This asks whether the *locked model*
   and scenario ranking are robust.

B. PROFILE-REFIT OAT (secondary calibration diagnostic)
   For the same one-at-a-time process perturbation, Kc/Kh are refitted using all
   six observed pond-area years. This asks whether the altered process setting
   can be recalibrated; it is not a fixed-parameter sensitivity test.

The tested values are the Stage45/49 admissible calibration-search values,
excluding outer guard values. They are not relabelled as independently measured
physical ranges. The central persistent peat rate is fixed at 0.38 mm/yr, the
midpoint of the site-informed long-term 0.29--0.47 mm/yr interval. Peat-rate
sensitivity itself was handled separately in Stage51.

No criterion favors Integrated. Scenario rank is always an output.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd

import stage50_four_scenario_peat_sensitivity as m
from stage45_expanded_hydrology_nested import annual_hydro
from stage49_six_observation_irreversible_recruitment import irreversible_state, annual

OUT = Path('stage52_outputs')
OUT.mkdir(exist_ok=True)
PEAT_RATE = 0.38

# Admissible values from Stage45/49 after removing explicit outer guard values.
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
    ('V0', 1000.0, 'm3', 'calibrated effective geometry/storage parameter',
     'Reference surface-storage scale in the Stage49 hypsometric relation; not a measured bathymetric volume.'),
    ('p_shape', 18.0, 'dimensionless', 'calibrated geometry-shape parameter',
     'Controls curvature of the storage-area/depth-area power law; not taken directly from Hayashi & van der Kamp.'),
    ('tau_surf', 60.0, 'day', 'calibrated effective hydrologic timescale',
     'Linear surface-drainage/storage recession timescale; not a directly measured outlet residence time.'),
    ('local_frac', 0.45, 'fraction', 'calibrated effective routing fraction',
     'Fraction of upland soil-capacity excess routed to local perched fast/slow return reservoirs; not fraction of rainfall or island-wide recharge.'),
    ('tau_fast', 30.0, 'day', 'calibrated effective perched-return timescale',
     'Fast local-return reservoir recession time; conceptual effective parameter.'),
    ('k_gw_mm_d', 4.0, 'mm day-1', 'calibrated effective subsurface-loss flux',
     'Area-proportional loss from surface-water storage. This is NOT basalt hydraulic conductivity/Ksat.'),
    ('r_est_yr', 0.05, 'yr-1', 'calibrated ecological establishment/occupation rate',
     'Rate of bounded recruitment/occupation under qualifying continuous exposure; 1/r = 20 yr full-exposure timescale.'),
    ('hydro_window_d', 60, 'day', 'calibrated causal observation-window parameter',
     'Trailing window used to form the return-flow anomaly H; H has units m3.'),
    ('est_window_d', 7, 'day', 'process timing parameter within literature-bounded search',
     'Minimum continuous antecedent exposure window used to create recruitment pressure.'),
    ('peat_rate_persistent', 0.38, 'mm yr-1', 'site-informed long-term persistent-net reference',
     'Midpoint of the site-informed 0.29-0.47 mm/yr long-term interval; not selected by fit optimization.'),
    ('K_colonizable_integrated', 1835.7764495736299, 'm2', 'calibrated observation-operator area scale',
     'Maps dimensionless ecological occupation state S to open-water area effect; fitted to six observed years.'),
    ('K_hydro_integrated', 0.006134764828277183, 'm-1', 'calibrated observation-operator hydrologic scale',
     'Maps H (m3 trailing return-flow anomaly) to area (m2); units m2/m3 = m-1.'),
]


def geomorphic_loss(dt, V, rate_mm_yr, V0, p_shape):
    """Stage50 peat-surface translation using the perturbed V0/p_shape."""
    dt = pd.to_datetime(dt)
    V = np.asarray(V, float)
    V0 = float(V0); p = float(p_shape)
    h0 = V0 * (p + 2.0) / (m.A0 * p)
    ratio = np.maximum(V, 0.0) / V0
    h = h0 * np.power(ratio, p / (p + 2.0))
    A_hyd = np.where(V > 0, m.A0 * np.power(ratio, 2.0 / (p + 2.0)), 0.0)
    A_hyd = np.minimum(A_hyd, m.A_WET)
    elapsed = np.maximum((dt - pd.Timestamp('2011-01-01')).days.to_numpy() / 365.2425, 0.0)
    B = float(rate_mm_yr) / 1000.0 * elapsed
    hres = np.maximum(h - B, 0.0)
    Apeat = np.where(hres > 0, m.A0 * np.power(hres / h0, 2.0 / p), 0.0)
    Apeat = np.minimum(Apeat, m.A_WET)
    return np.maximum(A_hyd - Apeat, 0.0)


def states_for(P):
    hp = {k: P[k] for k in ['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']}
    F, _, _ = m.forcing()
    h = m.hydro(F, hp)
    exposed = np.clip((m.A0 - np.asarray(h['area'], float)) / m.A0, 0.0, 1.0)
    ew = int(P['est_window_d'])
    E = pd.Series(exposed).rolling(ew, min_periods=ew).min().fillna(0.0).to_numpy()
    state = irreversible_state(E, P['r_est_yr'])
    S = annual(h['dates'], state)
    H = annual_hydro(h['dates'], h['return_flow'], P['hydro_window_d'])
    Gd = geomorphic_loss(h['dates'], h['V'], PEAT_RATE, P['V0'], P['p_shape'])
    G = annual(h['dates'], Gd)
    corr = float(np.corrcoef(S, m.YEARS)[0,1]) if np.std(S) > 1e-12 else 1.0
    return h, S, H, G, corr


def predict_with_coeff(name, S, H, G, kc, kh):
    if name == 'Baseline Model':
        return m.A0 + kh * H
    if name == 'Hydrosere Only Model':
        return m.A0 - kc * S + kh * H
    if name == 'Eco-Geo Only Model':
        return m.A0 - G + kh * H
    if name == 'Integrated Model':
        return m.A0 - kc * S - G + kh * H
    raise KeyError(name)


def central_coefficients():
    h,S,H,G,corr = states_for(dict(m.P49))
    rows = m.fit_scenarios(S,H,G)
    return {name: {'Kc':float(kc), 'Kh':float(kh)} for name,kc,kh,*_ in rows}, (h,S,H,G,corr)


def rows_for_setting(parameter, value, central_coeff, mode):
    P = dict(m.P49); P[parameter] = value
    h,S,H,G,corr = states_for(P)
    if mode == 'fixed':
        scen = []
        for name, b in central_coeff.items():
            pred = predict_with_coeff(name,S,H,G,b['Kc'],b['Kh'])
            rm,nr = m.metric(pred)
            scen.append((name,b['Kc'],b['Kh'],pred,rm,nr))
    elif mode == 'profile_refit':
        scen = m.fit_scenarios(S,H,G)
    else:
        raise ValueError(mode)
    ordered = sorted(scen,key=lambda z:z[5])
    rank = {z[0]:i+1 for i,z in enumerate(ordered)}
    result=[]
    for name,kc,kh,pred,rm,nr in scen:
        result.append({
            'mode':mode,'parameter':parameter,'value':float(value),
            'is_selected_value': bool(abs(float(value)-float(m.P49[parameter])) < 1e-12),
            'Scenario':name,'RMSE_m2':float(rm),'nRMSE_pct':float(nr),'rank':int(rank[name]),
            'K_colonizable_m2':float(kc),'K_hydro_m_inv':float(kh),
            'state_year_corr':corr,
            'mass_error_m3':float(h['mass_error']),
            'area_partition_error_m2':float(h['area_partition_error']),
            'precip_partition_error_m3':float(h['precip_partition_error']),
            **{f'pred_{int(y)}':float(pred[i]) for i,y in enumerate(m.YEARS)},
        })
    return result


def main():
    central_coeff, central_state = central_coefficients()
    h0,S0,H0,G0,corr0 = central_state

    prov = pd.DataFrame(PROVENANCE,columns=['parameter','selected_value','unit','classification','interpretation'])
    prov['selected_at_edge_of_admissible_oat_values'] = prov['parameter'].map({
        k: bool(abs(float(m.P49[k])-min(v))<1e-12 or abs(float(m.P49[k])-max(v))<1e-12)
        for k,v in OAT.items()
    }).fillna(False)
    prov.to_csv(OUT/'stage52_parameter_provenance.csv',index=False)

    rows=[]
    for parameter, values in OAT.items():
        for value in values:
            rows.extend(rows_for_setting(parameter,value,central_coeff,'fixed'))
            rows.extend(rows_for_setting(parameter,value,central_coeff,'profile_refit'))
    df=pd.DataFrame(rows)
    df.to_csv(OUT/'stage52_oat_all.csv',index=False)
    df[df['mode']=='fixed'].to_csv(OUT/'stage52_oat_fixed_coefficients.csv',index=False)
    df[df['mode']=='profile_refit'].to_csv(OUT/'stage52_oat_profile_refit.csv',index=False)

    integ_fixed=df[(df['mode']=='fixed')&(df['Scenario']=='Integrated Model')]
    byp=[]
    for p in OAT:
        x=integ_fixed[integ_fixed['parameter']==p]
        # Compare Integrated against the actual within-setting rank; no imposed preference.
        byp.append({
            'parameter':p,
            'n_values':int(len(x)),
            'n_integrated_rank1':int((x['rank']==1).sum()),
            'integrated_rank1_all_values':bool((x['rank']==1).all()),
            'integrated_nrmse_min_pct':float(x['nRMSE_pct'].min()),
            'integrated_nrmse_max_pct':float(x['nRMSE_pct'].max()),
            'selected_value':float(m.P49[p]),
            'selected_at_edge_of_admissible_oat_values':bool(abs(float(m.P49[p])-min(OAT[p]))<1e-12 or abs(float(m.P49[p])-max(OAT[p]))<1e-12),
        })
    bdf=pd.DataFrame(byp)
    bdf.to_csv(OUT/'stage52_oat_integrated_rank_by_parameter.csv',index=False)

    # Central metrics from the locked 0.38 mm/yr configuration.
    central=[]
    for name,b in central_coeff.items():
        pred=predict_with_coeff(name,S0,H0,G0,b['Kc'],b['Kh'])
        rm,nr=m.metric(pred)
        central.append((name,rm,nr,b['Kc'],b['Kh']))
    central.sort(key=lambda z:z[2])

    summary={
        'status':'PASS_STAGE52_ANALYSIS',
        'observed_area_years':[int(y) for y in m.YEARS],
        'pond_area_observation_2022':'ABSENT',
        'persistent_peat_rate_mm_yr':PEAT_RATE,
        'sensitivity_primary':'fixed observation-operator coefficients; one process parameter changed at a time',
        'sensitivity_secondary':'profile-refit Kc/Kh; calibration diagnostic only',
        'oat_values_source':'Stage45/49 admissible calibration-search values after removing explicit outer guards; not independent measurement ranges',
        'central_metrics':[{'Scenario':n,'RMSE_m2':rm,'nRMSE_pct':nr,'K_colonizable_m2':kc,'K_hydro_m_inv':kh} for n,rm,nr,kc,kh in central],
        'fixed_oat_integrated_rank1_all_settings':bool((integ_fixed['rank']==1).all()),
        'fixed_oat_integrated_rank1_count':int((integ_fixed['rank']==1).sum()),
        'fixed_oat_setting_count':int(len(integ_fixed)),
        'fixed_oat_by_parameter':byp,
        'parameters_selected_at_edge_of_admissible_oat_values':[r['parameter'] for r in byp if r['selected_at_edge_of_admissible_oat_values']],
        'central_state_year_corr':corr0,
        'water_balance_central':{
            'max_mass_error_m3':float(h0['mass_error']),
            'max_area_partition_error_m2':float(h0['area_partition_error']),
            'max_precip_partition_error_m3':float(h0['precip_partition_error']),
        },
        'rank_was_not_an_acceptance_gate':True,
        'calibration_dimensionality_warning':'Six pond-area targets cannot independently identify all process and observation-operator parameters; parameters remain explicitly classified as calibrated unless independently constrained.',
    }
    (OUT/'stage52_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
