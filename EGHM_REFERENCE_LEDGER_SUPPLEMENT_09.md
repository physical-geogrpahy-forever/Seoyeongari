# EGHM reference ledger supplement 09 — cumulative exposure and vegetation/peat feedback

Updated: 2026-08-27

This ledger records the references used to constrain Stage73–78 model-form decisions. It distinguishes evidence for **process form** from values that remain **Seoyeongari-calibrated**.

## A. Hydrologic exposure -> vegetation establishment / terrestrialization

### Casanova, M.T. & Brock, M.A. (2000)
**Title:** How do depth, duration and frequency of flooding influence the establishment of wetland plant communities?
**Journal:** Plant Ecology 147:237–250
**DOI:** 10.1023/A:1009875226637

**Use in EGHM:** Supports the model form that vegetation establishment depends on the duration/frequency/depth history of inundation and exposure, rather than on calendar time alone.

**Does not provide:** Seoyeongari `beta_D`.

### Webb, J.A., Wallis, E.M. & Stewardson, M.J. (2012)
**Title:** A systematic review of published evidence linking wetland plants to water regime components
**Journal:** Aquatic Botany 103:1–14
**DOI:** 10.1016/j.aquabot.2012.06.003

**Use in EGHM:** Systematic-review support for duration, frequency and timing of inundation/waterlogging as causal ecological drivers.

### Ahn, C., Sparks, R.E. & White, D.C. (2004)
**Title:** Dynamic modeling of the response of wetland plants to hydrologic conditions
**Journal:** River Research and Applications 20:485–498
**DOI:** 10.1002/rra.769

**Use in EGHM:** Supports daily hydrologic-history-based vegetation response. The reported dry-period benchmarks were tested only as analogues; they saturated at the present lumped spatial scale and were not adopted.

### Ahn, C., Moser, K.F., Sparks, R.E. & White, D.C. (2007)
**Title:** Developing a dynamic model to predict the recruitment and early survival of Black willow (Salix nigra) in response to different hydrologic conditions
**Journal:** Ecological Modelling 204:315–325
**DOI:** 10.1016/j.ecolmodel.2007.01.006

**Use in EGHM:** Supports recruitment/survival models driven dynamically by flood timing and duration.

### Balke, T., Herman, P.M.J. & Bouma, T.J. (2014)
**Title:** Critical transitions in disturbance-driven ecosystems: identifying windows of opportunity for recovery
**Journal:** Journal of Ecology 102:700–708
**DOI:** 10.1111/1365-2745.12241

**Use in EGHM:** Supports the general principle that establishment depends on disturbance-free/exposure history. A strict permanent-conversion WoO rule was tested but rejected for the current reduced-order spatial scale because it saturated immediately.

### Hu et al. (2021)
**Journal:** Geophysical Research Letters
**DOI:** 10.1029/2021GL095596

**Use in EGHM:** Mechanistic WoO support separating short initial inundation-free establishment from subsequent stability. The paper's ecosystem-specific durations are not transferred as Seoyeongari constants.

## B. Current preferred ecological rule

Daily fractional exposure:

`e(t) = clamp[(A0 - A_hyd(t))/A0, 0, 1]`

Cumulative exposure dose:

`D(t) = sum e(t) dt / 365`

Effective persistent terrestrialized area:

`A_terr(t) = beta_D D(t)`

The literature above supports the **functional dependence on cumulative water-regime history**. The linear reduced-order mapping and its coefficient are site parameterization.

Current Stage78 central Integrated value:

- `beta_D = 77 m2 exposure-year-1`

This value is **not a literature constant** and must be labelled site-calibrated.

## C. Vegetation -> evapotranspiration feedback

### Pereira, L.S., Paredes, P. & Espírito-Santo, D. (2024)
**Title:** Crop coefficients of natural wetlands and riparian vegetation to compute ecosystem evapotranspiration and the water balance
**Journal:** Irrigation Science 42:1171–1197
**DOI:** 10.1007/s00271-024-00923-9

**Use in EGHM:** Primary reference showing that `ETc = Kc ETo` is transferable to natural wetland/riparian vegetation, but Kc varies substantially with vegetation type, climate and water availability. Woody vegetation cannot be assigned a universally larger Kc than wetland herbaceous vegetation.

**Model implication:** Do not hard-code a positive vegetation-ET feedback solely because terrestrialization involves woody plants.

### Drexler, J.Z., Snyder, R.L., Spano, D. & Paw U, K.T. (2004)
**Title:** A review of models and micrometeorological methods used to estimate wetland evapotranspiration
**Journal:** Hydrological Processes
**DOI:** 10.1002/hyp.1462

**Use in EGHM:** Wetland ET is method- and ecosystem-dependent; no single universal method/coefficient is adequate.

### Kumagai, T. et al. (2014)
**Title:** Estimation of annual forest evapotranspiration from a coniferous plantation watershed in Japan (1): Water use components in Japanese cedar stands
**Journal:** Journal of Hydrology 508:66–76
**DOI:** 10.1016/j.jhydrol.2013.10.047

