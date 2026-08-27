# Seoyeongari / EGHM — NEXT CHAT HANDOFF

**Date:** 2026-08-27  
**Current branch:** `chatgpt-stage30-20260826`  
**Project:** Seoyeongari wetland Eco–Geo–Hydro model + TLMM reformulation  
**Immediate status:** Stage85 integrated daily model ran, but its hydrologic baseline is not yet scientifically accepted. Stage86 decomposed that baseline and identified the dominant structural problem as direct pond-loss terms and seasonal hydrologic memory, not the TLMM equations themselves.

---

# 0. READ THIS FIRST — FILE ACCESS IS A HARD REQUIREMENT

Before doing any model work, read the permanent Library handoff:

- Library path: `/EGHM/00_MUST_READ_FIRST_EGHM_FILE_LIBRARY_HANDOFF.md`
- file_id: `file_000000008e8c8207b0ac57c7d555f864`

The file says, and the next chat MUST obey:

1. **Never equate “not in current `/mnt/data`” with “file does not exist”.**
2. **Never use a `files.search` miss as proof of absence.**
3. If the Library path/folder is known, use **`files.list` on that exact folder first**.
4. Take the **real `file_id` returned by `files.list`**.
5. Call **`files.materialize` with that exact `file_id`** to copy the raw bytes into `/mnt/data`.
6. After materialization verify:
   - exact byte size,
   - SHA-256,
   - ZIP integrity (`ZipFile.testzip()`),
   - internal archive listing.
7. Search parent ZIPs/handoff archives before concluding that an internal raw file is absent.
8. Only use `TRULY_MISSING` after checking exact Library listing, exact file_id/path, parent archives, latest handoff/manifest, and current runtime mount status.

Required state vocabulary:

- `LIBRARY_DIRECT`
- `LIBRARY_IN_ARCHIVE`
- `RUNTIME_READY`
- `RUNTIME_NOT_MOUNTED`
- `MATERIALIZE_FAILED`
- `REFERENCE_ONLY`
- `TRULY_MISSING`

**Do not ask the user to re-upload a known Library file until `files.list → files.materialize` has actually been attempted and failed.**

---

# 1. PROVEN RAW-INPUT RECOVERY PACKAGE

The most important recovery object is already in File Library:

- file_id: `file_000000006330820bb97e7d8db9ce6984`
- Library path: `/EGHM/Seoyeongari_RAW_INPUT_RECOVERY_2026-08-27.zip`
- size: **3,146,778 bytes**
- verified SHA-256:  
  `187537eae8d61007f032eaeed352f6264f9b2c25eb00b2a7515e70d2bd8c8955`
- ZIP entries: **14**
- `testzip() = None`

Verified members include:

- `raw/met/OBS_AWS_DD_20250930013603.csv`
- `raw/met/OBS_ASOS_DD_20250930041037.csv`
- `raw/gis/dem/dem.tif`
- `raw/gis/plot_2011/plot_2011.shp`
- `raw/gis/plot_2011/plot_2011.shx`
- `raw/gis/plot_2011/plot_2011.dbf`
- `raw/gis/plot_2011/plot_2011.prj`
- `raw/gis/plot_2023.zip`
- `raw/gis/plot_2023_verified/plot_2023.shp`
- `raw/gis/plot_2023_verified/plot_2023.shx`
- `raw/gis/plot_2023_verified/plot_2023.dbf`
- `raw/gis/plot_2023_verified/plot_2023.prj`
- `raw/gis/plot_2023_verified/plot_2023.cpg`
- `RAW_INPUT_RECOVERY_MANIFEST_2026-08-27.json`

**Canonical recovery procedure:**

`files.list(surface="library", library_path="/EGHM")`  
→ recover exact file_id  
→ `files.materialize(file_000000006330820bb97e7d8db9ce6984)`  
→ verify byte size/SHA/ZIP integrity  
→ extract only after integrity passes.

A missing `/mnt/data/OBS_AWS...csv` is therefore **`RUNTIME_NOT_MOUNTED` or `LIBRARY_IN_ARCHIVE`**, not “missing”.

