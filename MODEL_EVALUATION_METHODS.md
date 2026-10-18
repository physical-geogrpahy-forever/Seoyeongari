# Stage239 model-evaluation methods

The paper reports accuracy for the six independent mapped-area years
`{2013, 2015, 2017, 2019, 2021, 2023}`. The 2011 mapped area initializes the model and is not scored. The 2022 value is retained as a diagnostic observation only.

For each scenario and scored year, the prediction is the median mapped area across the retained ensemble members. With prediction minus observation as the signed residual:

```text
RMSE  = sqrt(mean((prediction - observation)^2))
nRMSE = 100 * RMSE / mean(observed area)
```

The six-year mean observed area is 2041.0735 m2. The central Stage239 (`Cgw=0`) results are:

| Scenario | RMSE (m2) | nRMSE (%) |
|---|---:|---:|
| Baseline | 164.1231 | 8.0410 |
| Eco–Geo | 44.9467 | 2.2021 |
| Hydrosere | 131.2404 | 6.4300 |
| Integrated | 38.2614 | 1.8746 |

The scoring implementation is in `CODE/stage239_explicit_gw_exchange.py`; the exact central and sensitivity rows are archived in `RESULTS/stage239_explicit_gw_scores.csv`.
