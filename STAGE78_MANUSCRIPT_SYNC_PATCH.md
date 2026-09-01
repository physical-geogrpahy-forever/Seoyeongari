# Stage78 manuscript synchronization patch

Updated: 2026-08-27

This is a documentation/manuscript synchronization record only. It does not change the accepted Stage78 scientific calculation.

## Fixed data contract

- observation variable: mapped open-water pond surface area
- scored years: 2013, 2015, 2017, 2019, 2021, 2023
- 2011: initialization/reference only
- 2022 pond-area observation: **ABSENT**
- process support for mapped-area comparison: April-May
- central field-derived peat rate: 0.38 mm yr-1
- primary peat sensitivity: 0.29 / 0.38 / 0.47 mm yr-1

## Important documentation corrections

### Hydrologic feature window

The executed `eghm_deterministic_kernel.py` uses `hydro_window_d = 14`. Therefore the antecedent hydrologic feature `H` must be described as a **causal trailing 14-d sum** of fast + slow local-return flow, summarized over April-May and expressed relative to the 2011 April-May reference mean.

A `60 d` hydrologic-window value recorded in the v7 handoff state is a metadata error. The separate surface-drainage residence time `tau_surf = 60 d` remains correct.

### Integrated exposure basis

Hydrosere Only accumulates exposure directly from hydraulic area:

`e = clamp[(A0 - A_hyd)/A0, 0, 1]`

`D += e/365`

`A_terr = beta_D D`, capped to `[0,A0]`.

Integrated uses the causal Stage77 coupled area-partition calculation. With previous terrestrialized area:

`f_peat = clamp[1 - A_terr(t-1)/A0, 0, 1]`

`G_eff = f_peat * G_wet`

`A_exposure = max(A_hyd - G_eff, 0)`

`e = clamp[(A0 - A_exposure)/A0, 0, 1]`

then `D` and `A_terr` are updated. Thus previous terrestrialization reduces the remaining wet peat-forming fraction, while residual peat surface expression contributes to the exposure basis used for subsequent terrestrialization. This is the retained eco-geomorphic area-partition feedback; it does not alter conserved hydraulic storage.

## Active Stage78 scenario operators

- Baseline: `A = A0 + Kh H`
- Hydrosere Only: `A = A0 - A_terr + Kh H`
- Eco-Geo Only: `A = A0 - G_wet + Kh H`
- Integrated: `A = A0 - A_terr - G_eff + Kh H`

The old ecological state `S`, `r_est`, `K_colonizable`/`Kc`, and fixed 1-y/5-y succession thresholds are not part of the Stage78 scenario calculation.

## Active hydrologic/geometry description

The accepted hydrology is a daily deterministic, mass-conserved five-store model. There is no annual response relaxation or fitted time-memory surrogate.

Spatial bookkeeping:

- potential wetland footprint = 5939.5 m2
- `A0` = 2241.762 m2
- wetland margin = 3697.738 m2
- external contributing area = 8483 m2
- non-overlapping upland = 4785.262 m2
- modeled component sum = 10724.762 m2

Storage-area geometry:

`A(V) = A0 (V/V0)^[2/(p+2)]`

with `V0 = 1000 m3`, `p = 18`, and implied `h0 = 0.4956418706 m`. `V0` and `p` are calibrated effective geometry parameters, not measured bathymetry.

Key hydrologic quantities include `tau_surf = 60 d`, local fraction 0.45, fast fraction 0.75, `tau_fast = 30 d`, `tau_slow = 365 d`, and `k_gw = 4 mm d-1`. `k_gw` is a lumped area-proportional effective subsurface-loss flux, not saturated hydraulic conductivity.

Stage78 maximum closure errors are approximately:

- mass: 1.82e-12 m3
- area partition: 1.82e-12 m2
- precipitation partition: 2.27e-13 m3

## Peat representation

The submitted 3 mm yr-1 central peat rate, bottom-relaxation coefficient 0.08, and empirical 0.70 peat-elevation scaling are not active in Stage78.

The active primary rate range is 0.29 / 0.38 / 0.47 mm yr-1, with 0.38 mm yr-1 retained as the field-derived central estimate rather than selected by pond-area error.

For prescribed cumulative peat rise `B`:

`h_res = max[h(V) - B, 0]`

`A_peat = A(h_res)`

`G_wet = max(A_hyd - A_peat, 0)`

No water is removed from conserved storage by `G_wet` or `G_eff`.

## Central Stage78 results

At 0.38 mm yr-1:

| Scenario | RMSE (m2) | nRMSE (%) | AICc | Rank |
|---|---:|---:|---:|---:|
| Integrated | 26.0258 | 1.27510 | 47.1090 | 1 |
| Hydrosere Only | 30.4121 | 1.49001 | 48.9781 | 2 |
| Eco-Geo Only | 215.5025 | 10.55829 | 67.4757 | 3 |
| Baseline | 222.4183 | 10.89713 | 67.8547 | 4 |