**Key reported values:** Total annual ET ≈ 911.4 mm yr-1 in a Cryptomeria japonica plantation, comprising upper-canopy transpiration ≈359.3, sub-canopy transpiration ≈126.9 and canopy interception ≈425.2 mm yr-1.

**Use in EGHM:** Strong evidence that mature Cryptomeria stands can have substantial ecosystem water use and interception. Relevant because Seoyeongari field/manuscript evidence identifies surrounding and encroaching Cryptomeria.

**Does not provide:** a transferable Seoyeongari Kc or proof that Cryptomeria ET exceeds the local pre-existing wetland vegetation ET under the same meteorological and water-table conditions.

### Shimizu, T. et al. (2015)
**Title:** Estimation of annual forest evapotranspiration from a coniferous plantation watershed in Japan (2): Comparison of eddy covariance, water budget and sap-flow plus interception loss
**Journal:** Journal of Hydrology 522:250–264
**DOI:** 10.1016/j.jhydrol.2014.12.021

**Key reported values:** corrected eddy-covariance ET about 840 and 812 mm in two years; 9-y mean water-budget P-Q ≈897.5 mm yr-1; component-sum ET ≈911.4 mm yr-1.

**Use in EGHM:** Independent-method support for the magnitude of Cryptomeria plantation water use.

### Hosoda et al. (2021)
**Journal:** Hydrological Processes
**DOI:** 10.1002/hyp.14111

**Use in EGHM:** Long paired-watershed evidence that clear-cutting reduced ET by about 100 mm yr-1 and that forest developmental state influences watershed ET. Also shows that forest ET response evolves over decades and cannot be represented safely by a single universal instantaneous multiplier.

## D. Site-specific vegetation evidence

Current manuscript/source archive documents:

- surrounding Seoyeongari landscape includes 30–40-year-old Cryptomeria japonica plantations and broad-leaved forest;
- the area was historically grassland before mid-20th-century afforestation;
- 2025 vegetation surveys identify a gradient from aquatic vegetation through terrestrial herbs/shrubs to trees;
- increment cores were collected from Cryptomeria stands adjacent to water bodies to test the spatial age gradient.

This supports the **occurrence and direction of woody encroachment**, but does not itself measure ET.

## E. Decision on vegetation-ET feedback

Stage75b literature-bounded tests found only a very small in-sample gain from allowing a terrestrialized-vegetation Kc different from the current wet-vegetation Kc, while nested LOOCV worsened and fold-selected Kc values were unstable.

Therefore:

- vegetation-ET feedback is biologically plausible;
- Cryptomeria-specific water-use literature strengthens plausibility;
- the sign/magnitude is not independently identified for Seoyeongari;
- retain vegetation-ET feedback as sensitivity/future process, not a central fitted feedback at Stage78.

## F. Terrestrialization -> peat-forming-area feedback

### Laiho, R. (2006)
**DOI:** 10.1016/j.soilbio.2006.02.017

**Use in EGHM:** Drainage/water-table lowering changes peat decomposition through increased oxygen availability.

### Philben et al. (2014)
**DOI:** 10.1002/2013JG002573

**Use in EGHM:** Oxygen exposure time is a strong control on peat decomposition.

### Morris, P.J., Belyea, L.R. & Baird, A.J. (2011)
**DOI:** 10.1111/j.1365-2745.2011.01842.x

**Use in EGHM:** General coupled peatland ecohydrological feedback theory.

### Site evidence
Aquatic-center cores show greater organic matter than terrestrial grassland/Cryptomeria peripheral cores, consistent with stronger drainage/decomposition in terrestrialized peripheral zones.

## G. Current Stage78 peat coupling

The site-derived local wet-peat vertical rate is not modified:

- central = 0.38 mm yr-1
- primary field range = 0.29 / 0.38 / 0.47 mm yr-1

Instead, terrestrialization modifies only the fraction of the original pond footprint continuing to express the wet peat-forming regime:

`f_peat(t) = clamp[1 - A_terr(t)/A0, 0, 1]`

`G_eff(t) = f_peat(t) G_wet(t)`

This is an **area-partition approximation**, not a measured linear decomposition law and not a claim that the local vertical accumulation rate equals `0.38 * f_peat`.

Stage78 central 2023:

- A_terr ≈339.59 m2
- f_peat ≈0.84853
- G_eff ≈3.133 m2

## H. Stage78 central model status

At field-central peat rate 0.38 mm yr-1:

- Integrated RMSE = 26.0258 m2
- Integrated nRMSE = 1.27510%
- Hydrosere Only nRMSE = 1.49001%
- Eco-Geo Only nRMSE = 10.55829%
- Baseline nRMSE = 10.89713%

Integrated remains rank 1 at all primary peat rates 0.29 / 0.38 / 0.47 mm yr-1. Ranking is an output, not a model-selection gate.
