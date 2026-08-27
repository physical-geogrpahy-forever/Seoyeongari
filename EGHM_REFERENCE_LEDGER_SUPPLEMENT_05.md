# EGHM reference ledger — Supplement 05: mountain-wetland water balance, hydroperiod, vegetation feedback and encroachment

Updated: 2026-08-27

## Scope

This supplement adds Korean mountain-wetland and international process references that are directly useful for interpreting EGHM hydrologic variability, vegetation response, terrestrialization, and peat-surface change. These references strengthen the process interpretation but are not used to import site-specific parameter magnitudes into Seoyeongari.

---

# N1. Yang & Choi (2009) — Jangdo Island High Moor water balance

Yang, H.K. & Choi, T.B. (2009). **Management Considering Water Balance of Jangdo Island High Moor** [물수지를 고려한 신안장도산지습지의 관리방안]. *Journal of the Korean Geomorphological Association*, 16(4), 61–71.

Evidence class: **KOREAN MOUNTAIN-WETLAND WATER BALANCE / ECOHYDROLOGIC PROCESS**.

Key findings:
- water supply to Jangdo High Moor was interpreted as primarily precipitation-derived spring water plus moisture supply associated with sea fog;
- surrounding wetland/groundwater conditions can remain saturated even in a relatively low-rainfall regional setting because evapotranspiration and local hydrogeomorphic conditions matter;
- large interannual precipitation variability was associated with wetland drying;
- reduced groundwater level and water-budget imbalance were linked to ecological disturbance and likely expansion of willow vegetation;
- anthropogenic interception of subsurface water was identified as aggravating wetland drying.

Use in EGHM:
- Korean evidence that wetland terrestrialization/vegetation change can arise from water-budget and groundwater-level changes rather than from calendar succession alone;
- supports explicit treatment of subsurface inflow/groundwater support and interannual hydrologic variability;
- supports interpreting vegetation encroachment as a response to hydrologic state.

Limit:
- Jangdo is an island high moor with different geology/climate from Seoyeongari; no numerical flux or threshold is transferred.

---

# N2. Oh et al. (2018) — Janggun mountain wetland water balance

Oh, S.H., Kim, J.W., Chae, M.B., Bae, Y.H. & Kim, H.S. (2018). **Case study: Runoff analysis of a mountain wetland using water balance method** [물수지 방법을 이용한 산지습지의 유출 변동성 분석 — 금정산 장군습지를 대상으로]. *Journal of Wetlands Research*, 20(3), 210–218. DOI: **10.17663/JWR.2018.20.3.210**.

Evidence class: **KOREAN MOUNTAIN-WETLAND HYDROLOGY / OBSERVATION + WATER-BALANCE MODEL**.

Key findings:
- rainfall and observed wetland water level were used together with a water-balance/SWAT approach;
- in the studied Janggun wetland, positive wetland water level required sufficiently frequent rainfall, with the study reporting a site-specific example of ≥10 mm rainfall within about 8 days;
- years with relatively low rainfall experienced wetland water shortage;
- even in summer, intense but short-lived rainfall could leave water deficits when water was rapidly exported rather than sustained;
- management implications were explicitly linked to preventing drying/terrestrialization by retaining inflow and reducing rapid outflow.

Use in EGHM:
- strong domestic evidence that **rainfall amount alone is insufficient**: event timing, antecedent interval, storage and drainage govern wetland water level;
- supports the decision to use daily forcing and explicit storage/drainage rather than annual rainfall totals or a fitted time trend;
- supports a causal antecedent-hydrology concept.

Critical limit:
- the reported `10 mm / 8 d` threshold is Janggun-specific and must **not** be used to justify EGHM `est_window=7 d` or `hydro_window=60 d`.

---

# N3. Seo, Keum & Kim (2025) — Korean mountain-wetland ecohydrologic modelling

Seo, J., Keum, J. & Kim, S. (2025). **Eco-hydrologic model for assessing the climate and hydrologic elasticity of vegetation in mountain wetlands.** *Geoscience Letters*, 12, 55. DOI: **10.1186/s40562-025-00429-y**.

Evidence class: **KOREAN MOUNTAIN-WETLAND ECOHYDROLOGIC MODEL / DIRECT STRUCTURAL ANALOGUE**.

Key support:
- models mountain-wetland hydrology using explicit precipitation, direct wetland inflow, overflow, wetland evapotranspiration, groundwater exchange and baseflow components;
- explicitly incorporates vegetation into the hydrologic modelling framework;
- vegetation in studied wetlands was strongly associated with soil moisture and groundwater-related variables;
- presence/absence of vegetation measurably altered hydrologic fluxes, including groundwater exchange and overflow;
- different wetland depth/storage configurations exhibited different sensitivities to precipitation, PET and groundwater exchange;
- seasonal analysis showed that climate and hydrologic controls on vegetation are not temporally uniform.

Use in EGHM:
- highly relevant recent Korean support for an **integrated vegetation–hydrology wetland model**, rather than treating vegetation as a post hoc correction;
- supports keeping precipitation, ET, groundwater exchange, overflow/drainage and storage as separate flux/state terms;
- reinforces the scientific motivation for comparing hydrologic-only and integrated ecohydrologic scenarios.

Important distinctions:
- EGHM is not a reproduction of the Seo et al. model;
- their model structure/parameters must not be imported directly;
- their findings support the coupled-process concept, not exact Seoyeongari coefficients.

