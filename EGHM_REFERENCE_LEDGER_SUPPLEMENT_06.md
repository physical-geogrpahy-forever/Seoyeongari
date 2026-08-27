# EGHM reference ledger — Supplement 06: meteorological forcing, radiation, evapotranspiration and open-water evaporation

Updated: 2026-08-27

## Scope

This supplement audits the meteorological equations actually inherited by the current Stage49+ EGHM. Stage49 imports `forcing` from `stage31_topmodel_vsa.py`, which in turn imports the forcing implementation from `stage30_macro_head_drainage_fast.py`. Therefore the current model still uses the Stage30 meteorological calculation chain even though the later hydrological state equations have been extensively replaced.

The audit distinguishes published equations, literature-based parameter choices, and site/station data choices.

---

# O1. Current forcing implementation — code trace

The active forcing chain computes:

- extraterrestrial radiation and daylight duration from latitude/day-of-year;
- solar radiation from sunshine duration using the Ångström–Prescott relation;
- clear-sky radiation with elevation correction;
- net longwave radiation from FAO-56;
- reference vegetation ETo with FAO-56 Penman–Monteith;
- open-water evaporation with the Penman/Shuttleworth SI combination equation;
- daily AWS precipitation, temperature and wind plus ASOS sunshine duration.

Current constants inherited by Stage49:

- latitude = 33.30456°
- station elevation = 188.42 m
- `a_s = 0.25`
- `b_s = 0.50`
- vegetation/reference albedo = 0.23
- open-water albedo = 0.08
- external-catchment ET factor = 0.95

The current Stage49 hydrology no longer uses many legacy annual-model factors such as the old 0.80 pond-evaporation multiplier inside the Stage30 simulator; it uses the forcing product `ep` as the open-water evaporation input in the later mass-conserved hydrology. The meteorological calculation of `ep` itself, however, remains inherited.

---

# O2. Allen et al. (1998) — FAO-56 reference evapotranspiration

Allen, R.G., Pereira, L.S., Raes, D. & Smith, M. (1998). **Crop evapotranspiration — Guidelines for computing crop water requirements.** FAO Irrigation and Drainage Paper 56. Food and Agriculture Organization of the United Nations, Rome.

Evidence class: **DIRECT METHOD / PUBLISHED EQUATIONS**.

The current forcing uses the FAO-56 forms for:

- saturation vapour pressure `e°(T)`;
- slope of the saturation vapour-pressure curve `Δ`;
- atmospheric pressure as a function of station elevation;
- psychrometric constant;
- wind-speed conversion to 2 m;
- extraterrestrial radiation `Ra`;
- inverse relative Earth–Sun distance;
- solar declination;
- sunset hour angle and daylight duration;
- clear-sky radiation `Rso`;
- net longwave radiation `Rnl`;
- FAO Penman–Monteith reference ETo.

Audit judgement: **STRONG / KEEP**.

---

# O3. Ångström–Prescott solar radiation: `a_s = 0.25`, `b_s = 0.50`

Current relation:

`Rs = (a_s + b_s n/N) Ra`

with:

- `a_s = 0.25`
- `b_s = 0.50`.

FAO-56 / FAO ETo documentation gives **0.25 and 0.50 as the default coefficients** when site-specific solar-radiation calibration is not available. The model uses measured sunshine duration from ASOS station 189 and applies these defaults.

Evidence class: **DIRECT METHOD + DIRECT DEFAULT VALUES**.

Audit judgement: **KEEP AS FAO DEFAULTS**.

Manuscript wording:

> Incoming shortwave radiation was estimated from measured sunshine duration using the Ångström–Prescott relation with the FAO default coefficients `a_s=0.25` and `b_s=0.50`.

Do not describe these as coefficients calibrated to Seoyeongari unless a local pyranometer calibration is actually performed.

---

# O4. Reference-surface albedo `0.23`

FAO-56 defines the reference evapotranspiration surface as a hypothetical well-watered grass reference with an albedo of **0.23**.

Evidence class: **DIRECT METHOD / DIRECT VALUE**.

Current code:

`Rn_veg = (1 - 0.23) Rs - Rnl`.

Audit judgement: **KEEP**.

Important interpretation:
- 0.23 belongs to the reference ETo surface used by FAO-56;
- it is not a measured albedo of the Seoyeongari surrounding forest.

The later multiplication by an external vegetation coefficient is the step that maps reference ETo toward the external-catchment vegetation analogue.

---

# O5. Open-water albedo: current `alpha_water = 0.08`

## Code/provenance trace

The current Stage30 forcing uses:

`Rn_water = (1 - 0.08) Rs - Rnl`.

This value was **not introduced accidentally during Stage49 reconstruction**. File-Library recovery of the authoritative v5 optimizer and final R implementation confirms that both already used:

