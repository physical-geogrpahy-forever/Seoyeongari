# EGHM reference ledger — Supplement 07: vegetation persistence, hydrologic recovery and the Stage49 no-fitted-reversal assumption

Updated: 2026-08-27

## Scope

Stage49 removed the fitted flood-reversal coefficient after earlier calibration repeatedly pushed it toward extremely small values corresponding to century-to-millennial reversal timescales. The current ecological state therefore accumulates under qualifying exposure and is not explicitly reduced by ordinary seasonal reflooding.

This supplement audits what that assumption can and cannot mean biologically.

---

# P1. Slusher, Vepraskas & Broome (2014) — species-specific response to long ponding

Slusher, C.E., Vepraskas, M.J. & Broome, S.W. (2014). **Evaluating Responses of Four Wetland Plant Species to Different Hydroperiods.** *Journal of Environmental Quality*, 43, 723–731. DOI: **10.2134/jeq2013.06.0227**.

Evidence class: **DIRECT HYDROPERIOD–VEGETATION RESPONSE EXPERIMENT**.

Experimental structure:
- wetland tree species were exposed to contrasting hydroperiod treatments including approximately 100 d continuous ponding, 14 d intermittent ponding, and unsaturated conditions;
- species differed strongly in tolerance.

Key findings:
- bald cypress and sweet bay adapted comparatively well to 100 d ponding;
- pond pine and swamp chestnut oak were much less tolerant, with high mortality under continuous ponding;
- hydroperiod requirements therefore differ among wetland plant species and communities.

Use in EGHM:
- strongly supports hydroperiod as a causal ecological driver;
- **does not support literal ecological irreversibility**;
- shows why adding a universal flood-mortality coefficient would also be scientifically weak: mortality/reversal depends strongly on species and hydroperiod severity.

Implication for Stage49:
- the Stage49 state must not be interpreted as survival of every established individual under unlimited inundation;
- it is more defensible as a **persistent occupation/terrestrialization state variable** representing area that has undergone sustained establishment and associated habitat/surface change over the 13-y study horizon.

---

# P2. Bartholomew, Anderson & Berkowitz (2020) — vegetation response lags hydrologic recovery

Bartholomew, M.K., Anderson, C.J. & Berkowitz, J.F. (2020). **Wetland Vegetation Response to Groundwater Pumping and Hydrologic Recovery.** *Wetlands*, 40, 2609–2619. DOI: **10.1007/s13157-020-01383-5**.

Evidence class: **LONG-TERM FIELD HYDROLOGY + VEGETATION RECOVERY**.

Key findings:
- decades of groundwater withdrawal produced wetlands with different degrees of hydrologic alteration;
- after pumping reductions, vegetation showed detectable response during a 5–7 y post-recovery period;
- even after hydrologic improvement, the most altered wetland communities often remained compositionally different from the least altered wetlands;
- the authors note that vegetation recovery can take **years to decades**, and short (<5 y) monitoring periods may not capture full trajectories;
- less inundation-tolerant species can persist while more wetland-adapted species recruit following hydrologic recovery.

Use in EGHM:
- supports ecological **hysteresis / state persistence** after hydrologic conditions change;
- supports using a slow ecological state distinct from instantaneous surface-water area;
- supports the idea that ordinary short-term rewetting need not instantaneously erase an established terrestrialized/altered community state.

Important limitation:
- this evidence does not imply permanent irreversibility; substantial long-term hydrologic recovery can alter community composition.

---

# P3. Webb, Wallis & Stewardson (2012)

Webb, J.A., Wallis, E.M. & Stewardson, M.J. (2012). **A systematic review of published evidence linking wetland plants to water regime components.** *Aquatic Botany*, 103, 1–14. DOI: **10.1016/j.aquabot.2012.06.003**.

Evidence class: **SYSTEMATIC REVIEW / HYDROLOGIC ECOLOGY**.

Supports:
- depth, duration, frequency and timing of inundation/waterlogging affect establishment, growth, reproduction and vegetation composition;
- plant response cannot generally be collapsed to one universal inundation threshold or mortality coefficient.

Use in EGHM:
- reinforces both parts of the current decision:
  1. recruitment should be conditional on hydrologic exposure;
  2. without species/site information, a fitted universal `r_flood` would not be a well-constrained ecological constant.

---

# P4. Casanova & Brock (2000)

Casanova, M.T. & Brock, M.A. (2000). **How do depth, duration and frequency of flooding influence the establishment of wetland plant communities?** *Plant Ecology*, 147, 237–250. DOI: **10.1023/A:1009875226637**.