---

# 2. METEOROLOGICAL INPUT — TWO RAW FILES ONLY

There are exactly two raw meteorological inputs:

1. `OBS_AWS_DD_20250930013603.csv`
   - Seogwang AWS
   - station 752
   - nearest station intentionally retained
   - fields used: temperature, precipitation, wind
   - prior verified shape: **5479 × 6**
   - encoding: UTF-8
   - expected columns: `time,tmean,tmin,tmax,pre,wind`
   - prior recorded size: **174,481 B**
   - prior SHA prefix: `e0c10056a863a70c...`

2. `OBS_ASOS_DD_20250930041037.csv`
   - Seogwipo ASOS station 189
   - used for sunshine duration
   - prior verified shape: **5448 × 4**
   - encoding: CP949
   - must retain station 189 if station column exists
   - prior recorded size: **145,841 B**
   - prior SHA prefix: `acc6763cc618d5ad...`

`daily_forcing_v5_equations.csv` is **NOT a third raw dataset**. It is a derived reproducibility file.

Dependency is:

AWS raw + ASOS raw  
→ established V5 FAO/Penman/NRCS forcing equations  
→ daily forcing  
→ EGHM/TLMM model.

Reference derived forcing previously verified:

- 5479 × 8
- columns: `DATE,YEAR,PRE,E_P,ETo,P_ES,P_P,Q_S`
- SHA-256: `4ee18a90298d5407f0a7909e992cff9d3858b882d624f35fe85007fe8361d994`

If the raw two files exist, missing derived forcing must **not** block model execution.

---

# 3. OTHER OLDER RAW-ARCHIVE PROVENANCE

Earlier audits also proved the same AWS/ASOS files exist inside:

- `VESLEM_v5_bottomrelax_reproducibility_package.zip`
  - prior size: **3,441,479 B**
  - internal paths under `input_data/`

- `Seoyeongari_NEXT_CHAT_RUNTIME_v3_STAGE29_REALDATA_2026-08-26.zip`
  - prior size: **11,205,255 B**
  - internal paths under `raw/met/`

- `OBS_AWS_DD_20250930013603.zip`
  - prior size: **72,338 B**
  - despite the name, this ZIP contains **both AWS and ASOS CSVs**.

Therefore, if one archive is unavailable, inspect the others before declaring failure.

---

# 4. MANUSCRIPT / PROJECT DOCUMENTS

Current manuscript-family files in File Library:

- Main v11:  
  `/EGHM/2%20-%20Main%20body_R1_science_fixes_v11.docx`  
  file_id `file_000000008d3481fbb7a1151c25aa19aa`

- Supplement v9:  
  `/EGHM/4%20-%20Supplementary_R1_methods_v9.docx`  
  file_id `file_00000000597481f8af7b1622d615c0d2`

- Figures v2_3:  
  file_id `file_00000000d3b082118aea16d2b4621aaa`

- Reviewer-response draft:  
  file_id `file_0000000091048209911fcec43c5f720e`

- Master revision log:  
  `Seoyeongari_Round1_revision_master_log_v1.md`  
  file_id `file_0000000068448211a26b25996df399dc`

Do **not** edit manuscript science until the new hydrologic/TLMM formulation is frozen.

---

# 5. OBSERVATION SERIES — DO NOT INVENT 2022

Use these mapped pond/water-body areas:

- 2011: 2242.974 m² — initialization/reference
- 2013: 2154.430
- 2015: 2147.678
- 2017: 2051.218
- 2019: 2045.159
- 2021: 1965.256
- 2023: 1882.700

**2022 pond area does not exist for calibration/evaluation.**

2022 meteorological forcing remains because it is required for the 2023 state trajectory.

---

# 6. IMPORTANT OBSERVATION-TIMING DISCREPANCY

The latest Main manuscript explicitly states:

- airborne images were acquired in **April or May**;
- water-body boundaries were manually interpreted/digitized from each image;
- these polygons are intended to represent the visible water-body boundary.

