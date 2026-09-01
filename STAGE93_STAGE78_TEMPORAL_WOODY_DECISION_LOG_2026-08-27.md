# Stage93 — Stage78 temporal validation and woody-succession state separation

Date: 2026-08-27

## Decision
Retain Stage78 as the preferred semi-mechanistic eco-geo-hydrological model. Do not replace its cumulative-exposure terrestrialization state with TLMM in the primary model.

## Exact Stage78 reproduction
Using the official Stage78 GitHub Actions artifact and the raw AWS/ASOS inputs, the central 0.38 mm/yr Integrated model reproduces:
- beta_D = 77 m2 per exposure-year
- K_hydro = 0.0658703951 m2 per m3
- RMSE = 26.0257722 m2
- nRMSE = 1.2751022%
- nested LOOCV nRMSE = 2.0074665%

## Strict temporal forward validation
Expanding-window, one-step-ahead validation refits beta_D and K_hydro using only earlier observations. The target observation is never used in parameter selection.

- train 2013/2015/2017 -> predict 2019: 1933.126 m2 vs 2045.159; error -112.033 m2
- train 2013/2015/2017/2019 -> predict 2021: 2002.392 m2 vs 1965.256; error +37.136 m2
- train 2013/2015/2017/2019/2021 -> predict 2023: 1919.415 m2 vs 1882.700; error +36.715 m2

Forward RMSE for 2019/2021/2023 = 71.364 m2; nRMSE = 3.63290%.
With at least four training observations (2021 and 2023 targets), forward RMSE = 36.926 m2; nRMSE = 1.91924%.

Interpretation: the first 2019 forecast is unstable because two fitted coefficients are estimated from only three earlier pond-area observations. Later expanding-window forecasts stabilize near the full-series parameter values and retain ~2% error.

## Woody succession: state separation, not double-counted area loss
A_terr is retained as total persistent terrestrialized area. It is NOT equated with woody vegetation.

Each positive increment in A_terr is treated as a terrestrialization cohort. Woody area is a lagged subset of those cohorts:
- A_woody,L(t) = A_terr(t-L)
- A_herbaceous/transition,L(t) = A_terr(t) - A_woody,L(t)

This woody partition does not enter the pond-area fitting equation and therefore cannot improve nRMSE by construction. It exists to represent succession state and to support independent ecological validation/possible ET sensitivity.

Site-primary chronology:
- A1, B1, B2 presently occur at locations inside the mapped 2011 pond polygon.
- estimated establishment years are approximately 2015, 2017, and 2014.
- therefore elapsed time from the known 2011 pond state to establishment is approximately 4, 6, and 3 years, respectively.
- exact first-exposure dates are unknown, so no exact establishment lag is claimed.

Primary site-informed lag sensitivity = 3, 4, 6 years; 5 years is a midpoint diagnostic only and is not fitted to pond area.

At April-May 2023, A_terr = 339.588 m2. Cohort partitions are:
- 3 yr lag: A_woody = 255.854 m2; transition/herbaceous = 83.734 m2
- 4 yr lag: A_woody = 236.058 m2; transition/herbaceous = 103.530 m2
- 5 yr diagnostic: A_woody = 204.593 m2; transition/herbaceous = 134.996 m2
- 6 yr lag: A_woody = 148.093 m2; transition/herbaceous = 191.496 m2

No 'mature forest in 5 years' claim is permitted. These states represent woody establishment/encroachment only.

## Peat and ET semantics
- Peat-forming fraction continues to depend on total persistent terrestrialized area, not only woody area, because field evidence distinguishes the wet aquatic center from both terrestrial-herbaceous and Cryptomeria-dominated peripheral conditions.
- Woody-specific ET feedback remains outside the central model. Earlier literature-bounded tests gave minimal in-sample improvement and poorer nested LOOCV. It may be retained as sensitivity only.

## Model characterization
The preferred model should be described as semi-mechanistic:
1. deterministic mass-conserved daily hydrology;
2. process-derived cumulative hydrologic exposure;
3. empirical time-series coefficient beta_D converting cumulative exposure to persistent terrestrialized area;
4. field-derived peat accumulation with terrestrialized-area feedback;
5. independently evaluated woody-encroachment chronology from tree rings and historical pond geometry.

Files:
- stage93_stage78_temporal_woody_validation.py
- stage93_outputs/stage93_summary.json
- stage93_outputs/stage93_forward_validation.csv
- stage93_outputs/stage93_woody_cohort_sensitivity.csv
- stage93_outputs/stage93_full_fit_predictions.csv
