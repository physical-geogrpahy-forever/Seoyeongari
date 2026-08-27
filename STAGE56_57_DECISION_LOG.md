# Stage56–57 decision log — metadata-aligned April–May model

Updated: 2026-08-27

## Why the central observation window changed

Archived manuscript/source metadata documents that the historical NGII orthorectified airborne images used to delineate pond area were acquired in **April or May**. The previous May–June aggregation therefore included a month outside the documented image-acquisition support.

Stage55 tested April, May, April–May, May–June and April–June without selecting a window by fit. Integrated ranked first under all five windows in both fixed-transfer and profile-refit tests. On that basis, April–May was adopted provisionally because of the external image metadata, not because its RMSE happened to be lower.

Exact year-specific acquisition dates retain methodological priority if recovered later.

## Stage56 — full April–May recalibration under unchanged Stage49 architecture

Stage56 reran the complete 87,480-candidate Stage49 calibration with only the observation-feature aggregation changed from May–June to April–May.

Unchanged:
- six pond-area targets: 2013, 2015, 2017, 2019, 2021, 2023;
- 2011 initial/reference only;
- 2022 pond-area observation absent;
- daily mass-conserved hydrology;
- parameter grids;
- grid-edge, closure, ecological and nRMSE gates;
- exposure-conditioned persistent occupation model;
- no flood-reversal coefficient;
- no LOOCV/nested-CV selection gate;
- no scenario-rank gate.

Successful workflow run: `33033703169`.

### Stage56 selected setting

- V0 = 1000 m3
- p_shape = 18
- tau_surf = 60 d
- local_frac = 0.45
- tau_fast = 30 d
- k_gw = 4 mm d-1
- r_est = 0.05 yr-1
- **hydro_window = 14 d**
- est_window = 7 d

Relative to Stage49, **the only process/feature setting that changed was hydro_window, from 60 d to 14 d**. All water-balance and ecological parameters were unchanged.

Stage56 hydro-ecology fit:
- RMSE = 32.361 m2
- nRMSE = 1.5855%
- K_colonizable = 1942.391 m2
- K_hydro = 0.102174 m-1
- state-year correlation = 0.98967
- physical closure errors ≈ 1e-12.

The unchanged hydrologic parameter selection after correcting temporal support is evidence that the core daily process setting is not an artifact of the May–June aggregation.

## Stage57 — four scenarios with field-derived peat central estimate

Stage57 used the locked Stage56 process setting and April–May support, then compared the four manuscript scenarios. The central geomorphic rate remains the independently field-derived Clymo-model long-term central estimate **0.38 mm yr-1**; 0.29 and 0.47 mm yr-1 remain the reported lower/upper long-term estimates.

Successful workflow run: `33033945847`.
Artifact: `stage57-aprmay-four-scenario-peat`, artifact ID `9631284807`, SHA256 `143d1880e61ab79f2dca268780c859e70b757b55f83986f5bd25625d4d9949d3`.

### Central 0.38 mm yr-1 results

| Scenario | RMSE (m2) | nRMSE (%) | Rank |
|---|---:|---:|---:|
| Integrated | **28.116** | **1.3775** | **1** |
| Hydrosere Only | 32.361 | 1.5855 | 2 |
| Eco-Geo Only | 215.821 | 10.5739 | 3 |
| Baseline | 222.418 | 10.8971 | 4 |

Central Integrated observation-operator coefficients:
- K_colonizable = 1885.215 m2
- K_hydro = 0.0923141 m-1.

### Primary peat-rate robustness

Across the site-derived 0.29 / 0.38 / 0.47 mm yr-1 long-term estimates:
- Integrated ranks first at every value;
- Integrated nRMSE range = **1.3612–1.3938%**;
- Hydrosere remains 1.5855% because the Hydrosere scenario does not contain the peat term.

The scenario ranking is an output, not an acceptance condition.

## Change in central manuscript result

The previous Stage51 May–June central result (Integrated nRMSE ≈ 1.463%) should now be treated as the earlier temporally misaligned analysis.

The current metadata-aligned central result is:

> **Integrated RMSE 28.116 m2; nRMSE 1.378%, using April–May observation support and a field-derived 0.38 mm yr-1 long-term peat accumulation central estimate.**

This replacement is justified by observation metadata, not by optimizing the aggregation window.

## Remaining checks before final freeze

1. Re-run Stage52-style process-parameter robustness around the Stage56 setting and April–May support.
2. Re-run hidden-constant robustness (effective soil store, FAST_FRAC, TAU_SLOW) using the Stage56/57 model, because hydro_window changed from 60 to 14 d.
3. Keep daily hydroperiod timing as an independent structural diagnostic.
4. Continue provenance search for the unresolved legacy AWC fraction 0.294.
5. Exact NGII acquisition dates, if recovered, override the provisional April–May averaging convention.
