# Stage72 — manuscript/model consistency audit

Date: 2026-08-27
Active code basis: deterministic Stage63/71 + Stage72 dependency audit

This document is a manuscript-revision specification. It does **not** change the accepted model.

## Executive finding

The current Round-1 manuscript still describes the legacy annual relaxation model, while the accepted deterministic code is a daily mass-conserved model with a materially different process graph.

The most important mismatch is conceptual rather than numerical:

- The manuscript presently states that hydrarch succession modifies evapotranspiration in the model. **The accepted code does not implement vegetation-to-ET feedback.**
- The manuscript presently states that peat accumulation modifies water-storage capacity. **The accepted code does not feed peat rise back into conserved storage.** Peat modifies modeled open-water surface expression after the common hydrologic solve.

Accordingly, the manuscript must either narrow those mechanism claims to the implemented model, or a new independently constrained feedback model must be developed and re-evaluated. The current Stage71 result must not be presented as evidence for feedbacks that are absent from the code.

## A. Observation definition

### Keep / clarify

Current R1 airborne-image wording is compatible with the active model:

- manual digitization of water-body boundaries;
- 0.5-m orthorectified airborne imagery;
- historical open-water pond surface area;
- images acquired in April or May.

### Change

- Active scored years are 2013, 2015, 2017, 2019, 2021 and 2023.
- 2011 is initialization/reference only and is not included in the six-observation error metric.
- There is no 2022 pond-area observation in the active analysis.
- Exact per-image acquisition dates have not been recovered in the current model archive. State that April 1-May 31 mean modeled process support is used as an approximation until exact dates are recovered; do not imply exact date matching.

Historical thesis language that defined the changing polygon more broadly using canopy/transition boundaries is provenance only and must not silently replace the active R1 water-body definition.

## B. Temporal resolution and state update

### Legacy manuscript text — remove

- daily forcing aggregated to annual totals for an annual state update;
- annual target storage/depth followed by response relaxation;
- calibrated annual response coefficient lambda = 0.035.

### Accepted model — replace with

The hydrologic model is evaluated at a **daily time step**. Water is carried explicitly in five conserved stores:

1. upland soil-water storage;
2. non-open wetland soil-water storage;
3. fast local-return reservoir;
4. slow local-return reservoir;
5. open-surface water storage.

There is no annual response relaxation, damping or fitted memory surrogate. `lambda = 0` by rule.

For each day,

`Storage(t+1) = Storage(t) + precipitation inputs - ET/evaporation - deep loss - surface drainage - subsurface loss`,

with all fluxes evaluated explicitly and daily closure required to be <= 1e-8 m3.

The accepted deterministic trajectory has closure errors at approximately 1e-12 scale.

## C. Spatial accounting and precipitation

### Legacy manuscript text — remove from the active model description

- fixed 17.5-m dynamic riparian buffer as the principal process footprint;
- NRCS-CN runoff as the active source of runoff into the pond;
- CN = 68 as an active calibrated/model flux parameter;
- 13% interception / effective pond precipitation factor 0.87 as an active pond-rain flux.

`eghm_deterministic_forcing.py` still computes legacy `pes` and `pp` arrays for historical compatibility, but Stage72 numerically proves that replacing both arrays with extreme values leaves the accepted hydraulic V and area bit-identical. They are not read by the current `hydro()` kernel.

### Accepted model — replace with

The modeled domain is partitioned daily into mutually exclusive footprints:

- potential wetland footprint: `A_WET = 5939.5 m2`;
- 2011 model geometry reference open-water footprint: `A0 = 2241.762 m2`;
- 2011 wetland margin: `A_WET - A0 = 3697.738 m2`;
- non-overlapping upland footprint: `8483 - 3697.738 = 4785.262 m2`;
- modeled component sum: `10724.762 m2`.

The small difference from the nominal raster-domain bookkeeping value is reported rather than tuned.

On each day raw precipitation depth is converted to volume separately over:

1. non-overlapping upland area;
2. wetland area not currently hydraulically open;
3. current hydraulic open-water area.

