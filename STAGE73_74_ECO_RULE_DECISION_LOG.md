# Stage73–74 ecological-rule decision log — 2026-08-27

## Question

Can the opaque cumulative ecological state `S` be replaced by a simpler rule that has an explicit wetland-ecology literature basis and performs at least as well against the six mapped open-water-area observations?

## Fixed data/model contract

The comparison changed no hydrologic process parameter and no geomorphic parameter.

- observation variable: mapped open-water pond surface area
- observation support: April–May
- area observations: 2013, 2015, 2017, 2019, 2021, 2023
- 2011: initial/reference only
- 2022 pond-area observation: ABSENT
- persistent peat central estimate: 0.38 mm yr-1
- deterministic hydrology: unchanged
- exact physical closure: retained (~1e-12)
- accuracy ranking: result only, not an acceptance gate
- LOOCV: diagnostic only

## Literature basis for hydrologically conditioned vegetation response

The following sources support the *form* of using inundation/exposure duration and water-regime history as drivers of wetland plant establishment and recruitment. They do not directly prescribe the fitted Seoyeongari coefficient.

1. Casanova, M.T. & Brock, M.A. (2000). How do depth, duration and frequency of flooding influence the establishment of wetland plant communities? Plant Ecology 147:237–250. DOI 10.1023/A:1009875226637.
   - Experimental evidence that flooding depth, duration and frequency affect establishment and community composition; event duration is particularly informative.

2. Webb, J.A., Wallis, E.M. & Stewardson, M.J. (2012). A systematic review of published evidence linking wetland plants to water regime components. Aquatic Botany 103:1–14. DOI 10.1016/j.aquabot.2012.06.003.
   - Systematic review supporting causal effects of waterlogging/inundation depth, duration, frequency and timing on establishment, growth, reproduction and assemblage composition.

3. Ahn, C., Sparks, R.E. & White, D.C. (2004). Dynamic modeling of the response of wetland plants to hydrologic conditions. River Research and Applications 20:485–498. DOI 10.1002/rra.769.
   - Daily hydrologic vegetation modelling; reported field guidance around a ~70-d dry period and >85 d in the model for >=50% maximum moist-soil plant production. These values are analogues, not direct Seoyeongari thresholds.

4. Ahn, C., Moser, K.F., Sparks, R.E. & White, D.C. (2007). Developing a dynamic model to predict the recruitment and early survival of Black willow (Salix nigra) in response to different hydrologic conditions. Ecological Modelling 204:315–325. DOI 10.1016/j.ecolmodel.2007.01.006.
   - Recruitment/survival linked dynamically to hydrologic conditions and flood duration/timing.

5. Balke, T., Herman, P.M.J. & Bouma, T.J. (2014). Critical transitions in disturbance-driven ecosystems: identifying windows of opportunity for recovery. Journal of Ecology 102:700–708. DOI 10.1111/1365-2745.12241.
   - Establishment requires a disturbance-free window of opportunity; strongly supports hydrologic exposure history as an establishment constraint.

6. Hu et al. (2021). Geophysical Research Letters. DOI 10.1029/2021GL095596.
   - Mechanistic window-of-opportunity model separating an initial short inundation-free period (about 3 d in their implementation) from subsequent stability over several weeks (5–12 weeks tested; 8 weeks selected for their system). These values are ecosystem-specific and were used only to bound diagnostics.

## Stage73 rule families tested

### A. Continuous-exposure hazard (legacy-like comparator)

A first-order persistent establishment hazard after a minimum consecutive-exposure window.

Search support:
- exposure window: 3, 5, 7, 14, 21, 38, 45, 59, 70, 73, 85, 87 d
- rate: 0.025, 0.05, 0.10, 0.25 yr-1

Best:
- 3 d, 0.05 yr-1
- Integrated RMSE 28.209 m2
- Integrated nRMSE 1.3821%
- nested-LOOCV nRMSE 2.2928%

This already shows that the previous 7-d trigger was not uniquely required.

### B. Window-of-Opportunity persistent fraction

A fraction was permanently established after remaining continuously exposed for the full literature-bounded window (38–87 d).

Result:
- best nRMSE 4.7583%
- state saturated to 1.0 by the first evaluation year.

Interpretation: this strict aggregate rule discards too much temporal/spatial information under the present hydraulic exposure trajectory. It does not imply that the WoO literature is invalid; it means a binary permanent conversion after one uninterrupted long window is a poor reduced-order representation at this spatial scale.