`alpha_water = 0.08`.

The earlier equation-reference audit also explicitly classified Eq. 8 as:

`R_ns,w = (1-alpha_w) Rs, alpha_w=0.08`

and recommended retaining it with Shuttleworth (1993) as the reference.

## Literature context

Open-water shortwave albedo is not one universal constant. Literature values commonly lie around **0.04–0.08**, varying with solar angle, cloud conditions, turbidity and surface state.

Relevant evidence:

- Shuttleworth (1993), *Handbook of Hydrology*, gives/recommends approximately **0.08** as a practical open-water albedo for hydrologic evaporation calculations; numerous later Penman implementations follow this convention.
- Valiantzas-type / lake-evaporation studies also use 0.08 in the open-water radiation balance.
- Other lake-energy-balance studies use approximately **0.06** (e.g., Henderson-Sellers/Brutsaert-derived convention; Liu et al. 2009).

Evidence class: **LITERATURE-BASED PARAMETER CHOICE**.

Audit judgement: **KEEP 0.08**.

Why this is not a current correction:
- 0.08 is within the accepted open-water range;
- it is traceable to the original authoritative model and a published Penman/Shuttleworth convention;
- changing it to 0.06 merely because 0.06 is also common would substitute one literature convention for another without site albedo measurements.

Manuscript wording:

> Open-water net shortwave radiation was calculated using an albedo of 0.08 following the Shuttleworth open-water Penman convention; this value is a literature analogue rather than a site-measured albedo.

Optional robustness note:
- a 0.06–0.08 albedo check could be performed cheaply if desired, but it is lower priority than the unresolved inherited storage/routing constants because both values are physically accepted open-water choices.

---

# O6. Penman open-water evaporation

## Penman (1948)

Penman, H.L. (1948). **Natural evaporation from open water, bare soil and grass.** *Proceedings of the Royal Society of London A*, 193, 120–145. DOI: **10.1098/rspa.1948.0037**.

Evidence class: **DIRECT FOUNDATIONAL METHOD**.

Supports the combination of energy and aerodynamic terms for open-water evaporation.

## Shuttleworth (1993)

Shuttleworth, W.J. (1993). **Evaporation.** In: Maidment, D.R. (ed.), *Handbook of Hydrology*, McGraw-Hill, Chapter 4.

Evidence class: **DIRECT IMPLEMENTATION FORM / SI CONVENTION**.

The current code uses the Shuttleworth-style SI Penman form with aerodynamic wind function:

`6.43 (1 + 0.536 u2)`.

Audit judgement: **KEEP**.

## Harwell (2012), USGS SIR 2012-5202

Harwell, G.R. (2012). **Estimation of evaporation from open water — A review of selected studies, summary of U.S. Army Corps of Engineers data collection and methods, and evaluation of two methods for estimation of evaporation from five reservoirs in Texas.** USGS Scientific Investigations Report 2012–5202. DOI: **10.3133/sir20125202**.

Evidence class: **OPEN-WATER EVAPORATION REVIEW / METHOD CONTEXT**.

Supports:
- the need to represent open-water evaporation separately from terrestrial reference ET;
- Penman-type combination methods as established approaches when adequate meteorological inputs are available;
- the fact that energy-storage terms become increasingly important for large/deep water bodies.

Seoyeongari implication:
- Seoyeongari is a very small/shallow seasonal pool, so a Penman meteorological open-water approach is more defensible than importing large-reservoir thermal-storage parameters.

---

# O7. Actual vapour pressure approximated from `Tmin`

Current code uses:

`ea = e°(Tmin)`

rather than directly measured relative humidity/dewpoint.

FAO-56 explicitly permits estimating actual vapour pressure by assuming:

`Tdew ≈ Tmin`

when humidity/dewpoint observations are unavailable or unreliable, particularly outside arid conditions. FAO cautions that this approximation can be biased in arid environments where the air is not saturated near Tmin.

Evidence class: **DIRECT FAO MISSING-DATA METHOD**.

Audit judgement: **METHOD DEFENSIBLE, DATA-LIMITATION CAVEAT**.

Manuscript wording:

> Because daily humidity/dew-point data were unavailable in the forcing series, actual vapour pressure was approximated using the FAO-56 missing-data assumption `Tdew ≈ Tmin`.

Do not describe `ea=e°(Tmin)` as a measured humidity series.

Potential future improvement:
- if a complete nearby humidity record becomes available, recomputing `ea` directly would be a scientifically meaningful forcing upgrade that does **not** add a fitted coefficient.

---

# O8. Wind-speed conversion

Current code converts measured wind speed at height `z` to the standard 2-m height with:

`u2 = uz * 4.87 / ln(67.8 z - 5.42)`.

This is FAO-56 Eq. 47.

Evidence class: **DIRECT METHOD**.