The three precipitation volumes must sum exactly to precipitation depth times the modeled component area within 1e-8 m3. This prevents the historical wetland-margin double counting.

## D. Meteorological forcing

The deterministic forcing retains the FAO-56/Penman meteorological calculations used to obtain daily terrestrial reference ET and open-water evaporation from AWS/ASOS data. The currently active hydrologic kernel reads:

- raw daily precipitation `pre`;
- daily reference terrestrial ET `eto`;
- daily Penman open-water evaporation `ep`.

It does **not** use legacy `pes` (CN runoff) or `pp` (0.87 precipitation) in the accepted water-balance recurrence.

## E. Storage-area geometry

### Legacy manuscript text — remove

- initial depth = 1.2 m as the active storage initialization;
- area-depth exponent alpha = 1.3;
- legacy `A(h)=Aref(h/hb)^alpha` as the active fitted geometry.

### Accepted model — replace with

The deterministic geometry is

`A(V) = A0 (V / V0)^[2/(p+2)]`,

with the accepted effective geometry parameters

- `V0 = 1000 m3`;
- `p = 18`;
- `A0 = 2241.762 m2`.

The implied reference depth scale is

`h0 = V0 (p+2) / (A0 p) = 0.4956418705960361 m`.

Equivalent forms are

`h(V) = h0 (V/V0)^[p/(p+2)]`

and

`A(h) = A0 (h/h0)^(2/p)`.

For p = 18 the area-volume exponent is 1/10 and the area-depth exponent is 1/9. The deterministic implementation evaluates these rational roots in a fixed IEEE-754 order for cross-platform reproducibility.

`V0` and `p` are calibrated **effective geometry parameters**, not measured bathymetry.

## F. Daily hydrologic process structure

Accepted fixed/process parameters:

- `tau_surf = 60 d`: surface drainage residence time;
- `local_frac = 0.45`: fraction of upland capacity excess routed to local return reservoirs;
- `FAST_FRAC = 0.75`: fast fraction of locally routed excess;
- `tau_fast = 30 d`;
- `tau_slow = 365 d`;
- `k_gw = 4 mm d-1`: area-proportional effective subsurface-loss flux, **not Ksat**;
- upland ET multiplier = 0.95;
- soil-water capacity depth term = `0.294 x 0.55 m` over the relevant soil footprint.

Upland soil excess is split into local return and deep loss. The local-return component is partitioned between fast and slow reservoirs and subsequently returns to the surface store.

The open surface receives:

- precipitation directly over the hydraulic open-water footprint;
- excess from the non-open wetland soil store;
- fast + slow local-return flow.

Open-surface losses are evaluated concurrently from the same pre-loss state:

- Penman open-water evaporation over the current hydraulic area;
- surface drainage `V/tau_surf`;
- effective subsurface loss `k_gw * A`.

If their combined potential loss exceeds available storage, all three losses are reduced proportionally. No arbitrary within-day priority is allowed.

## G. Hydrarch-succession / ecological state

### Legacy manuscript text — remove from the active-model description

- newly exposed ground becomes grass after one year and forest after five years as the implemented model state machine;
- succession modifies riparian/forest evapotranspiration in the accepted Stage71 water balance.

### Accepted model — replace with

The hydraulic open-water area first defines daily exposed fraction

`E(t) = clamp[(A0 - A_hyd(t))/A0, 0, 1]`.

Recruitment requires continuous antecedent exposure. The current exposure driver is the trailing 7-d minimum of `E(t)`, with pre-window values set to zero.

An irreversible establishment state is updated using

`survival(t+1) = survival(t) * [1 - (r_est/365) E7(t)]`

`S(t) = 1 - survival(t)`

with `r_est = 0.05 yr-1` and a 7-d continuous-exposure window.

There is no fitted flood-reversal coefficient in the accepted model. Earlier fitted reversal rates collapsed to biologically negligible century-to-millennial time scales and were removed.