An older handoff also records a user-defined proxy rule:

- use **May 1–June 30 mean simulated area** for comparison.

These two are not identical. Do not silently choose one and pretend the conflict does not exist.

**Next best action:** recover exact acquisition dates from NGII image metadata if possible, then compare the daily model to the actual image dates. If exact dates cannot be recovered, retain an explicitly labeled April–May or May–June proxy and test the timing sensitivity. Do not use timing-window changes merely to improve fit.

---

# 7. FIELD/HYDROPERIOD CONSTRAINT THAT MUST REMAIN

Site observations and later satellite NDWI evidence support recurrent spring drying:

- surface/open water frequently disappears around **March–April**;
- therefore any final model with zero dry days throughout the period is not acceptable;
- monthly NDWI does **not** justify an exact number of dry days; the defensible constraint is recurrent spring drying/exposure.

This is the long-standing structural conflict:

**good multi-year pond-area fit** vs **realistic spring hydroperiod**.

Do not solve this by restoring the old λ=0.035 empirical memory operator.

---

# 8. TLMM — CURRENT ECOLOGICAL RULE SET

Use the published **Twin Limit Marsh Model (TLMM; Keddy & Campbell 2020 / Wetlands)** rather than a newly invented succession score.

Core published-rule settings currently adopted:

## Flooding / lower limit

- `f = 4 yr` central temperate value
- `cmin = 0.01`
- continuous flooding duration `dt`

`cd = 10^[ -log10(cmin) * ((dt - f)/f) ]`

`R_f = (1 - cd)/(1 - cmin)`

If `dt >= f`, marsh response goes to zero.

## Dewatering / upper limit

- `s = 30 yr` central general temperate value
- `wmin = 0.001`
- `xt` = years continuously dewatered/subject to succession

`wx = 10^[ -log10(wmin) * ((xt - s)/s) ]`

`R_w = (1 - wx)/(1 - wmin)`

If `xt >= s`, marsh response goes to zero / woody dominance reaches endpoint.

`S = 15 yr` is **sensitivity only**, because the published Great Lakes worked example used 15 yr. Do not use 15 yr as the central Seoyeongari value.

**Do not fit `s` or `f` to the six pond-area observations.**

**Do not restore q-scores, annual point accumulation, S/r_est/K_colonizable, or arbitrary succession lags.**

One growing-season drawdown/recruitment logic and annual TLMM state updates should remain source-faithful.

---

# 9. FOUR SCENARIO DEFINITIONS — CURRENT TARGET

Keep process definitions clean:

- **Baseline**: no peat, no TLMM succession. Reversible water ↔ bare exposure only.
- **Hydrosere Only**: TLMM succession + vegetation-specific ET; no peat.
- **Eco-Geo Only**: reversible water ↔ bare + peat geomorphic forcing; no TLMM succession.
- **Integrated**: TLMM succession + vegetation-specific ET + peat geomorphic forcing.

Historical vegetation ET coefficients retained for current testing:

- bare: K ≈ **0.30**
- herbaceous/marsh: K ≈ **0.90**
- woody/forest: K ≈ **0.95**
- background forest: ≈ **0.95**

Peat must act as geomorphic/storage change, **not as water deletion**.

Do not force Integrated to rank first.

---

# 10. STAGE79 / STAGE84 / STAGE85 STATUS

## Stage79

Stage79 is the key source-faithful TLMM boundary implementation. Its TLMM functions and state-transition tests passed. The remaining CI issue at the time was a contract/message mismatch, not failure of the core mathematical tests.

Use Stage79 as the ecological gold standard when checking later integrated implementations.

## Stage84

Stage84 introduced a daily mass-conserved hydro + TLMM band implementation and raw-meteorology reconstruction gate. Internal TLMM/source-fidelity tests passed, but the real-data run was initially blocked because raw AWS/ASOS were not mounted in that runtime. This is now a solved file-governance problem because the recovery ZIP is proven in Library.

## Stage85

Current GitHub integrated code:

- `stage85_exact_tlmm_integrated.py`

