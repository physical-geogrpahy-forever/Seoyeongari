# Seoyeongari EGHM — Stage65–71 decision log

Date: 2026-08-27
Branch: `chatgpt-stage30-20260826`

## 1. Active observation contract

The active Round-1 manuscript definition controls the current EGHM observation contract.

- Historical target variable: **mapped open-water pond surface area**.
- Source: manually interpreted/digitized water-body polygons from 0.5-m orthorectified airborne imagery.
- Active target years: **2013, 2015, 2017, 2019, 2021, 2023**.
- **2011 is initialization/reference only.**
- **There is no 2022 pond-area observation in the active analysis.** 2022 meteorology remains in the continuous forcing series only.
- Archived metadata currently establish acquisition in **April or May** but exact per-image acquisition days have not been recovered in the current model archive. Therefore the current April–May process-support mean is explicitly an approximation; no exact date is invented.

The historical undergraduate thesis used broader canopy/transition-boundary wording and reported a 2022 value. That wording/value are retained as provenance only and do not control the active Round-1 EGHM contract.

## 2. Three variables that must not be conflated

1. `mapped_open_water_pond_surface_area`: historical airborne-image target used for model-area comparison.
2. `daily_surface_storage_and_hydraulic_wetted_area`: conserved daily hydrologic model state.
3. `visible_surface_pool_presence_or_exposure`: seasonal hydroperiod observation/validation concept.

Numerical `V == 0` is **not** a definition of visible-pool absence. No arbitrary water-depth or area threshold may be fitted merely to reproduce a desired seasonal dry-day count.

## 3. Stage65–66 hydroperiod diagnosis

These stages diagnosed the timing and persistence of numerical hydraulic zero in the official deterministic model. Their outputs are retained as process diagnostics, not as direct validation of visible-pool disappearance.

The observed recurrent spring exposure/drying remains useful independent qualitative evidence, but a direct storage/depth-to-visible-pool observation operator is not independently constrained at present.

## 4. Stage67 head-dependent seepage — REJECTED

The tested head-dependent seepage structure is **not adopted**.

Reason:

- It reduced mean hydraulic-zero duration (approximately 100.1 to 45.5 d yr-1), but did not improve the seasonality of drying.
- The March–April share of hydraulic-zero days decreased (approximately 22.8% to 19.5%).
- A long 2013 late-year dry spell remained.
- Most importantly, the official Integrated pond-area fit degraded from approximately **1.411% to 2.636% nRMSE**.

Therefore this structure mainly changed the amount of numerical zero storage without producing a more defensible joint explanation of mapped pond area and seasonal hydroperiod.

## 5. Stage68 2024 forward diagnostic

Stage68 extended the frozen deterministic forcing through 2024 without refitting parameters and without using a 2024 mapped-area target or 2024 NDWI in computation.

Key result:

- annual precipitation: **1937.0 mm**
- numerical hydraulic-zero days (`V <= 1e-9`): **0**
- mean surface storage: **672.7466 m3**
- mean hydraulic wetted area: **2113.2442 m2**
- physical closure remains at machine precision (~1e-12 scale).

Interpretation: zero numerical hydraulic-zero days does **not** prove that a visibly expressed surface pool persisted all year.

## 6. Stage69 terminology audit — SUPERSEDED SEMANTICS

Stage69 correctly separated conserved hydraulic state from visible-pool expression, but its script described the active historical target as `mapped wetland extent`, following the older thesis wording.

That semantic label is superseded by Stage70/71. Stage69 remains an archived diagnostic stage; its active-target terminology must not be cited as the current observation definition.

## 7. Stage70 strict-rule correction

`eghm_strict_rules.py` now freezes:

- `EVAL_YEARS = (2013, 2015, 2017, 2019, 2021, 2023)`
- `OBS_MONTHS = (4, 5)`
- `OBSERVATION_VARIABLE = 'mapped_open_water_pond_surface_area'`
- `HYDRAULIC_STATE_VARIABLE = 'daily_surface_storage_and_hydraulic_wetted_area'`
- `HYDROPERIOD_VALIDATION_VARIABLE = 'visible_surface_pool_presence_or_exposure'`

LOOCV/nested CV remain diagnostics rather than acceptance gates. Full-six mapped-area nRMSE, physical closure, causal structure and anti-time-surrogate checks remain active constraints.

## 8. Stage71 observation-contract freeze — ACCEPTED

Workflow run: `33040002830`

Stage71 changes **no scientific process and no model parameter**. It verifies that the corrected observation semantics do not numerically move the official deterministic model.

Central peat rate: **0.38 mm yr-1**

| Rank | Scenario | RMSE (m2) | nRMSE (%) |
|---:|---|---:|---:|
| 1 | Integrated Model | 28.80618084 | **1.411325013** |
| 2 | Hydrosere Only Model | 32.38302382 | 1.586568236 |
| 3 | Eco-Geo Only Model | 215.50248761 | 10.558291390 |
| 4 | Baseline Model | 222.41834483 | 10.897125695 |

Integrated observation-operator coefficients in this central comparison:

- `K_colonizable = 1877.5080938921935 m2`
- `K_hydro = 0.08284997340969391 m2 m-3`

Reference geometry depth scale reported by the deterministic geometry: `h0 = 0.4956418705960361 m`.

The Stage63 Integrated nRMSE is reproduced **exactly** as `1.4113250129695185%`.

Historical deterministic fingerprints pass unchanged. 2024 remains a forward hydraulic diagnostic only; it is not a pond-area calibration/evaluation target.

Cross-runner result:

- Ubuntu 22.04 artifact ID: `9633480080`
- Ubuntu 24.04 artifact ID: `9633479917`
- The extracted `stage71_summary.json` is byte-for-byte identical across both runners.
- `stage71_summary.json` SHA-256: `0650f6bca0968511cec7a1afad4758a85cdba8f4b4a0c26f5d9b046d39575a4e`

## 9. Current accepted scientific state

The official model remains the deterministic Stage63/71 structure. Stage67 is rejected and must not replace it.

The current model may claim:

- physically closed daily hydrology;
- a deterministic, reproducible six-observation open-water pond-area comparison;
- Integrated lowest central error at the 0.38 mm yr-1 persistent-net peat reference rate;
- separate external/diagnostic treatment of seasonal visible-pool exposure.

The current model must **not** claim:

- that `V == 0` is identical to visually absent open water;
- that the model already independently validates exact spring dry-day duration;
- that exact historical acquisition dates are known when only April/May metadata have been recovered;
- that the old thesis canopy/transition-boundary definition or 2022 area value is part of the active Round-1 target set.

## 10. Next scientific constraints

Priority order:

1. Recover exact per-image historical acquisition dates if available in source-image metadata or an archived acquisition table. Until then retain April–May support and state the approximation explicitly.
2. If seasonal visible-pool timing is to become a quantitative validation target, independently constrain the mapping from conserved hydraulic state to visible surface expression using site microtopography, water-level observations, or image-linked geometry. Do not fit an arbitrary threshold to the desired 71–73 d disappearance count.
3. Update the manuscript model-development section, which still contains legacy annual-relaxation equations/coefficients, to the accepted deterministic Stage63/71 daily mass-conserved formulation before submission.
