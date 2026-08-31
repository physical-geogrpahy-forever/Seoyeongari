# Seoyeongari model evaluation metrics — locked methodology

## Purpose

This file fixes the model-performance evaluation procedure used for the Seoyeongari wetland model so that the reported accuracy metrics are reproducible and their interpretation is unambiguous.

The primary metrics are:

- Root Mean Square Error (RMSE; m²)
- mean-normalized Root Mean Square Error (nRMSE; %)
- Mean Absolute Error (MAE; m²)
- Mean Bias Error (MBE; m²)

The definitions below are to be applied consistently to Baseline, Eco–Geo, Hydrosere, and Integrated scenarios.

## 1. Evaluation years and observation series

The 2011 mapped wetland area is used as the model initialization condition and is **not** included in performance scoring.

Performance is evaluated using six independent observation years:

\[
Y=\{2013,2015,2017,2019,2021,2023\}, \qquad n=6.
\]

Observed mapped wetland areas are:

| Year | Observed area (m²) |
|---:|---:|
| 2013 | 2154.430 |
| 2015 | 2147.678 |
| 2017 | 2051.218 |
| 2019 | 2045.159 |
| 2021 | 1965.256 |
| 2023 | 1882.700 |

The mean observed area over the six scored years is:

\[
\overline{A}_{obs}=2041.0735\;\mathrm{m^2}.
\]

## 2. Ensemble prediction used for scoring

For each scenario and evaluation year, the representative model prediction is the **median mapped wetland area across the retained ensemble members**.

\[
\hat A_i=\operatorname{median}(\hat A_{i,1},\hat A_{i,2},\ldots,\hat A_{i,M}),
\]

where \(\hat A_i\) is the representative prediction for evaluation year \(i\), and \(M\) is the number of retained ensemble members.

The Stage232 observation operator is the mapped wetland area represented by water plus temporary bare area under the locked state-transition rules. All four scenarios are evaluated using the same observation and scoring definitions.

## 3. Error definition

Signed error is defined as prediction minus observation:

\[
e_i=\hat A_i-A_i,
\]

where \(A_i\) is observed mapped wetland area and \(\hat A_i\) is the ensemble-median model prediction for the same evaluation year.

With this sign convention:

- \(e_i>0\): overprediction
- \(e_i<0\): underprediction

The same sign convention is used for MBE.

## 4. Root Mean Square Error (RMSE)

\[
\mathrm{RMSE}=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(\hat A_i-A_i)^2}.
\]

For this study, \(n=6\).

RMSE retains the physical unit of the response variable (m²) and gives greater influence to larger individual errors because the residuals are squared before averaging.

**Reference basis:** Willmott (1982); Willmott and Matsuura (2005).

## 5. Mean-normalized RMSE (nRMSE)

Because multiple definitions of normalized RMSE exist in the literature, the normalization denominator must be stated explicitly. In this study, RMSE is normalized by the **mean observed mapped wetland area across the six scored years**:

\[
\mathrm{nRMSE}(\%)=\frac{\mathrm{RMSE}}{\overline{A}_{obs}}\times100,
\]

where

\[
\overline{A}_{obs}=\frac{1}{n}\sum_{i=1}^{n}A_i.
\]

Thus, nRMSE represents RMSE as a percentage of the mean observed wetland area. It is **not** normalized by the observed range, maximum observation, standard deviation, or 2011 initial area.

This mean-normalized definition is consistent with published relative/normalized RMSE applications in model evaluation, including Iizumi et al. (2014), who calculated relative RMSE against the long-term mean observed data.

## 6. Mean Absolute Error (MAE)

\[
\mathrm{MAE}=\frac{1}{n}\sum_{i=1}^{n}|\hat A_i-A_i|.
\]

MAE retains the physical unit (m²) and represents the mean absolute magnitude of prediction error without cancellation between positive and negative residuals.

RMSE and MAE are reported together because they emphasize different aspects of model error: RMSE is more sensitive to larger errors, whereas MAE directly summarizes the average absolute discrepancy.

**Reference basis:** Willmott (1982); Willmott and Matsuura (2005).

## 7. Mean Bias Error (MBE)

\[
\mathrm{MBE}=\frac{1}{n}\sum_{i=1}^{n}(\hat A_i-A_i).
\]

Equivalently,

\[
\mathrm{MBE}=\overline{\hat A}-\overline{A}.
\]

MBE retains the physical unit (m²) and indicates the direction of systematic model bias under the prediction-minus-observation convention:

- MBE > 0: mean overprediction
- MBE < 0: mean underprediction
- MBE = 0: no mean signed bias

Because positive and negative residuals can cancel, MBE must not be interpreted as a measure of total error magnitude and is therefore reported together with RMSE and MAE.

**Reference basis:** Willmott (1982).

## 8. Locked reporting format

Model comparison tables should report the metrics in the following order:

| Scenario | RMSE (m²) | nRMSE (%) | MAE (m²) | MBE (m²) |
|---|---:|---:|---:|---:|
| Baseline | — | — | — | — |
| Eco–Geo | — | — | — | — |
| Hydrosere | — | — | — | — |
| Integrated | — | — | — | — |

All four metrics must be calculated from the **same six evaluation years and the same ensemble-median predictions**.

## 9. Implementation check against Stage232

The locked Stage232 scoring implementation follows the same procedure:

```python
med = g.groupby('year').water_plus_bare_m2.median()
obs = np.array([OBSERVED_WETLAND_M2[y] for y in SCORED_YEARS])
pred = np.array([med[y] for y in SCORED_YEARS])
rmse = float(np.sqrt(np.mean((pred - obs)**2)))
nrmse = 100 * rmse / float(obs.mean())
```

MAE and MBE are to be calculated from the same `pred` and `obs` arrays:

```python
mae = float(np.mean(np.abs(pred - obs)))
mbe = float(np.mean(pred - obs))
```

No metric is to be used to select or tune model parameters retrospectively against the observation series.

## References

Iizumi, T., Tanaka, Y., Sakurai, G., Ishigooka, Y., & Yokozawa, M. (2014). Dependency of parameter values of a crop model on the spatial scale of simulation. *Journal of Advances in Modeling Earth Systems, 6*, 527–540. https://doi.org/10.1002/2014MS000311

Willmott, C. J. (1982). Some comments on the evaluation of model performance. *Bulletin of the American Meteorological Society, 63*(11), 1309–1313. https://doi.org/10.1175/1520-0477(1982)063%3C1309:SCOTEO%3E2.0.CO;2

Willmott, C. J., & Matsuura, K. (2005). Advantages of the mean absolute error (MAE) over the root mean square error (RMSE) in assessing average model performance. *Climate Research, 30*, 79–82. https://doi.org/10.3354/cr030079