**Critical interpretation:** `S` does not feed back to ET or to conserved water storage in Stage71. It enters the mapped open-water-area prediction through the colonization-area coefficient described below. Stage72 verifies that doubling `r_est` changes ecological state but leaves daily hydraulic V and hydraulic area bit-identical.

## H. Short-term hydrologic observation feature

Return flow from the fast + slow reservoirs is accumulated with a causal trailing 14-d sum. For each observed year the April-May mean trailing return flow is expressed as an anomaly from the corresponding 2011 April-May reference mean. This produces `H`.

`H` is therefore an antecedent hydrologic feature; no centered/future window or explicit year trend is used.

## I. Peat / geomorphic process

### Legacy manuscript text — remove

- constant 3 mm yr-1 as the central long-term peat-rise rate;
- bottom-relaxation coefficient = 0.08;
- empirical peat-elevation scaling factor = 0.70;
- statement that Stage71 peat rise directly reduces conserved water-storage capacity.

### Accepted model — replace with

The primary persistent-net peat-rise interval is **0.29-0.47 mm yr-1**, with **0.38 mm yr-1** as the reference value. Recent apparent rates of 2.89-7.00 mm yr-1 are retained only as upper stress tests and are not interpreted as sustained long-term topographic rise.

For prescribed cumulative peat rise `B(t)`, the daily deterministic translation is:

1. compute hydraulic area `A_hyd(V)` and equivalent depth `h(V)` from the shared conserved hydrologic trajectory;
2. set residual exposed-water depth `h_res = max[h(V) - B(t), 0]`;
3. compute `A_peat = A(h_res)`;
4. define geomorphic surface-expression loss `G(t) = max[A_hyd - A_peat, 0]`.

No water is removed from conserved storage by `G`.

**Critical interpretation:** this is a surface-expression geometry term, not a fully coupled peat-to-storage-capacity feedback. Stage72 verifies that peat rate changes `G` but does not change the shared conserved hydraulic `V` trajectory.

## J. Four scenario observation operators

For the six observed years, daily features are aggregated over April-May process support. With `S` = ecological establishment support, `H` = short-term return-flow anomaly, and `G` = peat surface-expression loss:

- Baseline: `A_pred = A0 + Kh H`
- Hydrosere Only: `A_pred = A0 - Kc S + Kh H`
- Eco-Geo Only: `A_pred = A0 - G + Kh H`
- Integrated: `A_pred = A0 - Kc S - G + Kh H`

Constraints:

- `Kc >= 0` and `Kc <= A0`;
- `Kh >= 0`;
- fits are evaluated deterministically at high precision.

`Kc` has units m2 and maps the dimensionless establishment state to colonized/non-open surface area. `Kh` has units m2 m-3 because `H` is based on a trailing sum of daily return-flow volume.

At the 0.38 mm yr-1 central peat rate, Integrated has:

- `Kc = 1877.5080938921935 m2`;
- `Kh = 0.08284997340969391 m2 m-3`.

These are calibrated observation-operator coefficients, not independently measured site constants.

## K. Calibration and evaluation text

### Legacy manuscript text — remove

- calibration of buffer width, lambda, alpha and bottom-relaxation as the current final parameterization;
- seven-observation performance including 2011;
- old composite-objective interpretation as the active final selection method;
- old scenario nRMSE values 1.64%, 1.27%, 1.22% and 1.06%.

### Accepted model — replace with

The active mapped-area target contains six years: 2013, 2015, 2017, 2019, 2021 and 2023. 2011 is used only for initialization/reference. 2022 is absent.

The accepted hydrologic/ecological structure is constrained by exact physical accounting, causal-process rules, ecological plausibility and an anti-time-surrogate guard. Remaining effective parameters are calibrated on the six historical target years and must be labelled calibrated rather than measured.

LOOCV and nested CV are small-sample diagnostics only and are not acceptance/ranking gates.

At the central persistent peat rate 0.38 mm yr-1, Stage71 reproduces:

