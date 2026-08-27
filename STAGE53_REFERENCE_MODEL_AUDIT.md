# Stage53 reference and structural audit — 2026-08-27

## Decision

Do not add another fitted process term at this stage. The present model already contains more calibrated effective parameters than can be independently identified by six pond-area target years. Further structural tuning is more likely to increase equifinality than to add defensible process information.

The high-value next step is reference/provenance auditing, transparent classification of parameters, and low-cost structural checks without retuning toward a desired scenario ranking.

## Current data contract

- 2011: initial/reference open-water footprint only.
- Pond-area observations used: 2013, 2015, 2017, 2019, 2021, 2023.
- No 2022 pond-area observation exists in the current analysis.
- 2022 meteorology may remain in the continuous forcing series but no pond-area target, score, validation, holdout, or selection is attached to 2022.

## Audit by model component

| Component | Current implementation | Literature/provenance status | Audit judgement | Action |
|---|---|---|---|---|
| Daily water balance | Explicit precipitation, ET, return flow, surface drainage and area-proportional subsurface loss; exact daily conservation | Strong general process basis | STRONG | Keep |
| Spatial domain partition | Upland + wet non-open + open area partitioned exactly once | Conservation requirement, not fitted | STRONG | Keep |
| Depression geometry | Hayashi-type power-law A-V-h relation | Hayashi & van der Kamp (2000) supports this class of relationships, but not the fitted Seoyeongari values | MODERATE | Keep form; label V0 and p_shape calibrated effective geometry parameters |
| Catchment/wetland coupling | Upland excess feeds local fast/slow return reservoirs and wetland | Hayashi et al. (2016) supports integrated catchment–wetland and groundwater exchange concepts | STRONG FORM / WEAK SITE PARAMETERIZATION | Keep form; do not interpret local_frac or tau_fast as directly measured quantities |
| Jeju perched/local groundwater concept | Local subsurface return plus loss | Ahn et al. (2017) supports perched/local aquifers controlled by interbedded low-permeability layers on Jeju | MODERATE-STRONG CONCEPT | Keep; k_gw remains an effective flux, not Ksat |
| k_gw = 4 mm d-1 | Area-proportional surface-storage loss | Selected at admissible-support edge; no direct site measurement presently encoded | WEAKLY IDENTIFIED | Do not expand merely to improve fit. Seek site hydrogeologic constraint if available |
| Exposure-conditioned recruitment | Recruitment only after continuous exposure | Wetland plant literature strongly supports effects of inundation depth/duration/frequency/timing on establishment | STRONG FORM | Keep |
| est_window = 7 d | Minimum continuous antecedent exposure window | Literature supports multi-day recruitment windows, but 7 d is not a universal wetland constant | MODERATE | Keep as bounded/calibrated timing parameter, not literature-measured site constant |
| r_est = 0.05 yr-1 | Bounded occupation rate under qualifying exposure | Process form defensible; exact rate is calibrated | MODERATE/WEAKLY IDENTIFIED | Keep calibrated label |
| Flood-reversal coefficient | Removed | Earlier fits drove it to near-zero and implausibly long reversal time scales | STRONG DECISION | Do not restore without independent mortality/reflooding data |
| H return-flow anomaly | 60-d causal trailing return-flow anomaly | Antecedent hydrology is process-relevant, but the exact 60-d window is calibrated | MODERATE | Keep as causal hydrologic signature; label as observation-operator feature |
| K_hydro | Converts H (m3) to area effect (m2), units m-1 | Calibrated observation-operator scale; not a physical conductivity | EMPIRICAL BUT TRANSPARENT | Keep only with explicit wording that this is an effective observation operator |
| K_colonizable | Converts dimensionless occupation to area effect | Calibrated observation-operator area scale | EMPIRICAL BUT INTERPRETABLE | Keep; do not present as a biological rate |
| Peat effect | Peat/persistent surface rise reduces surface expression of open water through the same hypsometry; no water is destroyed | Biogeomorphic logic reasonable | MODERATE | Keep as scenario component |
| Persistent peat rate 0.29–0.47 mm yr-1, reference 0.38 | Site-informed long-term interval | Must distinguish preserved peat accumulation from actual surface-elevation change | IMPORTANT CAVEAT | Verify wording/provenance before final manuscript claim |
| Recent 2.89–7.00 mm yr-1 | Upper stress test only | Recent accumulation need not equal persistent elevation gain | APPROPRIATE AS STRESS TEST | Do not use as primary long-term geomorphic rate |

## Key literature