### C. Dry-period maturation

Gradual maturation over 70 or 85 d of uninterrupted exposure, motivated by the Ahn moist-soil modelling benchmark.

Result:
- best nRMSE 4.7583%
- similarly saturated at the aggregate footprint scale.

Not recommended for the present reduced-order observation model.

### D. Hydroperiod/exposure hazard without an arbitrary consecutive-day threshold

Daily exposed fraction contributes directly to a first-order persistent establishment hazard.

Stage73 coarse best:
- rate 0.05 yr-1
- Integrated RMSE 28.033 m2
- nRMSE 1.37345%
- nested-LOOCV nRMSE 2.29211%

Stage74 dense rate profile:
- optimum rate 0.040 yr-1
- RMSE 27.5930 m2
- nRMSE 1.35189%
- K_colonizable 2090.999 m2
- K_hydro 0.0963801 m-1
- fixed-rate LOOCV nRMSE 1.86767%

The minimum at 0.040 was distinct on the 0.005 yr-1 search grid, although rates 0.035–0.060 remained within 0.05 percentage points of the optimum.

## Stage74 parsimonious rule: cumulative exposure dose

The simplest tested formulation removes both the arbitrary consecutive-day threshold and the fitted establishment-rate parameter.

Daily exposure fraction:

`e(t) = max[0, min(1, (A0 - Ahyd(t))/A0)]`

Cumulative exposure dose:

`D(t) = sum e(t) * dt / 365`

where `D` has units of exposure-years.

The ecological open-water-area effect is then represented directly as:

`A_eco(t) = beta_D * D(t)`

with `beta_D` in m2 per exposure-year.

Central fit with 0.38 mm yr-1 peat:

- beta_D = 77.6726993 m2 exposure-year-1
- K_hydro = 0.07254515 m-1
- RMSE = 26.0414224 m2
- nRMSE = 1.2758689%
- LOOCV nRMSE = 2.02804% (diagnostic only)
- relative small-sample AICc = 47.12

Exposure dose at evaluation dates:
- 2013: 0.8294 exposure-yr
- 2015: 1.6770
- 2017: 1.9106
- 2019: 3.0436
- 2021: 3.4510
- 2023: 4.3652

For comparison:
- accepted Stage71 old-S Integrated nRMSE ≈ 1.4113%
- optimized hydroperiod-hazard nRMSE = 1.3519%, AICc ≈ 57.81
- cumulative exposure dose nRMSE = 1.2759%, AICc ≈ 47.12

Thus the no-rate cumulative exposure rule is both more parsimonious and more accurate in the six-year fit than the old `S` formulation.

## Interpretation and terminology

`D` is **not vegetation cover**. It is a cumulative hydrologic exposure/recruitment dose with units of exposure-years.

`beta_D` is an effective site-calibrated ecological response coefficient with a transparent unit:

`m2 of persistent open-water-area loss per exposure-year`.

Literature supports the model form that cumulative duration/frequency of inundation or exposure controls wetland establishment and vegetation response. The exact assumption of linear response and the fitted value beta_D=77.67 are Seoyeongari model parameterization, not values taken from the cited studies.

A physically useful next interpretation is to define

`A_terr(t) = beta_D * D(t)`

as a modeled effective terrestrialized/established area (with an upper physical cap if required). This would eliminate both `S` and `K_colonizable` as separate quantities. However, using `A_terr` to alter evapotranspiration would upgrade the model from one-way ecological response to a true vegetation-to-hydrology feedback and therefore requires an independently defensible vegetation-specific ET contrast before implementation.

## Decision

1. Do not retain the old 7-d + r_est + K_colonizable formulation merely for continuity.
2. Use cumulative exposure dose `D` as the leading ecological-rule candidate because it is simpler, better fitting, and more directly tied to water-regime-duration literature.
3. Keep the optimized first-order hydroperiod hazard (r ≈ 0.04 yr-1) as an alternative sensitivity formulation because it gives the best fixed-rate LOOCV of the tested rules.
4. Do not use strict 38–87 d permanent WoO conversion in the reduced-order model; it saturates immediately under current hydraulic exposure.
5. Before closing the full ecohydrological feedback loop, independently constrain how modeled terrestrialized area changes ET; do not assume a forest ET multiplier merely to improve pond-area fit.
