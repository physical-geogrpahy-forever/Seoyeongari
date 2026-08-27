# Stage96 process-only TLMM checkpoint — 2026-08-28

## Binding rules
- No calendar year / secular trend / relaxation-to-observation / area correction.
- Same meteorological forcing and process structure are used for all four scenarios.
- TLMM central parameters remain source-locked: f=4 yr, s=30 yr, cmin=0.01, wmin=0.001.
- Peat central rate = 0.38 mm/yr.
- Model ranking is an output, never a constraint.
- Every structural change must report Baseline / Hydrosere / Eco-Geo / Integrated together.

## Stage96 hydrology/ecology structure
- Shallow wetland storage with microtopographic elevation distribution.
- Daily precipitation, Penman open-water evaporation, FAO-type wetland ET.
- Nonlinear lateral drainage decreases strongly as the water table falls.
- Exact annual TLMM state transitions.
- Site temporal adapter: minimum monthly mean water level among March–May, representing sustained maximum growing-season exposure.
- TLMM vegetation classes feed back to subsequent daily ET.
- Peat is a prescribed one-way geomorphic forcing, not a fitted time trend.
- Daily whole-system mass closure remains ~1e-12 m3.

## Central f=4 four-scenario result
Baseline: nRMSE 9.86295%
Hydrosere (exact TLMM + vegetation ET feedback): 4.00347%
Eco-Geo (peat only): 9.85209%
Integrated (TLMM + peat + vegetation ET feedback): 3.97129%

Thus exact TLMM supplies most of the additional predictive skill relative to hydrology-only; peat supplies a small further improvement. Integrated ranks first without a ranking constraint.

## Published/reference sensitivity
f=5 yr sensitivity (not central):
Baseline 9.86295%
Hydrosere 3.47850%
Eco-Geo 9.85209%
Integrated 3.47702%

f=5 is not selected by pond-area fit; retain only as a reference-supported sensitivity unless stronger site-specific justification is obtained.

## Driver diagnostics
At f=4:
- March–May minimum monthly mean: Integrated 3.97129%
- 30-day minimum mean: Integrated 4.10805%
- March–May 25th percentile: 4.65618%
- March–May 10th percentile: 5.17180%
- March–May overall mean: 8.03207%

Therefore extreme low-water statistics are not adopted to improve fit.

## Remaining failure
The model still fails the recurrent spring surface-drying constraint:
- March–April hydraulic/effective open-water area remains large.
- Parameter changes to q0, specific yield, local return fraction, and fast-return time do not create the observed spring phase without strongly degrading area accuracy.
- This is a structural/seasonal-phase problem, not a simple coefficient problem.

## Current status
Stage96 is a process-only checkpoint, not final success.
Next work should target the missing seasonal storage/drainage mechanism while preserving:
1. process-only formulation,
2. exact mass closure,
3. four-scenario comparison at every iteration,
4. central TLMM source lock.