It combines daily hydrology, TLMM-related area/state behavior, vegetation ET, and peat, and actually ran against raw meteorological data.

**However Stage85 is NOT accepted as the final model.**

Reason: its strict physical Baseline gave roughly **47% nRMSE**, far worse than the historical Stage78 statistical Baseline. This does not mean “TLMM failed”. Stage78 Baseline contained a fitted observation equation term `A = A0 + K_hydro·H`; Stage85 removed that fitted observation correction and compared direct modeled open water. Therefore Stage78 ≈10% and Stage85 ≈47% are not equivalent baselines.

Stage85 artifacts downloaded in the current chat included:

- `stage85-results.zip`
- `stage85_results/baseline_model_daily.csv`
- `baseline_model_evaluation.csv`
- `hydrosere_only_model_daily.csv`
- `hydrosere_only_model_evaluation.csv`
- `eco_geo_only_model_daily.csv`
- `eco_geo_only_model_evaluation.csv`
- `integrated_model_daily.csv`
- `integrated_model_evaluation.csv`
- `stage85_all_evaluation_years.csv`
- `stage85_annual_state_diagnostics.csv`
- `stage85_four_scenario_summary_s30.csv`
- `stage85_s15_s30_published_sensitivity.csv`

GitHub Actions artifact ID from the completed Stage85 run:

- **9644772506**

If not present in a new runtime, rerun from GitHub or download the Actions artifact; do not assume current `/mnt/data` persists across chats.

---

# 11. STAGE86 — CURRENT MOST IMPORTANT DIAGNOSTIC

GitHub files:

- `stage86_stage85_seasonal_budget_diagnostic.py`
  - commit: `3da8593dc4276f6fc25622fb0bc405e28eea8f55`

- `.github/workflows/stage86.yml`
  - commit: `3ba7bc7cf769bcbd44821da393a2bf6673af6339`

GitHub Actions:

- run ID: **33069100810**
- result: **SUCCESS**
- artifact: `stage86-seasonal-budget-diagnostic`
- artifact ID: **9644989678**
- artifact ZIP SHA-256:  
  `b9112fd7be0c14987b7a0fbde5c640ff4678f30740dc5322b29df091524f8265`
- artifact size: **836,264 B**

Stage86 was deliberately diagnostic only:

- changed **no scientific parameters**;
- reproduced Stage85 Baseline exactly:
  - max area difference = **0.0 m²**
  - max volume difference = **0.0 m³**
- mass-balance max error = **1.8189894035458565e-12 m³**.

Therefore the following diagnosis is about the actual Stage85 Baseline, not a separate approximation.

---

# 12. STAGE86 RESULTS — WHY 2013/2017/2019 COLLAPSE

Stage86 examined the hydrologic support from **Oct–Dec of the previous year + Jan–Apr of the observation year**.

Key end-April Baseline states:

| Year | start pond V (m³) | end-Apr V (m³) | end-Apr hydraulic area (m²) | zero-surface days |
|---|---:|---:|---:|---:|
| 2013 | 2296.54 | 103.26 | 1786.41 | 18 |
| 2015 | 1173.75 | 828.57 | 2200.00 | 0 |
| 2017 | 153.36 | 139.32 | 1840.74 | 33 |
| 2019 | 462.81 | ~0 | 28.52 | 102 |
| 2021 | 2658.24 | 289.89 | 1980.67 | 11 |
| 2023 | 760.33 | 329.44 | 2006.17 | 77 |

Pre-observation direct pond supply vs direct pond losses:

| Year | direct supply (m³) | direct pond losses (m³) |
|---|---:|---:|
| 2013 | 2488.92 | 4682.21 |
| 2015 | 3906.08 | 4251.26 |
| 2017 | 4020.87 | 4034.90 |
| 2019 | 1588.46 | 2051.27 |
| 2021 | 2764.86 | 5133.21 |
| 2023 | 2136.02 | 2566.91 |

The critical discovery is that the collapse is dominated by **direct pond-loss structure**, especially:

