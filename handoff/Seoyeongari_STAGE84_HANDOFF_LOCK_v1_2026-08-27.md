# Stage84 handoff lock

- Succession model: **Twin Limit Marsh Model (Keddy & Campbell 2019/2020)**. Do not replace with a score, GDD hybrid, logistic transition, or arbitrary exposure threshold.
- Apply published TLMM `dt/f/cmin` lower-limit and `xt/s/wmin` upper-limit equations **at specified elevations**.
- Seoyeongari hypsometry/DEM may be used only to integrate those elevation-specific TLMM states to actual area; label this as EGHM site geometry coupling.
- `f=4 yr`, `cmin=0.01`, `s=30 yr`, `wmin=0.001` are the current central published TLMM values. `s=15 yr` is published Great Lakes sensitivity only. Do not fit `s` to pond-area observations.
- The ~5.3 yr tree-ring lag is not automatically TLMM `s`; `s` means time to closed-canopy woody vegetation.
- Canonical raw meteorological inputs are exactly two CSVs: AWS + ASOS. `daily_forcing_v5_equations.csv` is derived only and must never be treated as a third raw dataset or execution requirement.
- Evaluation years: 2013, 2015, 2017, 2019, 2021, 2023. 2011 initialization. 2022 mapped area does not exist and must not be used.
- Library/archive existence and current runtime mount are separate states. Do not call raw files missing merely because `/mnt/data` lacks their bytes.