Audit judgement: **KEEP**.

Current implementation sets `wind_height_m = 2`, so if the AWS wind observation is already a true 2-m wind observation, this conversion is almost identity. The station metadata should remain archived so that measurement height is reproducible.

---

# O9. Station elevation in atmospheric-pressure calculation

Current pressure calculation uses `z = 188.42 m`, the meteorological-station elevation associated with the forcing data, rather than the approximately 634-m wetland elevation.

For FAO meteorological calculations this is the correct conceptual choice **if the temperature/wind observations are being treated as station observations**, because pressure and the psychrometric constant belong to the conditions at which the meteorological forcing was observed.

Audit judgement: **KEEP; CLARIFY IN METHODS**.

Do not call 188.42 m the Seoyeongari site elevation.

If meteorological forcing were ever lapse-corrected/transferred physically to the wetland elevation, the pressure/radiation treatment should be revisited consistently rather than changing elevation alone.

---

# O10. `ET_EXT = 0.95`: exact terminology correction

The current hydrology uses:

`ET_external = min(storage, 0.95 * ETo * area)`.

FAO-56 contains two related but different conifer coefficients:

- **dual-coefficient Table 17 basal coefficient `Kcb ≈ 0.95`** for conifer trees;
- **single-coefficient table `Kc ≈ 1.00`** for conifer trees under the stated standard conditions.

Therefore the current 0.95 value has a clear FAO analogue, but the precise wording matters.

Evidence class: **LITERATURE ANALOGUE FOR VALUE**.

Manuscript-safe wording:

> External-catchment vegetation evapotranspiration was scaled from FAO reference ETo using a fixed coefficient of 0.95, corresponding to the FAO-56 conifer basal-coefficient analogue.

Avoid:

> FAO-56 states that the conifer crop coefficient is universally 0.95.

The latter is false because the tabulated value depends on whether basal or single crop-coefficient convention is being used.

Audit judgement: **KEEP 0.95, FIX TERMINOLOGY**.

---

# O11. Root-depth implication for the inherited 161.7-mm soil store

FAO-56 Table 22 lists a generic maximum effective rooting depth of approximately **1.0–1.5 m for conifer trees**. Therefore FAO-56 cannot be used to justify the current inherited `0.55 m` active/root-depth term used in:

`0.294 × 0.55 = 0.1617 m = 161.7 mm`.

This audit reinforces Supplement 02:

- the **form** `available-water fraction × effective active depth` is physically standard;
- `0.294` remains source-unresolved;
- `0.55 m` remains source-unresolved;
- the product 161.7 mm should remain classified as a **legacy effective soil-storage assumption**, not an FAO-derived conifer root-zone capacity.

A waterlogged or shallow-rooted forest can physically have a shallower effective root zone than the FAO generic maximum; that possibility must be established with site soil/root information, not inferred from the FAO table.

---

# O12. Current forcing audit table

| Item | Current implementation | Evidence status | Action |
|---|---|---|---|
| FAO Penman–Monteith ETo | FAO-56 equations | **Direct published method** | Keep |
| `a_s=0.25`, `b_s=0.50` | FAO defaults | **Direct default values** | Keep; say defaults |
| reference albedo 0.23 | FAO reference surface | **Direct value** | Keep |
| open-water albedo 0.08 | Shuttleworth/Penman hydrology convention | **Literature-based value** | Keep; not site-measured |
| Open-water Penman equation | Penman 1948 + Shuttleworth SI form | **Direct method** | Keep |
| `ea=e°(Tmin)` | FAO missing-humidity approximation | **Direct fallback method** | Keep with data caveat |
| wind conversion to 2 m | FAO Eq. 47 | **Direct method** | Keep |
| station elevation 188.42 m | forcing-station metadata | **Data/provenance choice** | Keep; distinguish from site elevation |
| external ET factor 0.95 | FAO conifer **basal** Kcb analogue | **Literature analogue** | Keep; correct terminology |
| inherited 0.55-m root/active depth | not FAO conifer default | **Unresolved exact value** | Remains robustness/provenance priority |

---

# O13. Net conclusion

The current meteorological forcing is one of the stronger parts of the EGHM reference chain. Most equations are directly traceable to FAO-56 or Penman/Shuttleworth.

The apparent 0.06-vs-0.08 water-albedo discrepancy has been resolved:

- `0.08` is the actual value in the original authoritative v5 optimizer and final R implementation;
- `0.08` is a recognized Shuttleworth open-water convention;
- `0.06` is another common literature value, not evidence that the current 0.08 is erroneous.

Therefore **no forcing-structure modification is recommended from this audit**.

The remaining high-value uncertainty is not the radiation/evaporation equation set but the inherited external soil-water storage and hidden fast/slow routing constants identified in Supplement 02.
