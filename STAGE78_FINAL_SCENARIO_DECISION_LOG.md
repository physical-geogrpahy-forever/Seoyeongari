# Stage78 final cumulative-exposure scenario decision log — 2026-08-27

## Purpose

Rebuild the four manuscript scenarios after replacing the abstract ecological state `S` with cumulative hydrologic exposure dose `D`, while carrying forward the Stage77 terrestrialization-dependent peat-forming-area coupling.

## Fixed contract

- observation variable: mapped open-water pond surface area
- observation support: April–May
- observed years: 2013, 2015, 2017, 2019, 2021, 2023
- 2011: initial/reference only
- 2022 pond-area observation: ABSENT
- deterministic conserved hydrology: unchanged
- primary field-derived persistent wet-peat rates: 0.29 / 0.38 / 0.47 mm yr-1
- central field-derived peat rate: 0.38 mm yr-1
- scenario rank: output only
- nested LOOCV: diagnostic only
- physical closure retained at ~1e-12

## Ecological memory

The former `S`, `r_est` and `K_colonizable` formulation is not used.

Daily hydrologic exposure fraction is

`e(t) = clamp[(A0 - A_hyd(t))/A0, 0, 1]`

and cumulative exposure dose is

`D(t) = Σ e(t) Δt / 365`

with units of exposure-years.

Persistent terrestrialized area is

`A_terr(t) = beta_D D(t)`

subject to the physical cap `0 <= A_terr <= A0`.

`beta_D` therefore has a transparent unit of m2 per exposure-year and replaces the opaque combination of `S` and `K_colonizable`.

## Scenario definitions

### Baseline
`A = A0 + Kh H`

### Hydrosere Only
`A = A0 - A_terr + Kh H`

### Eco-Geo Only
`A = A0 - G_wet + Kh H`

### Integrated
`A = A0 - A_terr - G_eff + Kh H`

For Integrated, previous terrestrialization reduces the basin fraction that continues to express the local wet-peat geomorphic contribution:

`f_peat = clamp(1 - A_terr/A0, 0, 1)`

`G_eff = f_peat G_wet`

The local wet-peat vertical rate itself remains the independently field-derived 0.38 mm yr-1 central value; no decomposition-rate coefficient is fitted.

## Successful workflow

Workflow run: `33044023254`

Both Ubuntu 22.04 and Ubuntu 24.04 jobs passed after correction of a CSV schema-only output bug. The bug did not affect scientific calculations; scenario-specific diagnostic columns were heterogeneous and the CSV writer had initially assumed the Baseline row contained the complete schema.

## Central 0.38 mm yr-1 results

| Scenario | RMSE (m2) | nRMSE (%) | AICc | Rank |
|---|---:|---:|---:|---:|
| Integrated | **26.0258** | **1.27510** | **47.1090** | **1** |
| Hydrosere Only | 30.4121 | 1.49001 | 48.9781 | 2 |
| Eco-Geo Only | 215.5025 | 10.55829 | 67.4757 | 3 |
| Baseline | 222.4183 | 10.89713 | 67.8547 | 4 |

Central Integrated quantities:

- `beta_D = 77 m2 exposure-year-1`
- `Kh = 0.0658704 m2 m-3`
- 2023 cumulative exposure dose `D = 4.41024 exposure-yr`
- 2023 effective terrestrialized area `A_terr = 339.588 m2`
- 2023 peat-forming fraction `f_peat = 0.848527`
- 2023 effective peat surface-expression loss `G_eff = 3.13260 m2`

Hydrosere-only central fit:

- `beta_D = 80 m2 exposure-year-1`
- nRMSE = 1.49001%

## Nested LOOCV at central peat rate

Diagnostic only:

- Integrated: RMSE 40.9739 m2; nRMSE **2.00747%**
- Hydrosere Only: RMSE 41.5367 m2; nRMSE **2.03504%**
- Eco-Geo Only: nRMSE 10.55829%
- Baseline: nRMSE 10.89713%

Thus Integrated remains marginally ahead of Hydrosere in the nested diagnostic, although the small n=6 dataset requires restrained interpretation.

## Primary peat sensitivity

Integrated ranks first at every independently defined field-rate value:

- 0.29 mm yr-1: Integrated nRMSE 1.29359%
- 0.38 mm yr-1: Integrated nRMSE 1.27510%
- 0.47 mm yr-1: Integrated nRMSE 1.25746%

Hydrosere Only remains 1.49001% because it contains no peat process.

The central value remains 0.38 mm yr-1 because it is the field-derived central estimate, not because the 0.47 case has the smallest pond-area error.

## ET feedback status

Vegetation-to-hydrology ET feedback is NOT included in the central Stage78 model.

Reason:

1. Site evidence supports progressive woody/Cryptomeria encroachment, so such a feedback is ecologically plausible.
2. Existing Stage75b tests using literature-bounded vegetation crop coefficients showed only a tiny in-sample gain relative to the no-ET-feedback anchor, while nested LOOCV became worse and the preferred coefficient varied by held-out year.
3. Wetland/riparian ET literature shows overlapping vegetation coefficients and strong dependence on water availability; woody vegetation cannot be assumed universally to have greater ET than the pre-existing wetland vegetation.
4. Japanese Cryptomeria plantation measurements demonstrate substantial forest water use (e.g. ~911 mm yr-1 total ET in Kumagai et al. 2014), but transferring that absolute ET directly to Seoyeongari would not independently determine a site crop coefficient.

Therefore vegetation-ET feedback remains a sensitivity/future independently constrained process rather than a fitted central mechanism.

## Final interpretation

The preferred current model is a deterministic, mass-conserved hydrologic model coupled to:

1. cumulative hydrologic exposure -> persistent terrestrialized area;
2. terrestrialized area -> reduced peat-forming-area fraction;
3. persistent field-derived peat accumulation over the remaining wet peat-forming fraction -> altered open-water surface expression.

This is a genuine eco-geomorphic feedback because terrestrialization modifies the spatial extent of the geomorphic process and the resulting surface expression modifies subsequent exposure. It is not yet a fully vegetation-ET-hydrology feedback model.