---

# N4. Wallace et al. (2024) — wetland daily water balance from weather + depth

Wallace, J., Nicholas, M., Grice, A. & Waltham, N.J. (2024). **Application of a water balance model using depth measurements in the Mungalla wetland in north Queensland, Australia.** *Journal of Hydrology*, 644, 132055. DOI: **10.1016/j.jhydrol.2024.132055**.

Evidence class: **DIRECT WETLAND WATER-BALANCE METHOD**.

Key support:
- demonstrates a daily wetland water-balance model using meteorological forcing and wetland depth observations;
- shows large within-year and between-year variability in water-balance components;
- emphasizes that complete direct measurement of all wetland inflows/outflows is often impractical and that parsimonious water-balance models can estimate dominant fluxes when carefully constrained.

Use in EGHM:
- modern support for daily wetland water-budget modelling under sparse direct flux observations;
- supports interpreting year-to-year pond-area variability mechanistically rather than via annual empirical relaxation.

Limit:
- tropical floodplain wetland analogue; no parameter values are transferable to Seoyeongari.

---

# N5. Saintilan & Rogers (2015) — woody encroachment in wetlands

Saintilan, N. & Rogers, K. (2015). **Woody plant encroachment of grasslands: a comparison of terrestrial and wetland settings.** *New Phytologist*, 205(3), 1062–1070. DOI: **10.1111/nph.13147**.

Evidence class: **VEGETATION ENCROACHMENT REVIEW**.

Key support:
- woody encroachment is documented in freshwater and intertidal wetland settings as well as terrestrial grasslands;
- global drivers interact with local hydrology and other site processes to control woody recruitment/expansion;
- vegetation expansion can reinforce new ecosystem states through feedbacks.

Use in EGHM:
- supports treating woody/terrestrial vegetation entry into a wetland margin as an ecologically recognized state transition process;
- useful Discussion support for the observed Seoyeongari wetland-to-terrestrial vegetation gradient.

Does not support:
- irreversible occupation under all circumstances;
- exact recruitment rate or exposure threshold;
- a claim that woody encroachment is driven by hydrology alone.

---

# N6. Regan et al. (2019) — groundwater drainage, peat subsidence and ecology

Regan, S., Flynn, R., Gill, L., Naughton, O. & Johnston, P. (2019). **Impacts of Groundwater Drainage on Peatland Subsidence and Its Ecological Implications on an Atlantic Raised Bog.** *Water Resources Research*, 55(7), 6153–6168. DOI: **10.1029/2019WR024937**.

Evidence class: **LONG-TERM FIELD HYDROGEOLOGY / SURFACE-ELEVATION CAVEAT**.

Key support:
- 28-year field observations linked groundwater drainage to changes in peat hydraulic properties and peat-surface subsidence;
- peat compression changed hydraulic conductivity and storativity;
- regional groundwater pressure can act as an environmental supporting condition for peatland water tables;
- hydrologic alteration can change surface morphology and thereby ecological conditions.

Use in EGHM:
- reinforces that hydrology and geomorphic surface elevation can be coupled over time;
- strengthens the caveat that peat-surface elevation is not governed solely by positive peat accumulation: compression/subsidence can also contribute;
- supports not interpreting `peat accumulation rate` as a direct measured surface-elevation-change rate.

Domain caveat:
- Atlantic raised bog affected by drainage is not a direct analogue for undrained Seoyeongari; use for process interpretation only.

---

# N7. Updated support for EGHM design choices

| EGHM design choice | New supporting references | Strength |
|---|---|---|
| Daily rather than annual water balance | Oh et al. 2018; Wallace et al. 2024 | **Strong method/process support** |
| Storage/drainage matter in addition to rainfall amount | Yang & Choi 2009; Oh et al. 2018 | **Strong Korean support** |
| Explicit groundwater exchange/support | Yang & Choi 2009; Seo et al. 2025; Regan et al. 2019 | **Strong process support** |
| Vegetation and hydrology should be coupled | Seo et al. 2025; Saintilan & Rogers 2015 | **Strong concept support** |
| Wetland depth/storage geometry changes sensitivity | Seo et al. 2025; Hayashi & van der Kamp 2000 | **Strong form support** |
| Peat accumulation != net surface elevation change | Regan et al. 2019; Cahoon 2024 | **Strong caveat** |
| Hydrologic drying can promote vegetation-state change | Yang & Choi 2009; Saintilan & Rogers 2015 | **Strong general support; site rate not constrained** |

---

# N8. Implications for current diagnostics

These references make one model diagnostic particularly important: **seasonal timing of visible surface-water disappearance**.

The literature supports that wetland ecological condition depends on water-level duration, rainfall timing, storage, groundwater support and drainage. Consequently, matching only six May–June open-water-area observations is insufficient evidence that the simulated daily hydroperiod is realistic.

For Seoyeongari, the independently known spring disappearance behaviour should therefore be retained as a **non-fitted process diagnostic**. It should not automatically become another calibration objective because doing so with sparse qualitative evidence could encourage overfitting.

A useful final audit should compare:
- annual number of days with zero visible surface storage;
- March–April concentration of disappearance days;
- onset of drawdown and reflooding timing;
- whether subsurface/soil stores remain active when visible surface water disappears.

This diagnostic is especially valuable when robustness-testing unresolved `FAST_FRAC`, `TAU_SLOW`, and effective soil-storage capacity.
