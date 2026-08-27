# Seoyeongari Stage84 — TLMM exact-process audit

## Decision
Stage84 keeps the published Twin Limit Marsh Model biological process literal at each specified elevation. It does **not** replace TLMM with an EGHM score, logistic transition, or fitted succession threshold.

## Published TLMM process locked in code
- Lower limit: continuous flooded duration `dt` at a specified elevation; `f=4 yr` central published temperate interim value; `cmin=0.01`; marsh remaining is the published scaled exponential response.
- Upper limit: dewatered duration `xt` at a specified elevation; `s=30 yr` central published temperate interim value; `wmin=0.001`; marsh remaining is the published scaled exponential response.
- Newly exposed sediment: marsh colonization within one annual growing-season step.
- Woody reset: a flood pulse lasting at least one growing season removes woody canopy in the published simple model; marsh re-establishes after dewatering.
- Annual water-level support: September mean is retained because it is the authors' worked-example choice for Lake Erie/Ontario, intended to capture maximum summer exposure/germination conditions.

## What is EGHM coupling, not TLMM biology
The paper explicitly says its `MUL-MLL` result is an elevation expanse rather than actual marsh area because site topography/bathymetry were not included. Stage84 therefore applies the published TLMM state at many specified elevations and uses accepted Seoyeongari hypsometry only as area weights. This is a site-specific geometric integration, not a new succession rule.

Likewise, class-specific ET feedback, peat coupling, the observation operator, and the complementary woody-area bookkeeping are EGHM coupling layers. They are not described as TLMM parameters.

## Critical result of the audit
The Stage83 elevation-band idea itself is not a replacement biological model: it is a numerical discretization of TLMM's own `dt`/`xt` calculation at specified elevations. Stage84 makes this distinction explicit and adds scalar-vs-vector recurrence tests plus MLL/MUL diagnostics.

## Raw meteorology contract
Only the two observed raw files are canonical inputs:
1. `OBS_AWS_DD_20250930013603.csv`
2. `OBS_ASOS_DD_20250930041037.csv`

`daily_forcing_v5_equations.csv` remains a derived reproducibility product, not a raw input and not an execution gate.

## Current execution status
Synthetic TLMM source-fidelity tests and mass-balance smoke tests run in the current runtime. Real 2011–2023 evaluation remains gated only because the current runtime does not contain the raw AWS/ASOS bytes (or a parent archive byte stream that can be extracted). Library/archive existence is not disputed.