Evidence class: **DIRECT HYDROPERIOD–ESTABLISHMENT FORM**.

Supports:
- establishment windows and community development depend on flooding regime;
- temporary drawdown/exposure can enable terrestrial or mudflat-associated recruitment that would not establish under persistent flooding.

Use in EGHM:
- strong support for using antecedent continuous exposure to generate recruitment pressure.

Does not establish:
- 7 d as a universal threshold;
- permanent survival after later reflooding.

---

# P5. van der Valk (1981) — wetland succession and establishment requirements

van der Valk, A.G. (1981). **Succession in Wetlands: A Gleasonian Approach.** *Ecology*, 62, 688–696. DOI: **10.2307/1937737**.

Evidence class: **WETLAND SUCCESSION THEORY**.

Supports:
- community change can be modelled through species-specific propagule availability and establishment requirements;
- succession is contingent on environmental change rather than a fixed calendar sequence.

Use in EGHM:
- conceptual support for the move away from legacy fixed-time succession toward water-regime-conditioned occupation.

---

# P6. Stage49 removal of `r_flood`: scientific interpretation

## What the calibration history showed

Earlier Stage40–48 formulations included a fitted flood-reversal/mortality-like term. Searches drove the fitted rate toward values such as approximately `0.0005 yr-1`, which imply reciprocal timescales on the order of 2000 years under the simple first-order interpretation.

That is not a meaningful estimate of seasonal reflooding mortality. It indicates that, given the six pond-area targets and the then-current model structure, the data did not identify a useful positive reversal coefficient.

## What literature says

The literature shows **both**:
- established wetland/upland vegetation can persist and community recovery can lag hydrologic restoration for years to decades;
- sufficiently prolonged/deep inundation can kill flood-intolerant species, with response highly species dependent.

Therefore neither of these extremes is defensible:

1. `r_flood > 0` must always be fitted because plants can die under flooding — **not defensible without site/species mortality data**;
2. established vegetation is biologically immortal — **also not defensible**.

## Current defensible interpretation

The Stage49 ecological variable should be defined as:

> a bounded cumulative **persistent occupation / terrestrialization state** of portions of the 2011 open-water footprint that experienced qualifying continuous exposure.

It is an effective landscape-state variable, not a count of living individual plants.

Ordinary seasonal reflooding:
- stops or reduces new qualifying exposure and therefore suppresses additional recruitment;
- does not automatically reset the cumulative occupation state.

The model does **not** assert that extreme/prolonged inundation could never reverse terrestrialization. Such reversal is simply not parameterized because the current Seoyeongari data set does not independently constrain its magnitude.

---

# P7. Is a new mortality/reversal process currently warranted?

**No.** The literature alone is insufficient to add a new fitted reversal parameter.

A scientifically useful reversal term would require at least one of:

- repeated mapped vegetation-boundary retreat after major re-inundation events;
- species-specific mortality/survival observations;
- multi-year vegetation cover/composition time series;
- independent hydrologic restoration/reflooding episode showing measurable reversal;
- repeated drone/field evidence of previously colonized area returning to persistent open water.

Without such information, adding a new fitted `r_flood` increases equifinality and risks recreating the near-zero arbitrary parameter that Stage49 intentionally removed.

---

# P8. Manuscript-safe terminology

### Preferred

> Vegetation encroachment was represented by a bounded cumulative occupation state triggered by sustained exposure. Seasonal reflooding prevented additional exposure-driven recruitment but did not automatically reset previously established occupation, reflecting the persistence and hysteresis of wetland vegetation states over multi-year timescales. The model does not assume universal biological immortality; explicit flood-induced mortality was omitted because no site-specific reversal rate was independently constrained.

### Avoid

> Once vegetation establishes it can never die.

> Flooding has no effect on established vegetation.

> Wetland succession is irreversible by definition.

All three overstate what the current model and literature support.

---

# P9. Consequence for model status

This audit **does not require a structural change** to Stage49.

It does require a semantic correction in final documentation:

- call `S` a persistent occupation/terrestrialization state, not simply “vegetation amount”;
- state explicitly that the lack of a reversal term is a parsimonious modelling choice under insufficient reversal observations;
- retain the old flood-reversal experiments as a documented negative result demonstrating non-identifiability rather than hiding them.

This interpretation is more defensible than either forcing a tiny fitted mortality coefficient or claiming literal ecological irreversibility.