- surface-store residence outflow: approximately `surf / 60 days`
- a direct groundwater/leakage-like loss around `4.0 mm/day × pond area`
- plus open-water evaporation.

2019 is the clearest example: the pond reaches essentially zero before the observation period despite mapped area remaining ~2045 m².

This means the immediate scientific problem is **not the TLMM response curves**. It is whether those daily pond-loss terms are physically justified for Seoyeongari.

---

# 13. CRITICAL PROVENANCE WARNING — 4 mm/day MUST NOT BE TREATED AS TRUTH

Older audit explicitly established:

- Mulyeongari hydraulic conductivity K must **not** be used directly as an actual leakage flux;
- Darcy flux is `q = K i`, not simply `q = K`;
- the old effective leakage around **4.091 mm/day** was a strong modeling assumption;
- prior handoff explicitly said: **do not reuse Mulyeongari K=4.091 mm/day as actual Seoyeongari leakage**.

Therefore Stage85's ~4 mm/day direct pond groundwater/loss term is now a top-priority provenance issue.

Likewise, the **60-day surface residence/outflow constant** has not yet been demonstrated here as a field-measured Seoyeongari quantity. Its provenance must be recovered before it is retained.

Do **not** immediately tune either value to the pond-area observations. First determine whether these terms belong in the structural model at all.

---

# 14. WHAT HAS ALREADY FAILED — DO NOT REPEAT BLINDLY

Prior strict-model experiments already showed:

- simple pond-only storage cannot match area and spring drying simultaneously;
- increasing depth/storage until fit is good requires physically absurd ~8–10 m average-scale depths;
- all catchment recharge routed to pond produces massive overfilling;
- a single slow groundwater reservoir failed;
- simple two-reservoir/slow-memory structures failed to satisfy both area trajectory and spring drying;
- Stage26 achieved nRMSE ~8% but dry days = 0 and huge spill;
- Stage27/28 could produce drying but 2017/2019 collapse returned and nRMSE degraded severely;
- simple orographic precipitation multiplication did not solve the problem;
- mm→m³ conversion was already audited and is correct;
- the 2025 5939.5 m² pond+transition footprint must not be declared the hydrologic catchment.

Do not restart these old branches without a new hypothesis.

---

# 15. CURRENT BEST HYDROLOGIC INTERPRETATION

The old λ=0.035 annual relaxation created an empirical ~decadal memory and hid closure problems. Removing it revealed that **pond volume alone is not the correct memory state**.

The most plausible unresolved structure remains:

- external catchment rainfall partition,
- soil/root-zone storage,
- perched/local recharge,
- travel time,
- regional/deep loss,
- shallow wetland subsurface storage,
- visible surface-water threshold,
- microtopographic/fill–spill wetness geometry.

The model must allow:

- spring surface drying,
- later refilling,
- broad/shallow visible pond boundaries in wet years,
- strict mass conservation,
- no arbitrary λ memory operator.

---

# 16. EXACT NEXT TASK ORDER

The next chat should proceed in this order.

## Step 1 — pre-flight/file governance

Read `/EGHM/00_MUST_READ_FIRST_EGHM_FILE_LIBRARY_HANDOFF.md`.

If raw inputs are not in `/mnt/data`:

`files.list(/EGHM)`  
→ recover `file_000000006330820bb97e7d8db9ce6984`  
→ `files.materialize`  
→ verify size/SHA/testzip  
→ extract raw AWS/ASOS/GIS.

## Step 2 — reproduce Stage85 and Stage86 unchanged

Pull/inspect branch `chatgpt-stage30-20260826` and ensure Stage85/86 reproduce before any edit.

Acceptance checks:

- Stage86 area diff vs Stage85 = 0
- volume diff = 0
- mass error <1e-8 m³

## Step 3 — recover provenance for the two suspicious direct pond-loss terms

Trace exactly where the following entered the code:

- `TAU_SURF ≈ 60 d`
- `K_GW ≈ 4.0 mm/d`

Classify each as:

- field measured,
- literature-derived,
- analogue-derived,
- calibrated,
- assumed,
- inherited diagnostic constant.

