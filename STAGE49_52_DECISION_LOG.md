# Stage49–52 decision log — 2026-08-27

## Data contract

- Pond-area observations used by the current analysis: 2013, 2015, 2017, 2019, 2021, 2023.
- 2011 is initial/reference only.
- There is no 2022 pond-area observation in the current analysis. 2022 meteorology may remain in continuous forcing, but no 2022 pond area is fitted, scored, held out, or used for selection.
- Leave-one-year-out and nested-CV model-selection stability are diagnostics only, not acceptance gates.

## Stage49 hydrology + ecology

Stage49 explicitly removed the fitted flood-reversal coefficient after earlier searches drove it to near-zero, century-to-millennial reversal time scales. Recruitment is instead bounded and conditional on causal continuous exposure.

Selected Stage49 parameters:

- V0 = 1000 m3 — calibrated effective storage/geometry scale, not measured bathymetric volume.
- p_shape = 18 — calibrated dimensionless hypsometric-shape parameter.
- tau_surf = 60 d — calibrated effective surface-storage/drainage time scale.
- local_frac = 0.45 — calibrated fraction of upland soil-capacity excess routed through local perched return reservoirs; not rainfall fraction or island-wide recharge.
- tau_fast = 30 d — calibrated fast local-return reservoir time scale.
- k_gw = 4 mm d-1 — calibrated area-proportional subsurface-loss flux; not hydraulic conductivity/Ksat.
- r_est = 0.05 yr-1 — calibrated establishment/occupation rate; 20-y full-exposure reciprocal time scale.
- hydro_window = 60 d.
- continuous-exposure window = 7 d.

Stage49 six-observation fit: RMSE 33.10 m2; nRMSE 1.622%. Physical closure errors are approximately 1e-12.

## Stage51 persistent peat interpretation

Recent apparent surface peat accumulation is not automatically interpreted as sustained topographic rise. Primary geomorphic sensitivity uses the site-informed long-term persistent-net interval 0.29–0.47 mm yr-1, with 0.38 mm yr-1 as the interval midpoint and reference value. The recent 2.89–7.00 mm yr-1 range is retained only as an upper stress test.

At 0.38 mm yr-1:

1. Integrated — RMSE 29.861 m2; nRMSE 1.463%.
2. Hydrosere Only — RMSE 33.095 m2; nRMSE 1.621%.
3. Eco-Geo Only — RMSE 216.254 m2; nRMSE 10.595%.
4. Baseline — RMSE 222.418 m2; nRMSE 10.897%.

Integrated is rank 1 across all three primary persistent-net peat rates 0.29, 0.38 and 0.47 mm yr-1. This rank is an output, not a gate or objective term.

## Stage52 OAT and provenance

Stage52 separates:

- fixed-coefficient OAT: central Kc/Kh locked; tests robustness of the locked model;
- profile-refit OAT: Kc/Kh refitted after each process perturbation; tests recalibration capability, not fixed-model robustness.

OAT values are the pre-existing Stage45/49 admissible calibration-search support after removing explicit outer guard values. They are not claimed to be independently measured uncertainty intervals.

The raw Stage52 table has 33 parameter/value rows, but the selected central setting is repeated once under each of nine parameter axes. Therefore robustness statements must use the 24 noncentral perturbations, not the raw 33 rows.

### Noncentral fixed-coefficient OAT

Integrated ranks first in 21/24 perturbations.

Three reversals:

- local_frac = 0.15: Hydrosere nRMSE 2.2709%, Integrated 2.2766%; difference 0.0057 percentage points and 0.117 m2 RMSE.
- tau_fast = 60 d: Hydrosere nRMSE 1.6645%, Integrated 1.6903%; difference 0.0258 percentage points and 0.527 m2 RMSE.
- r_est = 0.25 yr-1: fixed Kc from the r_est=0.05 central model becomes incompatible with the much faster ecological state; Integrated nRMSE 29.57%. This is a coefficient-state scaling/non-identifiability diagnostic rather than evidence that a fixed observation coefficient should be transferred unchanged between strongly different ecological rates.

### Noncentral profile-refit OAT

Integrated ranks first in 22/24 perturbations. The only reversals remain near-ties:

- local_frac = 0.15: Hydrosere 1.5085%, Integrated 1.5171%; difference 0.0085 percentage points.
- tau_fast = 60 d: Hydrosere 1.6567%, Integrated 1.6728%; difference 0.0161 percentage points.

At r_est = 0.25 yr-1, refitting Kc/Kh restores Integrated to rank 1 (nRMSE 1.918%), confirming strong r_est–Kc scaling dependence.

## Interpretation for manuscript sensitivity

Do not claim that Integrated wins at every value in the entire calibration-search support. The defensible statement is:

- Integrated has the lowest central error;
- Integrated remains rank 1 throughout the independently motivated persistent-net peat-rate range;
- under the broad internal calibration-search OAT, Integrated is top-ranked in 21/24 fixed noncentral settings and 22/24 profile-refit settings;
- the two persistent hydrologic rank reversals are numerically near-ties with Hydrosere, not large reversals;
- broad calibration-search values are stress tests and must not be presented as independently measured physical uncertainty ranges.

## Remaining caution

The six pond-area target years cannot independently identify all hydrologic, ecological and observation-operator parameters. Several selected hydrologic parameters lie at an edge of the admissible calibration-search support (though not at the explicit outer guard values). These parameters must remain labelled calibrated effective parameters unless independently constrained.
