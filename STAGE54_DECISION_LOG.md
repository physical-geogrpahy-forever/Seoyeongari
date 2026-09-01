# Stage54 decision log — inherited hidden constants and daily hydroperiod

Updated: 2026-08-27

## Purpose

Stage52 tested the explicit Stage49 calibration axes. Stage54 audited three quantities that were still inherited as fixed constants from Stage35c/38:

- effective external/wet-soil storage depth: `0.294 × 0.55 = 0.1617 m = 161.7 mm`;
- fast local-return fraction: `FAST_FRAC = 0.75`;
- slow local-return reservoir time scale: `TAU_SLOW = 365 d`.

No hidden constant was optimized in Stage54. Scenario rank and hydroperiod diagnostics were outputs only. The only acceptance checks remained the data contract (no 2022 pond-area observation) and exact physical closure.

## Tested values

### Effective active/root depth

The unresolved legacy available-water fraction `0.294 m3 m-3` was held fixed while active depth was perturbed:

- 0.42 m → effective storage 123.48 mm
- 0.55 m → effective storage 161.70 mm (current central assumption)
- 0.65 m → effective storage 191.10 mm

The 0.42 and 0.65 m values bracket the root-bearing subsoil interval documented in the Rural Development Administration representative Jungmun-series pedon: roots are common through the 42–65 cm Bw horizon and become sparse below approximately 65 cm. This makes 0.55 m physically plausible as an effective active depth, but **does not make it a measured Seoyeongari root depth**.

The exact origin of `0.294 m3 m-3` remains unresolved.

### Fast/slow routing

Pre-existing conceptual support from earlier model searches was used without expansion:

- `FAST_FRAC = 0.25, 0.50, 0.75`
- `TAU_SLOW = 180, 365, 730, 1460 d`

These are robustness values, not independently measured site uncertainty intervals.

## Central results

At the unchanged central configuration and site-derived Clymo central peat-rate estimate `0.38 mm yr-1`:

1. Integrated — RMSE 29.861 m2; nRMSE 1.463%
2. Hydrosere Only — RMSE 33.095 m2; nRMSE 1.621%
3. Eco-Geo Only — RMSE 216.254 m2; nRMSE 10.595%
4. Baseline — RMSE 222.418 m2; nRMSE 10.897%

Physical closure remained approximately `1e-12`.

## Hidden-constant robustness

There are seven noncentral settings.

Integrated ranked first in:

- **6/7 fixed-coefficient perturbations**;
- **6/7 profile-refit perturbations**.

### FAST_FRAC

All tested noncentral values preserved Integrated rank 1:

- 0.25: fixed nRMSE 1.677%; profile-refit 1.664%
- 0.50: fixed nRMSE 1.650%; profile-refit 1.639%

Conclusion: the present scenario conclusion is not materially dependent on fixing `FAST_FRAC=0.75` within the pre-existing conceptual support.

### TAU_SLOW

All tested noncentral values preserved Integrated rank 1:

- 180 d: fixed 1.616%; profile-refit 1.613%
- 730 d: fixed 1.497%; profile-refit 1.496%
- 1460 d: fixed 1.598%; profile-refit 1.596%

Conclusion: the present scenario conclusion is not materially dependent on `TAU_SLOW=365 d` within the pre-existing conceptual range.

### Effective active/root depth

- 0.65 m: Integrated remains rank 1 (fixed 1.550%; profile 1.531%).
- 0.42 m: **Hydrosere becomes rank 1**; Integrated becomes rank 2.

At 0.42 m:

fixed coefficients:
- Hydrosere nRMSE 1.653%
- Integrated nRMSE 1.842%

profile refit:
- Hydrosere nRMSE 1.593%
- Integrated nRMSE 1.830%

This reversal is larger than the near-ties seen for `local_frac` and `tau_fast` in Stage52 and therefore must not be hidden.

Interpretation:
- effective catchment soil storage is a meaningful structural uncertainty;
- the current 0.55-m active-depth assumption is plausible in the Jungmun pedon root-distribution context but is not independently measured at Seoyeongari;
- the exact `0.294` AWC fraction also remains unresolved;
- therefore the 161.7-mm store must remain an **effective inherited soil-storage assumption**, with the 123–191 mm diagnostic sensitivity reported transparently.

Do not recalibrate root depth to make Integrated win. Independent soil hydraulic information would be needed to narrow this uncertainty.

## Daily hydroperiod diagnostic

The central model, over 2012–2023, produces:

- mean zero-surface-storage days: 96.17 d yr-1
- median: 66 d yr-1
- mean March–April zero days: 19.67 d yr-1
- March–April share of all zero days: 20.45%
- maximum zero-storage days in one year: 238 d
- maximum continuous zero-storage run: 165 d

Central yearly pattern:

| Year | zero-storage days | Mar–Apr zero days | longest zero run |
|---:|---:|---:|---:|
| 2011 | 147 | 61 | 110 |
| 2012 | 67 | 4 | 60 |
| 2013 | 207 | 24 | 165 |
| 2014 | 74 | 15 | 70 |
| 2015 | 0 | 0 | 0 |
| 2016 | 0 | 0 | 0 |
| 2017 | 238 | 30 | 147 |
| 2018 | 65 | 0 | 58 |
| 2019 | 173 | 61 | 140 |
| 2020 | 30 | 22 | 30 |
| 2021 | 20 | 3 | 19 |
| 2022 | 218 | 42 | 83 |
| 2023 | 62 | 35 | 36 |

2022 remains forcing-only and is not an area-observation year.

### Hydroperiod judgement

This daily series is **not validated merely because the six pond-area observations fit well**.

The model shows a realistic ability to lose visible surface water and, in some years such as 2019, 2020 and 2023, substantial spring concentration. However:

- several years produce very long dry periods;
- 2015–2016 produce no zero-surface-storage days;
- aggregate March–April concentration is only about one fifth of all zero days.

Therefore daily hydroperiod realism remains a genuine independent diagnostic caution. It should not be converted into another fitted objective without quantitative, dated field observations.

## Decision

1. **Do not add another hydrologic process term.**
2. Keep `FAST_FRAC=0.75` and `TAU_SLOW=365 d` as transparently labelled conceptual central values; their tested legacy ranges do not change the main conclusion.
3. Keep the 161.7-mm soil store only as an effective central assumption, not a measured physical constant.
4. Report the 123.48–191.10 mm active-depth sensitivity; acknowledge the 0.42-m scenario rank reversal.
5. Continue searching for the exact source of `AWC=0.294` and any site/catchment soil hydraulic measurements.
6. Keep daily hydroperiod as an independent structural diagnostic rather than a fitting gate.
7. Next audit the **temporal support of the mapped pond-area observations**, because NGII imagery is an April/May snapshot whereas the current model comparison uses a May–June mean.