Central Integrated:

- `beta_D = 77 m2 exposure-year-1`
- `Kh = 0.0658704 m2 m-3`
- 2023 `D = 4.41024 exposure-yr`
- 2023 `A_terr = 339.588 m2`
- 2023 `f_peat = 0.848527`
- 2023 `G_eff = 3.13260 m2`

Hydrosere Only:

- `beta_D = 80 m2 exposure-year-1`
- `Kh = 0.07943285 m2 m-3`

## Peat sensitivity

Integrated remains rank 1 at every primary field-rate value:

- 0.29 mm yr-1: 1.29359% nRMSE
- 0.38 mm yr-1: 1.27510%
- 0.47 mm yr-1: 1.25746%

Hydrosere Only remains 1.49001%. The 0.38 case remains central because it is the field-derived central rate, not because the 0.47 case has the lowest fit error.

## Reviewer 2-2 diagnostics to replace the legacy endpoint analysis

Using the central Stage78 trajectories:

- Hydrosere RMSE = 30.4121 m2
- Integrated RMSE = 26.0258 m2
- relative in-sample RMSE reduction = **14.4231%**
- nRMSE difference = **0.214905 percentage points**
- delta AICc (Hydrosere - Integrated) = **1.86905**

With each scored observation omitted in turn **without refitting**, Integrated remains rank 1 in all six omissions, including omission of 2023. The old result in which removing 2023 reversed the ranking belongs to the superseded model and must not remain in the manuscript.

Nested LOOCV remains a small-sample diagnostic and is nearly tied:

- Integrated nRMSE = **2.00747%**
- Hydrosere Only nRMSE = **2.03504%**

Therefore the preferred wording is incremental explanatory support, not independent validation or universal superiority.

The Integrated advantage is also not a late-period effect: over 2021-2023 the Hydrosere RMSE is lower than the Integrated RMSE. Do not retain the legacy claim that 2021/2023 drive the Integrated improvement.

## Legacy items that must be removed or explicitly labelled superseded

- annual hydrologic update
- `lambda = 0.035`
- active `alpha = 1.3`
- active initial-depth geometry of 1.2 m
- bottom relaxation 0.08
- empirical peat-elevation scaling 0.70
- 3 mm yr-1 central peat rate
- CN=68 as an active Stage78 runoff control
- 13% pond interception / 0.87 effective rainfall as an active Stage78 flux
- 0.80 Penman multiplier as the active Stage78 open-water evaporation flux
- `S`, `r_est`, `Kc`/`K_colonizable`
- fixed 1-y bare-to-grass / 5-y woody transitions
- central vegetation-to-ET feedback claims
- peat-to-conserved-storage feedback claims
- old nRMSE 1.64 / 1.27 / 1.22 / 1.06%
- old R2-2 13.2% / 2023 endpoint-collapse result
- any scored 2022 pond-area observation

Legacy arrays may remain in compatibility code but are not active hydrologic controls.

## Required document synchronization

Apply these changes in place to the latest existing document bases:

- Main v11
- Supplement v9
- Figures v2_3
- Response draft v1

Do not reconstruct the final documents from older binaries solely because the latest binaries are temporarily unavailable.

### Main

Replace the legacy model-development/scenario/calibration/results/discussion mechanism text with the daily mass-conserved hydrology, cumulative exposure `D -> A_terr`, peat surface expression, and the Integrated area-partition feedback above. Define RMSE and `nRMSE = 100*RMSE/mean(observed)` with `n=6`.

### Supplement

Replace the active parameter/provenance table and obsolete sensitivity/endpoint tables. Retain the corrected mixed-effects soil-depth analysis already implemented in v9. Add cumulative-exposure process-form references and clearly label `beta_D` as site-calibrated.

### Figures

Fig. 10 must use the Stage78 six-observation trajectories and central legend:

- Baseline 10.90%
- Eco-Geo Only 10.56%
- Hydrosere Only 1.49%
- Integrated 1.28%

Show 2011 only as reference, not scored; do not plot a 2022 observation.

Fig. 2 should be redrawn around the five-store conserved hydrology plus `H`, `D -> A_terr`, `G_wet`, and Integrated `f_peat -> G_eff -> exposure` loop. Do not show central vegetation->ET or peat->storage arrows.

Fig. 9 legacy forest/grass/bare ET panels are not Stage78 scenario outputs and must be removed or redesigned rather than merely relabelled.

### Reviewer response

For R1-1/R2-1, state that further audit/reformulation removed the submitted empirical parameters rather than defending them. For R1-2, state that the 1-y/5-y threshold rule was removed and replaced by cumulative exposure. For R1-6, reserve feedback terminology for the implemented eco-geomorphic area-partition loop. For R2-2, use the new modest/diagnostic interpretation above. For R2-3, define nRMSE with six scored observations. Preserve the already corrected mixed-effects response for R2-5.