Do not retain them merely because a prior stage used them.

## Step 4 — structural ablation, NOT optimization

Run fixed-parameter diagnostic variants of the Stage85 Baseline:

- current loss structure
- remove only `surf/60` outflow
- remove only `4 mm/day` direct groundwater loss
- remove both
- replace direct pond groundwater loss with the original model's parsimonious fractional percolation formulation only as a documented comparator, not as an automatic final choice

For each report:

- 2013/15/17/19/21/23 April–May or exact-date mapped-area error
- recurrent spring dry occurrence
- annual/seasonal water budget
- total and maximum mass-balance error
- pond zero-day counts
- spill/outflow totals

No parameter tuning in this diagnostic.

## Step 5 — observation timing

Recover exact orthophoto acquisition dates if possible.

If exact dates are available, compare modeled visible water to those dates.

If not, explicitly compare:

- April–May mean
- historical May–June proxy

and document that this is timing uncertainty, not calibration.

## Step 6 — only after hydrologic core is acceptable, reattach TLMM/peat

Use Stage79 TLMM logic as ecological reference.

Run four scenarios with:

- `f=4`
- `s=30` central
- `s=15` sensitivity only
- vegetation ET 0.30 / 0.90 / 0.95
- site-informed peat rate central around 0.38 mm/yr if retaining the current long-term constraint

Do not fit TLMM parameters to the six observations.

## Step 7 — final comparison

Report, without forcing ranking:

- 6-year predicted areas
- RMSE / nRMSE
- hydroperiod compatibility
- spring-dry behavior
- mass closure
- marsh/woody state diagnostics
- ET feedback magnitude
- peat geomorphic effect
- 2021–2023 late-period behavior

Only then decide whether Integrated actually outperforms Hydrosere/Eco-Geo/Baseline.

---

# 17. NON-NEGOTIABLE SCIENTIFIC RULES

- No invented 2022 observation.
- No return to q-score / point accumulation.
- No fitted TLMM `s`/`f` from the six mapped-area observations.
- No old λ=0.035 resurrection as “hydrologic memory”.
- No treating the interpolated DEM as independent bathymetric evidence.
- No treating 5939.5 m² transition footprint as confirmed hydrologic catchment.
- No treating Mulyeongari K as Seoyeongari leakage flux.
- No forcing Integrated-best in the objective.
- No manuscript claim that good calibration = independent validation.
- No saying “mass closure passed, therefore the model is correct”.
- No declaration that a file is missing before the Library/materialization workflow is exhausted.

---

# 18. GITHUB / PERSISTENCE

Repository:

`physical-geogrpahy-forever/Seoyeongari`

Working branch:

`chatgpt-stage30-20260826`

Important latest commits:

- Stage86 diagnostic code: `3da8593dc4276f6fc25622fb0bc405e28eea8f55`
- Stage86 workflow: `3ba7bc7cf769bcbd44821da393a2bf6673af6339`

A separate `MUST READ FIRST` file-access document was also committed earlier to the branch. The File Library copy `/EGHM/00_MUST_READ_FIRST_EGHM_FILE_LIBRARY_HANDOFF.md` is the authoritative cross-chat file-transfer rule.

---

# 19. ONE-PARAGRAPH CURRENT SCIENTIFIC CONCLUSION

The current reformulation has successfully replaced arbitrary succession scoring with a published TLMM framework and established a reproducible raw-data/file-governance path. However, the new strict daily model exposed a more fundamental hydrologic issue: the model's direct pond-loss terms can drain the pond to near zero in 2013/2017/2019 despite mapped April–May water-body areas remaining around 2,000 m². Stage86 proved that this is not a coding-drift artifact and isolated direct surface residence outflow and ~4 mm/day groundwater/leakage loss as dominant suspects. Because the latter has already been flagged as an unjustified use of a Mulyeongari analogue if treated as actual leakage, the next scientific step is **provenance + structural ablation of those loss terms**, followed by exact image-date evaluation, before any further TLMM/peat calibration or manuscript synchronization.