| Rank | Scenario | RMSE (m2) | nRMSE (%) |
|---:|---|---:|---:|
| 1 | Integrated | 28.80618084 | 1.411325013 |
| 2 | Hydrosere Only | 32.38302382 | 1.586568236 |
| 3 | Eco-Geo Only | 215.50248761 | 10.558291390 |
| 4 | Baseline | 222.41834483 | 10.897125695 |

Scenario rank is an output, not an acceptance criterion.

## L. Results section corrections

Replace the legacy four-model performance paragraph with the Stage71 values above.

Do not state that all four models reproduce the declining trajectory comparably well: under the current deterministic operator, Baseline and Eco-Geo Only have approximately 10.6-10.9% nRMSE, whereas Hydrosere and Integrated are near 1.4-1.6%.

Any figure/table based on the legacy annual model must be regenerated from the Stage63/71 predictions before submission.

## M. Discussion corrections

### Statements that are defensible

- the Integrated observation model has the lowest central mapped-area error;
- hydrologically driven exposure can be linked causally to cumulative establishment state;
- persistent peat rise can alter the modeled surface expression of open water;
- the incremental peat contribution remains assessable through external peat-rate sensitivity;
- the result supports added explanatory value of including both ecological occupation and geomorphic surface expression under this model structure.

### Statements that are **not** defensible for Stage71

Do not say that the fitted comparison demonstrates that:

- woody succession increases modeled ET and thereby lowers water storage;
- peat rise reduces conserved storage capacity in the accepted numerical water balance;
- the model is fully two-way feedback coupled among ecology, geomorphology and hydrology;
- CN runoff or a 13% pond-rain interception coefficient controls the accepted hydro trajectory;
- `V == 0` reproduces observed visible-pool disappearance;
- the exact image date is represented when only April/May metadata are currently available.

A precise description is: **the model integrates a shared mass-conserved daily hydrologic trajectory with hydrologically driven ecological establishment and peat-controlled open-water surface expression in the mapped-area observation operator.** Coupling from hydrology to ecology is explicit; vegetation-to-hydrology and peat-to-conserved-storage feedbacks are not included in the accepted Stage71 kernel.

## N. Abstract / Introduction mechanism language

The present abstract/introduction should no longer say, as a statement about the implemented model, that peat accumulation “alters storage capacity” and hydrarch succession “alters evapotranspiration.” Those are literature-motivated candidate mechanisms, but they are not the numerical pathways evaluated by Stage71.

Suggested conceptual replacement:

> The model combines a physically closed daily water balance with two internal terrestrialization pathways: hydrologically conditioned vegetation establishment that reduces the surface area represented as open water, and persistent peat accretion that modifies the surface expression of open water relative to the conserved hydraulic state.

If the paper wishes to retain explicit vegetation-to-ET and peat-to-storage **feedback** claims, those processes must first be implemented, independently constrained and re-evaluated as a new model version.

## O. Limitations that should be added

1. Only six mapped pond-area target years are available, limiting independent parameter identifiability.
2. `V0`, `p`, `tau_surf`, `local_frac`, `tau_fast`, `k_gw`, `r_est`, `Kc` and `Kh` include calibrated/effective quantities; none should be relabelled as direct site measurements without independent data.
3. The peat process modifies modeled open-water surface expression but does not feed back into conserved storage in Stage71.
4. The ecological establishment state does not modify ET in Stage71.
5. Exact historical acquisition days are unresolved; April-May mean process support is used from metadata.
6. The mapping from hydraulic depth/storage to binary visible-pool presence is not independently constrained, so seasonal visible-pool disappearance is an external diagnostic rather than a fitted dry-day target.
7. The Stage67 head-dependent seepage experiment was rejected because it worsened mapped-area fit and did not improve spring concentration of hydraulic-zero timing.

## P. Recommended publication path

Given the present data, the defensible low-assumption path is to **rewrite the manuscript to match Stage71 rather than reintroduce poorly constrained feedback coefficients solely to preserve legacy wording**. A genuinely feedback-coupled future version would require independent constraints on vegetation-specific ET and basin microtopography/peat-driven storage geometry.

This recommendation follows the project rule that process plausibility and parameter identifiability outrank a preferred narrative or a lower RMSE.
