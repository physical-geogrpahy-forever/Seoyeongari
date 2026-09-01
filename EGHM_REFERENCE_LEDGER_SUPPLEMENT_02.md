# EGHM reference ledger — Supplement 02: inherited hydrology constants and linear-reservoir audit

Updated: 2026-08-27

## Scope

The current Stage49 hydrology inherits several fixed constants from the Stage35c/38 implementation that were not included among the nine Stage52 OAT axes:

- `SOIL_DEPTH = 0.294 * 0.55 = 0.1617 m water-equivalent storage`
- `ET_EXT = 0.95`
- `FAST_FRAC = 0.75`
- `TAU_SLOW = 365 d`

This supplement distinguishes (1) whether the *process form* has literature support, and (2) whether the *exact numerical value* has independent site/reference support.

---

# K1. Linear-reservoir routing form

## Nash (1957)

Nash, J.E. (1957). **The form of the instantaneous unit hydrograph.** International Association of Scientific Hydrology Publication 45, 114–121.

Evidence class: **DIRECT FORM**.

Key support:
- catchment routing can be represented parsimoniously by successive linear-storage reservoirs;
- the linear storage formulation is a long-established conceptual hydrology approximation.

Use in EGHM:
- supports equations of the generic form `Q = S / tau` for conceptual reservoir drainage;
- does not constrain `tau_fast`, `tau_slow`, or the fast/slow partition for Seoyeongari.

## Moore (2007)

Moore, R.J. (2007). **The PDM rainfall-runoff model.** *Hydrology and Earth System Sciences*, 11, 483–499. DOI: **10.5194/hess-11-483-2007**.

Evidence class: **DIRECT CONCEPTUAL-MODEL FORM**.

Key support:
- practical rainfall–runoff models may partition flow into fast surface and slow groundwater pathways;
- linear-reservoir routing is a standard parsimonious representation in conceptual hydrology.

Use in EGHM:
- supports having separate fast and slow local-return stores as a modelling family;
- does not justify `FAST_FRAC = 0.75` or `TAU_SLOW = 365 d`.

## Wittenberg & Sivapalan (1999)

Wittenberg, H. & Sivapalan, M. (1999). **Watershed groundwater balance estimation using streamflow recession analysis and baseflow separation.** *Journal of Hydrology*, 219, 20–33. DOI: **10.1016/S0022-1694(99)00040-2**.

Evidence class: **FORM + CAVEAT**.

Key support:
- groundwater storage, recharge, discharge and ET can be inferred from recession behaviour;
- observed shallow-groundwater storage–discharge relations may be nonlinear rather than exactly linear.

Use in EGHM:
- supports reservoir/recession conceptualization but cautions that `Q=S/tau` is a parsimonious approximation, not a universal physical law.

## Wittenberg (1999)

Wittenberg, H. (1999). **Baseflow recession and recharge as nonlinear storage processes.** *Hydrological Processes*, 13, 715–726. DOI: **10.1002/(SICI)1099-1085(19990415)13:5<715::AID-HYP775>3.0.CO;2-N**.

Evidence class: **STRUCTURAL CAVEAT**.

Key support:
- many catchments exhibit nonlinear storage–baseflow relations;
- a calibrated linear reservoir should therefore be described as an effective conceptual response, not direct aquifer physics.

## Cuthbert (2014)

Cuthbert, M.O. (2014). **Straight thinking about groundwater recession.** *Water Resources Research*. DOI: **10.1002/2013WR014060**.

Evidence class: **STRUCTURAL CAVEAT**.

Key support:
- exponential recession associated with a linear-store interpretation is only one possible recession regime;
- recession form depends on aquifer diffusivity, geometry, boundaries and antecedent/recharge conditions.

Use in EGHM:
- justifies retaining linear reservoirs only as a simple effective routing representation unless site water-level recession data are available.

### Audit judgement for linear reservoirs

**KEEP FORM.** The use of fast/slow conceptual reservoirs is strongly defensible. Exact timescales and partition fractions must remain independently classified.

---

# K2. `ET_EXT = 0.95`

## Allen et al. (1998), FAO-56

Allen, R.G., Pereira, L.S., Raes, D. & Smith, M. (1998). **Crop evapotranspiration — Guidelines for computing crop water requirements.** FAO Irrigation and Drainage Paper 56.

FAO-56 dual-coefficient table gives **Conifer Trees: `Kcb_ini = Kcb_mid = Kcb_end = 0.95`** under well-watered large-forest reference conditions. FAO also explicitly cautions that conifers can exhibit substantial stomatal control and actual Kcb can fall below the tabulated well-watered value.

Evidence class: **DIRECT LITERATURE ANALOGUE FOR VALUE**.

Current EGHM interpretation:
- `ET_EXT=0.95` has a clear literature analogue if the external catchment is represented as conifer forest;
- it is not a site-measured Seoyeongari ET coefficient;
- because the code multiplies reference ETo by this constant, manuscript wording should say **FAO-56 conifer analogue**, not field calibration.

Audit judgement: **KEEP, LITERATURE ANALOGUE.**

---

# K3. `SOIL_DEPTH = 0.294 * 0.55`

## What the current code actually means

The inherited name `SOIL_DEPTH` is misleading. In the Stage35c/38 code, the quantity is:

`0.294 [m3 m-3 available-water fraction] * 0.55 [m effective rooting/profile depth] = 0.1617 m = 161.7 mm water storage capacity`.

Thus it is not a geometric soil depth of 0.1617 m. It is a **lumped external-catchment available-water storage capacity**.

The Stage24 handoff records the original calculation explicitly:

`AWC = 0.294 × root depth = 0.55 m × area 8483 m2 ≈ 1371.7 m3`, equivalent to 161.7 mm.

