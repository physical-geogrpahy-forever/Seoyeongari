# Stage94 fallback route decision log — 2026-08-27

## Role

This is a **frozen publication fallback route** for Seoyeongari. It is not the current TLMM primary route. It exists so that, if exact-TLMM transfer/coupling remains scientifically or numerically inadequate, the project can return immediately to a tested, reproducible, parsimonious semi-mechanistic model.

## Why Stage94 rather than raw Stage78

Stage78 achieved Integrated nRMSE 1.27510%, but its pond-area equation contained the fitted short-term term `+Kh H`. Stage94 deliberately removes that term entirely.

### Integrated Stage94 equation

`A_pred(t) = A0 - A_terr(t) - G_eff(t)`

with

`e(t) = clamp[(A0 - A_hyd(t))/A0, 0, 1]`

`D(t) = sum e(t) dt / 365`

`A_terr(t) = beta_D D(t)`

and the Stage77 causal peat-forming-area partition retained:

`f_peat(t) = clamp[1 - A_terr(t-1)/A0, 0, 1]`

`G_eff(t) = f_peat(t) G_wet(t)`

The central wet-peat accumulation rate remains 0.38 mm/yr and is not selected by pond-area fit.

**There is no `Kh`, no `Kh H`, and no additional pond-area observation correction in Stage94.**

## Central four-scenario performance

| Scenario | fitted parameters | nRMSE (%) | RMSE (m2) | AICc | rank |
|---|---:|---:|---:|---:|---:|
| Integrated Model | 1 | 1.28567 | 26.241 | 42.208 | 1 |
| Hydrosere Only Model | 1 | 1.50314 | 30.680 | 44.083 | 2 |
| Eco-Geo Only Model | 0 | 10.55829 | 215.502 | 64.476 | 3 |
| Baseline Model | 0 | 10.89713 | 222.418 | 64.855 | 4 |

Central Integrated beta_D = **76 m2 exposure-yr-1**.

Compared with Stage78 +KhH, removing the fitted short-term observation term changes Integrated nRMSE only from 1.27510% to **1.28567%**.

## Cross-validation and temporal validation

Nested leave-one-year-out validation, re-estimating only beta_D on the remaining years:

- RMSE = **32.454 m2**
- nRMSE = **1.59007%**

Fixed-origin temporal holdout is stricter: beta_D is fitted once using only the past block, then all later observations are predicted without updating the coefficient.

| calibration data | held-out future years | beta_D | holdout nRMSE |
|---|---|---:|---:|
| through 2017 | 2019, 2021, 2023 | 75 | 1.39978% |
| through 2019 | 2021, 2023 | 68 | 2.43813% |
| through 2021 | 2023 | 72 | 2.03607% |

The particularly useful stress test is calibration through 2017 (three historical pond observations, one fitted parameter) followed by fixed prediction of 2019, 2021 and 2023: **nRMSE 1.39978%**.

## Parameter stability

Full-series optimum beta_D = 76.

The full-series objective is relatively broad rather than needle-like:

- within +0.05 percentage points nRMSE: beta_D 74–78
- within +0.10 pp: beta_D 72–79
- within +0.25 pp: beta_D 70–81

LOOCV-selected beta values are mostly concentrated in the mid-70s, with 2019 the most influential held-out year. This must be disclosed rather than hidden.

## Woody succession contract

**A_terr is not synonymous with woody area.**

`A_terr = A_nonwoody_terrestrialized + A_woody`

New persistent terrestrialized area first belongs to a non-woody/herbaceous-transition cohort. A lagged subset may subsequently be diagnosed as woody-encroached. **A_woody is never subtracted from pond area a second time.** Therefore woody succession cannot improve Stage94 pond-area fit by double counting the same terrestrialized area.

Site evidence:

- tree ages: A1 10 yr, A2 12 yr, A3 27 yr, B1 8 yr, B2 11 yr, B3 29 yr;
- age-distance regression: `Age = 5.283 + 1.760 Distance`, r~0.957, R2~0.916, p~0.00272, n=6;
- A1, B1 and B2 locations were inside the mapped 2011 pond polygon;
- approximate establishment years are ~2015, ~2017 and ~2014.

Thus 3, 4 and 6 yr are used only as **upper-bound timing sensitivities from the last confirmed inside-pond state (2011) to estimated establishment**, not as measured exposure-to-tree-establishment lags. Exact first-exposure dates cannot yet be reconstructed because the current recovery package contains the 2011 and 2023 polygon geometries but not the intermediate 2013–2021 polygon geometries.

No woody lag is fitted to pond area and no lag changes the 1.286% central accuracy.

## What the model can and cannot claim

The observed-predicted level correlation across the six scored years is 0.963, and the observed vs predicted linear trend slopes are -27.31 and -25.94 m2/yr, respectively. The model therefore reproduces the **secular terrestrialization trajectory** well.

However, first differences between successive biennial observations are not reproduced well (difference correlation -0.510). The fallback must therefore be described as a model of persistent multi-year terrestrialization and pond-area decline, **not** as a high-fidelity reconstruction of every biennial hydrologic fluctuation. Exact acquisition dates are also unavailable beyond April/May.

## Evidence classes

- deterministic hydrology and mass closure: process-based implementation;
- peat rate 0.38 mm/yr: site/field-derived central value;
- cumulative exposure D: process-derived state;
- beta_D: empirical **longitudinal time-series-estimated** terrestrialization rate coefficient;
- woody age-distance and historical 2011-inside-polygon evidence: independent process validation, not used to fit beta_D;
- woody lag: sensitivity/diagnostic only, not a fitted pond-area parameter.

## Physical closure

- mass error: 1.819e-12 m3
- area partition error: 1.819e-12 m2
- precipitation partition error: 2.274e-13 m3

## Fallback gate

**PASS.** If the TLMM route is later rejected, Stage94 can be promoted as the manuscript model without returning to the Stage78 `+KhH` observation-correction term.

Remaining limitations that must stay visible:

1. six scored pond-area years only;
2. beta_D remains empirical, even though it is estimated from a longitudinal series rather than unrelated spatial samples;
3. intermediate historical polygon geometries are not currently available for exact tree exposure dating;
4. the route reproduces secular decline much better than biennial first differences.
