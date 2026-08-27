# EGHM strict model rules

These rules are non-negotiable. A lower RMSE never overrides a failed physical or ecological rule.

1. **Exact daily water balance**: maximum daily closure error must be <= 1e-8 m3.
2. **lambda = 0**: no memory/relaxation/carry-over/damping surrogate may be introduced under another name.
3. **2011 is an initial/reference observation, not a cap**: no hard storage/area maximum at the 2011 state.
4. **No arbitrary spill/freeboard thresholds**: overflow or drainage thresholds require independently observed geometry; otherwise they are forbidden.
5. **There is no 2022 pond-area observation in this analysis**: 2022 is neither calibration data nor holdout data. Its meteorology may remain in the continuous forcing series, but no 2022 pond-area value may be fitted, scored, ranked, validated against, or used for stopping/tuning.
6. **Observed pond-area years are fixed**: 2013, 2015, 2017, 2019, 2021, 2023.
7. **Evaluation statistic is fixed**: May 1-June 30 mean modeled open-water area against the six observed areas.
8. **No future information**: predictors must be causal/antecedent only. No centered rolling windows, negative shifts, future leakage, or use of later-year observations as predictors.
9. **No explicit time trend**: year/date may index observations but may not be a fitted predictor of pond area.
10. **Process accounting**: every new hydrologic loss/gain must enter the conserved water balance as an explicit flux and be recorded in diagnostics.
11. **New-process identifiability**: if a stage is proposed to test a new process, the accepted candidate must use that process materially. A coefficient driven effectively to zero is evidence to remove or redesign the process, not a reason to preserve an arbitrary tiny nonzero value.
12. **Short-term hydrologic term**: while the observation operator explicitly contains a short-term hydrologic term, its accepted coefficient must be >0. If later removed by model redesign, removal must be explicit.
13. **No grid-edge acceptance**: a calibrated search parameter at the minimum or maximum tested guard value is not accepted as final. Expand/refine the guard range and rerun.
14. **Accuracy gate**: full-six-observation nRMSE must be <=2.0% after all physical/ecological gates pass. Leave-one-year-out and nested-CV scores are optional diagnostics only and are not acceptance or ranking gates.
15. **Ecological trend guard**: the ecological state must have |corr(state, year)| <0.99 over the six observed years; otherwise it is treated as an implicit time-trend surrogate.
16. **Spring drying is diagnostic, not a fitting target**: do not require every year to dry in March-April. Report timing, zero-storage days and refilling when present. Do not tune parameters to force annual spring drying.
17. **Zero surface water is defined by conserved storage**, not an arbitrary area threshold: use numerical zero surface storage (diagnostic tolerance only).
18. **The six observed years form one calibration/evaluation set**: do not repeatedly redefine the data set by hiding one year and then reject a physically acceptable model because its fitted coefficients change. Such leave-one-year-out instability may be reported as a small-sample diagnostic, not as a model-validity gate.
19. **Literature-supported structure, site-calibrated parameters**: distinguish a process supported by literature from a parameter actually measured at Seoyeongari. Do not label calibrated values as measured.
20. **Report order** after substantive runs: full-six RMSE and nRMSE first, then water-balance/area/precipitation closure, physical/ecological gates, year-wise predictions, parameter interpretation, sensitivity results, and optional CV diagnostics only if useful.
21. **No spatial double counting**: every square metre of the modeled hydrologic domain must belong to exactly one precipitation/ET footprint on each day. Overlapping upland + wetland/open-water forcing domains are forbidden.
22. **Area partition closure**: the daily non-overlapping area components must sum to the fixed modeled domain within 1e-8 m2.
23. **Precipitation partition closure**: the sum of rainfall volumes assigned to the daily area components must equal precipitation depth times the modeled domain within 1e-8 m3.
24. **Geometry bookkeeping is not calibration**: the 2011 pond, external contributing area and potential wetland footprint must be reconciled explicitly. Small vector/raster area discrepancies are reported, not tuned away to improve fit.
25. **No arbitrary within-day loss priority**: surface evaporation, surface drainage and subsurface leakage acting during the same daily time step must be evaluated from a common pre-loss surface state. If their combined potential loss exceeds available storage, scale concurrent losses proportionally.
26. **Nested model-selection validation is not mandatory** under the six-observation analysis. Historical Stage39-48 nested results remain archived but do not determine acceptance of the current model.
27. **Fixed-candidate LOOCV is diagnostic only**: refitting Kc/Kh after omitting one of six observations may be inspected for sensitivity but must not determine the selected physical/ecological structure.
28. **Ecological coefficient plausibility outranks tiny numerical gains**: coefficients and process time scales must be interpretable and defensible. A near-zero fitted rate introduced only to satisfy a nonzero gate must be removed or reformulated rather than presented as a meaningful ecological process.
29. **Sensitivity analysis tests robustness, not desired ranking**: use ecologically/hydrologically defensible perturbation ranges and the same stated rules across competing model structures. Report whether the Integrated model remains superior or whether rankings overlap; do not choose ranges solely to force a preferred winner.
30. **Calibration-dimensionality warning**: six pond-area target years cannot independently identify every hydrologic and ecological parameter. Prefer literature/field constraints where available, and describe remaining fitted parameters explicitly as calibrated rather than measured.