### Provenance status of `0.294`

Current audit has not recovered a primary Seoyeongari soil measurement or clearly documented published source showing that the external catchment AWC is exactly `0.294 m3 m-3`.

General literature supports defining available water capacity from field-capacity minus wilting-point water content, but this does **not** establish the exact 0.294 value for Seoyeongari.

Classification: **LEGACY SITE/ANALOGUE VALUE — EXACT SOURCE UNRESOLVED**.

### Provenance status of `0.55 m`

Current audit has not recovered an independent Seoyeongari rooting-depth measurement for 0.55 m.

Moreover, FAO-56 Table 22 gives **1.0–1.5 m** as a generic maximum rooting-depth range for conifer trees under its agricultural/water-balance convention. That table does not support 0.55 m as a standard conifer root depth.

This does not prove 0.55 m is physically impossible in shallow/poorly drained/volcanic soils; it means 0.55 m must **not** be attributed to FAO-56 without separate site evidence.

Classification: **LEGACY EFFECTIVE ROOT/ACTIVE-SOIL DEPTH — EXACT SOURCE UNRESOLVED**.

### Audit judgement for the product `161.7 mm`

**DO NOT PRESENT AS REFERENCE-DERIVED YET.**

The form `AWC × active depth` is physically standard, but both numerical inputs need provenance if 161.7 mm is to remain a fixed externally constrained parameter. Until then, manuscript-safe wording is:

> The external-catchment soil store was represented by a fixed 161.7-mm effective available-water capacity inherited from the hydrologic reformulation; its exact site-specific AWC/root-depth provenance remains unresolved and it is treated as a model assumption pending independent constraint.

---

# K4. `FAST_FRAC = 0.75`

## Historical trace

The Seoyeongari Stage26 hydrologic search explicitly tested fast-path fractions `0.25 / 0.50 / 0.75` while developing a two-reservoir perched-groundwater architecture. The best Stage26 setting was **0.25**, not 0.75, although that Stage26 model had other known structural deficiencies (no realistic seasonal drying and large spill).

The later Stage35c/38 implementation hard-coded `FAST_FRAC = 0.75` while separately calibrating `local_frac` and `tau_fast`.

No independent field hydrograph/baseflow separation, tracer analysis or Seoyeongari groundwater-response observation has yet been recovered that assigns 75% of local excess to the fast reservoir.

Literature such as Moore (2007) supports a proportional fast/slow split as a conceptual model choice, but **not 75% for this site**.

Classification: **LEGACY FIXED CONCEPTUAL ROUTING FRACTION / UNRESOLVED VALUE PROVENANCE**.

Audit judgement:
- **process form: defensible**;
- **exact 0.75: not independently defensible yet**;
- should be added to robustness testing or externally constrained before being described as a fixed physical parameter.

---

# K5. `TAU_SLOW = 365 d`

## Historical trace

Earlier Seoyeongari hydrologic searches examined slow-reservoir timescales broadly (approximately 180–1460 d). `365 d` subsequently became fixed in Stage35c/38 while `tau_fast` remained an explicit calibrated parameter.

No current site water-level/recession record or tracer-derived residence time has been recovered that identifies a 365-day Seoyeongari slow-store recession time.

Nash-type linear-reservoir theory supports the form `Q=S/tau`; recession literature shows the actual `tau` must depend on hydrologic properties and system scale. One year is therefore not a literature universal.

Classification: **LEGACY FIXED EFFECTIVE TIMESCALE / UNRESOLVED VALUE PROVENANCE**.

Audit judgement:
- **keep the slow-reservoir concept**;
- do not label 365 d measured/literature-derived;
- include `TAU_SLOW` in a targeted robustness test unless independent recession data are found.

---

# K6. Updated hidden-constant status table

| Constant | Current value | Process-form support | Exact-value support | Status |
|---|---:|---|---|---|
| External-catchment effective AWC fraction | 0.294 m3 m-3 | Strong generic soil-water basis | Not recovered | **Unresolved legacy value** |
| External effective root/active depth | 0.55 m | Strong generic rooting/storage basis | Not recovered; not FAO conifer default | **Unresolved legacy value** |
| Effective soil-water store | 161.7 mm | Product form physically meaningful | Depends on two unresolved inputs | **Model assumption pending constraint** |
| `ET_EXT` | 0.95 | FAO-56 ET framework | Direct conifer Kcb analogue 0.95 | **Literature analogue** |
| `FAST_FRAC` | 0.75 | Fast/slow splitting common in conceptual hydrology | No site support recovered | **Legacy conceptual value** |
| `TAU_SLOW` | 365 d | Linear/slow reservoirs well established | No site support recovered | **Legacy effective timescale** |

---

# K7. Consequence for the current model freeze decision

The discovery of these inherited constants slightly modifies the previous Stage53 conclusion.

It still does **not** justify adding more process terms. However, before declaring the parameterization fully frozen, the following low-dimensional checks are scientifically worthwhile:

1. test `FAST_FRAC` at the pre-existing values 0.25, 0.50, 0.75;
2. test `TAU_SLOW` at representative pre-existing values (e.g. 180, 365, 730 d; broader values only if needed);
3. test the effective external soil-store capacity as a single quantity rather than independently fitting AWC and root depth, unless independent site soil/root data are recovered;
4. keep `ET_EXT=0.95` fixed as an explicitly labelled FAO conifer analogue unless site ET evidence indicates otherwise.

These tests should be performed as **robustness checks**, not as a search for a smaller RMSE. Scenario ranking must not be an acceptance criterion.

If the central conclusions remain stable, the model can then be frozen with transparent parameter classifications. If conclusions depend strongly on one of these hidden legacy constants, that parameter becomes a priority for independent constraint or explicit uncertainty analysis.