1. Hayashi, M. & van der Kamp, G. (2000). Simple equations to represent the volume–area–depth relations of shallow wetlands in small topographic depressions. Journal of Hydrology 237, 74–85. DOI: 10.1016/S0022-1694(00)00300-0.
2. Hayashi, M., van der Kamp, G. & Rosenberry, D.O. (2016). Hydrology of prairie wetlands: Understanding the integrated surface-water and groundwater processes. Wetlands 36(S2), 237–254. DOI: 10.1007/s13157-016-0797-9.
3. Webb, J.A., Wallis, E.M. & Stewardson, M.J. (2012). A systematic review of published evidence linking wetland plants to water regime components. Aquatic Botany 103, 1–14. DOI: 10.1016/j.aquabot.2012.06.003.
4. Casanova, M.T. & Brock, M.A. (2000). How do depth, duration and frequency of flooding influence the establishment of wetland plant communities? Plant Ecology 147, 237–250. DOI: 10.1023/A:1009875226637.
5. Nicol, J.M. & Ganf, G.G. (2000). Water regimes, seedling recruitment and establishment in three wetland plant species. Marine and Freshwater Research 51, 305–309. DOI: 10.1071/MF99147.
6. Ahn, U. et al. (2017). Proposal of new groundwater model through field observations in Jeju Island, Korea. Journal of the Geological Society of Korea 53, 347–360. DOI: 10.14770/jgsk.2017.53.2.347.
7. Cahoon, D.R. (2024). Measuring and interpreting the surface and shallow subsurface process influences on coastal wetland elevation: A review. Estuaries and Coasts 47, 1708–1734. DOI: 10.1007/s12237-024-01332-z. Critical point: vertical accretion is often not equal to net surface-elevation change because compaction, decomposition and root-zone processes contribute.
8. Beven, K. (2006). A manifesto for the equifinality thesis. Journal of Hydrology 320, 18–36. DOI: 10.1016/j.jhydrol.2005.07.007.
9. Efstratiadis, A. & Koutsoyiannis, D. (2010). One decade of multi-objective calibration approaches in hydrological modelling: a review. Hydrological Sciences Journal 55, 58–78. DOI: 10.1080/02626660903526292.
10. Her, Y. (2015). Impact of the numbers of observations and calibration parameters on equifinality, model performance, and output and parameter uncertainty. Hydrological Processes 29, 4220–4237. DOI: 10.1002/hyp.10487.

## Parameter identifiability warning

The Stage52 selected central setting lies on an edge of the admissible OAT support for 7 of 9 process axes:

- V0: minimum tested admissible value
- p_shape: maximum
- tau_surf: minimum
- local_frac: maximum
- tau_fast: minimum
- k_gw: maximum
- est_window: minimum

r_est and hydro_window are not at an admissible-support edge.

This does not invalidate the model because these OAT values are calibration-search support rather than independent uncertainty bounds. It does mean that expanding the grids solely to obtain a smaller RMSE is not scientifically justified. Independent process information should constrain these parameters before any further expansion.

## Scenario-comparison fairness

At the Stage51 0.38 mm yr-1 reference:

- Integrated: RMSE 29.861 m2; nRMSE 1.463%
- Hydrosere Only: RMSE 33.095 m2; nRMSE 1.621%
- Eco-Geo Only: RMSE 216.254 m2; nRMSE 10.595%
- Baseline: RMSE 222.418 m2; nRMSE 10.897%

Integrated and Hydrosere each fit the same two observation-operator coefficients (Kc and Kh), so their main comparison is not an unequal-parameter-count comparison. Baseline and Eco-Geo fit Kh only. A simple AICc check using n=6 and only these fitted observation-operator coefficients gives approximately:

- Integrated: 48.76
- Hydrosere: 49.99
- Eco-Geo: 67.52
- Baseline: 67.85

This is only a small-sample diagnostic and should not replace the process-based comparison, but it does not reverse the central ranking.

## Highest-value unresolved checks before freezing the model

### 1. Peat accumulation versus actual surface-elevation change — HIGH priority

Confirm what the 0.29–0.47 mm yr-1 site value physically represents. If it is an age-depth/preserved peat accumulation rate rather than measured surface-elevation change, the manuscript must not call it a directly measured annual surface-rise rate. The model can still use it as a persistent-net biogeomorphic sensitivity, but this distinction must be explicit.

### 2. Hypsometry — HIGH value only if independent topographic/bathymetric data exist

Hayashi & van der Kamp justify the power-law form, but V0=1000 m3 and p_shape=18 are effective calibrated values. Independent pond-floor elevations, RTK/UAV DSM, bathymetry, or sufficient elevation profiles would sharply improve identifiability. Do not claim such data are unavailable without checking the project files/archives.

### 3. Effective subsurface loss k_gw — MEDIUM priority

The form is plausible in a wetland with surface–subsurface exchange, and Jeju geology supports perched/local groundwater systems. The selected 4 mm d-1 is nevertheless a calibrated effective flux at the edge of the admissible support. It should remain explicitly distinguished from hydraulic conductivity. Independent water-level recession observations would be much more valuable than further grid expansion.

### 4. Recruitment timing — MEDIUM/LOW priority

The water-regime dependence is well supported. The exact 7-d threshold is not independently established for Seoyeongari. Treat it as a calibrated process-timing parameter. Adding species-specific germination/mortality parameters without species-level time-series data would worsen identifiability.

### 5. Observation operator — MEDIUM priority, reporting rather than structural

Kc and Kh are still calibrated mappings from mechanistic/ecological state variables to observed open-water area. Therefore describe the model as process-based/semi-mechanistic with calibrated observation operators, not as parameter-free or fully physically determined.

### 6. Sensitivity terminology — HIGH reporting priority

Stage52 OAT bounds are admissible calibration-search support, not independently measured uncertainty intervals. In the manuscript call this a parameter-perturbation/robustness analysis. Reserve stronger physical-uncertainty language for the independently motivated peat-rate interval or for parameters with external constraints.

## Freeze recommendation

Unless independent bathymetry/topography, repeated water-level recession measurements, or a direct surface-elevation series is found, freeze the present process structure after this audit. Further fitted terms or wider calibration grids are more likely to improve RMSE for the wrong reason than to improve the scientific model.
