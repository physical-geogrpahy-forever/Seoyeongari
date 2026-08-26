# EGHM strict model rules

These rules are non-negotiable. A lower RMSE never overrides a failed rule.

1. **Exact daily water balance**: maximum daily closure error must be <= 1e-8 m3.
2. **lambda = 0**: no memory/relaxation/carry-over/damping surrogate may be introduced under another name.
3. **2011 is an initial/reference observation, not a cap**: no hard storage/area maximum at the 2011 state.
4. **No arbitrary spill/freeboard thresholds**: overflow or drainage thresholds require independently observed geometry; otherwise they are forbidden.
5. **2022 is holdout only**: 2022 pond area is excluded from fitting, ranking, feature selection, parameter selection and stopping criteria. 2022 meteorology remains in the continuous forcing series.
6. **Evaluation years are fixed**: 2013, 2015, 2017, 2019, 2021, 2023.
7. **Evaluation statistic is fixed**: May 1-June 30 mean modeled open-water area against the six observed areas.
8. **No future information**: predictors must be causal/antecedent only. No centered rolling windows, negative shifts, future leakage, or use of later-year observations.
9. **No explicit time trend**: year/date may index observations but may not be a fitted predictor of pond area.
10. **Process accounting**: every new hydrologic loss/gain must enter the conserved water balance as an explicit flux and be recorded in diagnostics.
11. **New-process identifiability**: if a stage is proposed to test a new process, the accepted candidate must use a nonzero value for that process. If the optimum sets it to zero, that stage does not support the process and is rejected as a process model.
12. **Short-term hydrologic term**: while the current observation operator explicitly contains a short-term hydrologic term, its accepted coefficient must be >0. If later removed by model redesign, removal must be explicit rather than silently accepting a zero coefficient.
13. **No grid-edge acceptance**: a calibrated search parameter at the minimum or maximum tested value is not accepted as final. Expand/refine the range and rerun.
14. **Accuracy gate**: training nRMSE <=2.0% and LOOCV nRMSE <=2.0% are both required after all physical gates pass.
15. **Ecological trend guard**: the ecological state must have |corr(state, year)| <0.99 for the six evaluation years; otherwise it is treated as an implicit time-trend surrogate.
16. **Spring drying is diagnostic, not a fitting target**: do not require every year to dry in March-April. Report timing, zero-storage days and refilling when present. Do not tune parameters to force annual spring drying.
17. **Zero surface water is defined by conserved storage**, not an arbitrary area threshold: use numerical zero surface storage (diagnostic tolerance only).
18. **Holdout order is irreversible**: lock the candidate first, write it to output, then run 2022 holdout in a separate step. Never return to tuning because of the 2022 result.
19. **Literature-supported structure, site-calibrated parameters**: distinguish a process supported by literature from a parameter actually measured at Seoyeongari. Do not label calibrated values as measured.
20. **Report order** after substantive runs: RMSE and nRMSE first, then LOOCV, water-balance error, rule-gate result, year-wise predictions, and diagnostics.
21. **No spatial double counting**: every square metre of the modeled hydrologic domain must belong to exactly one precipitation/ET footprint on each day. Overlapping upland + wetland/open-water forcing domains are forbidden.
22. **Area partition closure**: the daily non-overlapping area components must sum to the fixed modeled domain within 1e-8 m2. Failure rejects the model even when volumetric mass residual is zero.
23. **Precipitation partition closure**: the sum of rainfall volumes assigned to the daily area components must equal precipitation depth times the modeled domain within 1e-8 m3. Algebraically closed but spatially double-counted models are invalid.
24. **Geometry bookkeeping is not calibration**: the 2011 pond, external contributing area and potential wetland footprint must be reconciled explicitly. Small vector/raster area discrepancies are reported, not tuned away to improve fit.
