# Stage91 — TLMM coupling verification

Date: 2026-08-27

## Status

`PASS_STAGE91_V2_SELF_CONTAINED_VERIFICATION`

The Stage91 diagnosis was rechecked from the official Stage85 CSV artifact rather than trusting the earlier diagnostic prose. The first Stage91 script was not self-contained because it imported `stage85_exact_tlmm_integrated`; `stage91_tlmm_coupling_forensics_v2.py` now reproduces the diagnosis from saved CSV outputs only and implements the audited TLMM recurrence and p=18 geometry directly.

## Verified Stage85 error decomposition

- Baseline nRMSE: **47.018194%**
- Hydrosere Only nRMSE: **51.030097%**
- Integrated nRMSE: **51.216849%**
- TLMM increment over direct Baseline: **+4.011903 percentage points**
- Peat increment over Hydrosere: **+0.186752 percentage points**

Therefore the catastrophic Stage85 error already exists before TLMM. TLMM amplifies it, but does not create the original ~47% failure.

## Verified 2015 attribution

- observed: **2147.678 m2**
- Stage85 direct Baseline: **2188.087202 m2**
- Stage85 Hydrosere: **1465.766001 m2**
- additional removal after TLMM coupling: **722.321201 m2**
- April-May days: **61**
- days exactly capped by the inherited MLL aquatic-zone area: **61/61**
- MLL used in 2015 April-May: **0.0108254075 m**
- corresponding `A(MLL)`: **1465.766001 m2**

The causal chain is verified:

`2013 September effective water level ≈ 9.51e-19 m -> MLL collapses for the following ecological state -> high 2014 water does not instantly remove TLMM hysteresis -> 2015 MLL cap remains only ~1466 m2`.

## s parameter check

- Hydrosere `s=15 yr`: **51.040461%**
- Hydrosere `s=30 yr`: **51.030097%**

Thus changing the woody succession time does not solve the Stage85 error. The mapped-open-water clipping is dominated by MLL rather than MUL.

## Independent structural controls

These are diagnostics only and are **not accepted final hydrology**.

Applying the same published TLMM recurrence and the same MLL planform clipping to alternative hydrologic trajectories gives:

- Stage88 `threshold_hard_raw`, September driver: **8.104010% nRMSE**
- Stage89 `subcap=729.6 m3`, April-May driver: **5.881988% nRMSE**

This proves that the published TLMM recurrence alone does not force a ~50% error. The Stage85 hydrologic collapse is the dominant upstream source of failure.

## Source-fidelity warning

Keddy & Campbell describe TLMM output as the elevation span between MLL and MUL. They explicitly note that this is not marsh area unless site-specific topography and bathymetry are supplied for the corresponding elevations. Stage85 instead maps MLL/MUL to planform area with the existing calibrated EGHM `p=18` hypsometry. That relationship is an effective hydrologic storage-area geometry, not independently measured Seoyeongari ecological microtopography.

The paper also used September mean water level for Lake Erie specifically to capture maximal exposed area during the summer growing season and maximum plant canopy. September is therefore an application choice, not a universal TLMM constant for every site.

## Decision

1. Do not fit `f`, `s`, `cmin`, or `wmin` to the six pond-area observations.
2. Correct the unsupported Stage85 direct pond-loss hydrology first.
3. Retain TLMM primarily in elevation-boundary space until an independently supported elevation-to-planform relation is available.
4. Treat `A(MLL)` clipping under `p=18` as a diagnostic coupling, not accepted site geometry.
5. Use 2015 as a regression test: a corrected coupling must not turn a near-correct ~2188 m2 direct state into ~1466 m2 solely because of inherited MLL hysteresis.
