#!/usr/bin/env python3
"""Stage57 — metadata-aligned April-May four-scenario comparison.

Inputs locked before this stage
-------------------------------
- Stage56 selected process setting from successful run 33033703169.
- Observation support = April-May because all archived NGII airborne images are
  documented as April/May acquisitions. This was selected from metadata, not fit.
- Peat central estimate = 0.38 mm/yr from the Seoyeongari field Clymo analysis;
  0.29/0.47 mm/yr are the reported lower/upper long-term estimates.
- 2022 pond-area observation is absent.

This stage does not search hydrologic/ecological process parameters and does not
make scenario rank an acceptance criterion. It only fits the same constrained
observation-operator coefficients (Kc/Kh) for the four manuscript scenarios.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import stage50_four_scenario_peat_sensitivity as base
from stage31_topmodel_vsa import forcing, OBS
from stage35c_mass_balance_state_operator import A0, A_WET
from stage38_domain_corrected import hydro
from stage49_six_observation_irreversible_recruitment import irreversible_state
from eghm_strict_rules import EVAL_YEARS, MASS_TOL_M3, AREA_PARTITION_TOL_M2, PRECIP_PARTITION_TOL_M3

OUT = Path('stage57_outputs')
OUT.mkdir(exist_ok=True)
MONTHS = [4, 5]
YEARS = np.array(EVAL_YEARS, int)
Y = np.array([OBS[int(y)] for y in YEARS], float)

# Locked from Stage56 successful run 33033703169. Relative to Stage49, only the
# causal H aggregation window changed from 60 d to 14 d after April-May support
# was imposed from external image metadata.
P56 = {
    'V0': 1000.0,
    'p_shape': 18.0,
    'tau_surf': 60.0,
    'local_frac': 0.45,
    'tau_fast': 30.0,
    'k_gw_mm_d': 4.0,
    'r_est_yr': 0.05,
    'hydro_window_d': 14,
    'est_window_d': 7,
}

PRIMARY_PEAT_RATES = [0.29, 0.38, 0.47]
CENTRAL_PEAT_RATE = 0.38
RECENT_APPARENT_STRESS_RATES = [2.89, 5.91, 7.00]


def aggregate(dt, x):
    dt = pd.to_datetime(dt)
    yr = dt.year.to_numpy(); mo = dt.month.to_numpy()
    x = np.asarray(x, float)
    return np.array([
        float(np.mean(x[(yr == y) & np.isin(mo, MONTHS)]))
        for y in YEARS
    ])


def hydro_feature(dt, q, days):
    dt = pd.to_datetime(dt)
    yr = dt.year.to_numpy(); mo = dt.month.to_numpy()
    rr = pd.Series(np.asarray(q, float), index=dt).rolling(int(days), min_periods=1).sum().to_numpy()
    ref = float(np.mean(rr[(yr == 2011) & np.isin(mo, MONTHS)]))
    return np.array([
        float(np.mean(rr[(yr == y) & np.isin(mo, MONTHS)]) - ref)
        for y in YEARS
    ])


def peat_geomorphic_loss(dt, V, rate_mm_yr):
    dt = pd.to_datetime(dt)
    V = np.asarray(V, float)
    p = float(P56['p_shape']); V0 = float(P56['V0'])
    h0 = V0 * (p + 2.0) / (A0 * p)
    ratio = np.maximum(V, 0.0) / V0
    h = h0 * np.power(ratio, p / (p + 2.0))
    A_hyd = np.where(V > 0, A0 * np.power(ratio, 2.0 / (p + 2.0)), 0.0)
    A_hyd = np.minimum(A_hyd, A_WET)
    elapsed = np.maximum((dt - pd.Timestamp('2011-01-01')).days.to_numpy() / 365.2425, 0.0)
    B = float(rate_mm_yr) / 1000.0 * elapsed
    hres = np.maximum(h - B, 0.0)
    Apeat = np.where(hres > 0, A0 * np.power(hres / h0, 2.0 / p), 0.0)
    Apeat = np.minimum(Apeat, A_WET)
    return np.maximum(A_hyd - Apeat, 0.0), h0, B


def metric(pred):
    pred = np.asarray(pred, float)
    rm = float(np.sqrt(np.mean((pred - Y) ** 2)))
    return rm, 100.0 * rm / float(np.mean(Y))


def fit_scenarios(S, H, G):
    rows = []
    kh = base.fit_nonnegative(H, Y - A0)[0]
    pred = A0 + kh * H; rm, nr = metric(pred)
    rows.append(('Baseline Model', 0.0, float(kh), pred, rm, nr))

    X = np.c_[-S, H]
    b = base.fit_nonnegative(X, Y - A0, upper_kc=A0)
    pred = A0 + X @ b; rm, nr = metric(pred)
    rows.append(('Hydrosere Only Model', float(b[0]), float(b[1]), pred, rm, nr))

    geom_base = A0 - G
    kh = base.fit_nonnegative(H, Y - geom_base)[0]
    pred = geom_base + kh * H; rm, nr = metric(pred)
    rows.append(('Eco-Geo Only Model', 0.0, float(kh), pred, rm, nr))

    X = np.c_[-S, H]
    b = base.fit_nonnegative(X, Y - geom_base, upper_kc=A0)
    pred = geom_base + X @ b; rm, nr = metric(pred)
    rows.append(('Integrated Model', float(b[0]), float(b[1]), pred, rm, nr))
    return rows


def main():
    F, _, _ = forcing()
    hp = {k:P56[k] for k in ['V0','p_shape','tau_surf','local_frac','tau_fast','k_gw_mm_d']}
    h = hydro(F, hp)
    assert h['mass_error'] <= MASS_TOL_M3
    assert h['area_partition_error'] <= AREA_PARTITION_TOL_M2
    assert h['precip_partition_error'] <= PRECIP_PARTITION_TOL_M3

    exposed = np.clip((A0 - np.asarray(h['area'], float))/A0, 0.0, 1.0)
    ew = int(P56['est_window_d'])
    E = pd.Series(exposed).rolling(ew, min_periods=ew).min().fillna(0.0).to_numpy()
    state = irreversible_state(E, P56['r_est_yr'])
    S = aggregate(h['dates'], state)
    H = hydro_feature(h['dates'], h['return_flow'], P56['hydro_window_d'])

    all_rates = PRIMARY_PEAT_RATES + RECENT_APPARENT_STRESS_RATES
    rows=[]; geom=[]; predrows=[]
    for rate in all_rates:
        Gd,h0,B = peat_geomorphic_loss(h['dates'],h['V'],rate)
        G=aggregate(h['dates'],Gd)
        scen=fit_scenarios(S,H,G)
        ranks={z[0]:i+1 for i,z in enumerate(sorted(scen,key=lambda z:z[5]))}
        for name,kc,kh,pred,rm,nr in scen:
            rows.append({
                'peat_rate_mm_yr':float(rate),'Scenario':name,
                'RMSE_m2':float(rm),'nRMSE_pct':float(nr),'rank':int(ranks[name]),
                'K_colonizable_m2':float(kc),'K_hydro_m_inv':float(kh),
                **{f'pred_{int(y)}':float(pred[i]) for i,y in enumerate(YEARS)},
            })
            if np.isclose(rate,CENTRAL_PEAT_RATE):
                for i,y in enumerate(YEARS):
                    predrows.append({'Scenario':name,'year':int(y),'observed_m2':float(Y[i]),'predicted_m2':float(pred[i]),'error_m2':float(pred[i]-Y[i])})
        geom.append({
            'peat_rate_mm_yr':float(rate),'h0_reference_depth_m':float(h0),
            'peat_rise_2023_end_m':float(B[pd.to_datetime(h['dates']).year.to_numpy()==2023][-1]),
            'mean_geomorphic_loss_eval_m2':float(np.mean(G)),
            **{f'G_{int(y)}_m2':float(G[i]) for i,y in enumerate(YEARS)},
        })

    df=pd.DataFrame(rows); gd=pd.DataFrame(geom); pdp=pd.DataFrame(predrows)
    df.to_csv(OUT/'stage57_four_scenario_peat.csv',index=False)
    gd.to_csv(OUT/'stage57_geomorphic_translation.csv',index=False)
    pdp.to_csv(OUT/'stage57_central_predictions.csv',index=False)

    primary=df[df.peat_rate_mm_yr.isin(PRIMARY_PEAT_RATES)]
    central=df[np.isclose(df.peat_rate_mm_yr,CENTRAL_PEAT_RATE)].sort_values('nRMSE_pct')
    integ=primary[primary.Scenario=='Integrated Model'].sort_values('peat_rate_mm_yr')
    hydro_s=primary[primary.Scenario=='Hydrosere Only Model'].sort_values('peat_rate_mm_yr')
    summary={
        'status':'PASS_STAGE57_ANALYSIS',
        'observation_support':'April-May',
        'observation_support_basis':'NGII image metadata; not selected by pond-area fit',
        'observed_area_years':[int(y) for y in YEARS],
        'pond_area_observation_2022':'ABSENT',
        'stage56_process_parameters':P56,
        'central_peat_rate_mm_yr':CENTRAL_PEAT_RATE,
        'central_peat_rate_role':'field-derived Clymo-model central long-term estimate; not pond-area-fit selected',
        'primary_peat_lower_central_upper_mm_yr':PRIMARY_PEAT_RATES,
        'recent_apparent_stress_rates_mm_yr':RECENT_APPARENT_STRESS_RATES,
        'central_metrics':central[['Scenario','RMSE_m2','nRMSE_pct','rank','K_colonizable_m2','K_hydro_m_inv']].to_dict('records'),
        'integrated_rank1_all_primary_peat_rates':bool((integ['rank']==1).all()),
        'integrated_primary_nrmse_range_pct':[float(integ.nRMSE_pct.min()),float(integ.nRMSE_pct.max())],
        'hydrosere_primary_nrmse_pct':[float(x) for x in hydro_s.nRMSE_pct],
        'scenario_rank_not_acceptance_gate':True,
        'physical_closure':{
            'mass_error_m3':float(h['mass_error']),
            'area_partition_error_m2':float(h['area_partition_error']),
            'precip_partition_error_m3':float(h['precip_partition_error']),
        },
    }
    (OUT/'stage57_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
