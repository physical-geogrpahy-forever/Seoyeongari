# EGHM reference ledger — Supplement 03: Jeju volcanic-island wetland hydrology and perched-water evidence

Updated: 2026-08-27

## Scope

This supplement prioritizes Jeju-specific field and regional evidence for the hydrological architecture used in the current Seoyeongari EGHM. Its purpose is to reduce reliance on prairie-wetland or generic groundwater analogues when a Jeju volcanic-island process reference exists.

The references below support **process plausibility and structural form**. Except where explicitly stated, they do not provide the exact numerical values of `local_frac`, `FAST_FRAC`, `tau_fast`, `TAU_SLOW`, or `k_gw` used in the current model.

---

# L1. Kim (2009) — formation of Jeju montane wetlands by local impermeability

Kim, T. (김태호) (2009). **Geomorphic Characteristics of 1100 Highland, and Mulyeongari-oreum, Wetlands in Jeju Island** [제주도 산지 습지의 지형 특성 — 1100고지 습지와 물영아리오름 습지를 사례로]. *Journal of the Korean Geomorphological Association* [한국지형학회지], 16(4), 35–45.

Evidence class: **JEJU WETLAND / DIRECT REGIONAL GEOMORPHIC PROCESS**.

Key findings:
- 1100 Highland Wetland occurs on a concave gentle slope surrounded by volcanic landforms, but the decisive retention condition includes **locally impermeable surface geology**;
- Mulyeongari-oreum Wetland occurs despite the inherently high permeability of a scoria cone because fine materials accumulated on the crater floor and/or local subsurface impervious bedding is present;
- the rarity of crater wetlands among hundreds of Jeju scoria cones emphasizes that high-permeability volcanic terrain alone does not determine wetland occurrence; local geomorphic and low-permeability controls matter.

Use in EGHM:
- strong Jeju-specific support for representing a small wetland as hydrologically distinct from the surrounding permeable volcanic terrain;
- supports the assumption that water can be temporarily retained and laterally redistributed by local low-permeability material rather than immediately joining deep regional groundwater.

Does **not** determine:
- Seoyeongari `local_frac`;
- reservoir time constants;
- a site-specific leakage rate.

---

# L2. Ahn et al. (2017) — multi-shingle groundwater model and 1100 Highland Wetland

Ahn, U.S., Jeon, Y., Ki, J.S., Kim, G.P., Koh, S.H., Lee, B.C. & Jung, C.Y. (2017). **Proposal of new groundwater model through field observations in Jeju Island, Korea** [야외지질학적 관찰을 통한 제주도 지하수 모델 제안]. *Journal of the Geological Society of Korea*, 53(2), 347–360. DOI: **10.14770/jgsk.2017.53.2.347**.

Evidence class: **JEJU FIELD HYDROGEOLOGY / DIRECT REGIONAL PROCESS**.

Key findings directly relevant to EGHM:
- impermeable clay-rich sediment layers occur between permeable lava units and can strongly regulate groundwater occurrence and flow;
- field exposure at Suwolbong shows groundwater moving through permeable volcanic material and then being diverted laterally above a relatively impermeable clay-rich formation;
- borehole records show repeated clay-rich sediment layers between lava flows, supporting multiple vertically separated storage horizons;
- in the western highlands, the Bulreoreum–1100 Wetland–Sumeunbeongdwi wetland area has clay-rich wetland-floor deposits that limit downward infiltration and promote surface/lateral flow;
- the paper proposes that infiltrated rainwater may collect above impermeable layers, move along their topographic gradient, form local aquifers, and later leak or connect to deeper aquifers.

Use in EGHM:
- this is the strongest Jeju-specific conceptual support for separating infiltrated catchment water into a **local/perched return pathway** and a **deeper/regional loss pathway**;
- supports a hierarchy of short and longer subsurface residence/storage components in volcanic terrain;
- supports explicit lateral return from local storage to a wetland depression rather than routing all recharge directly to deep groundwater.

Important limitation:
- the multi-shingle model is a regional conceptual hydrogeological model. It does not imply that the current EGHM's two linear reservoirs are a literal geological representation of two measured Seoyeongari aquifers.

---

# L3. Koh et al. (2012) — isotopic separation of local perched and regional groundwater

Koh, E.-H., Kaown, D., Mayer, B., Kang, B.-R., Moon, H.S. & Lee, K.-K. (2012). **Hydrogeochemistry and Isotopic Tracing of Nitrate Contamination of Two Aquifer Systems on Jeju Island, Korea.** *Journal of Environmental Quality*, 41(6), 1835–1845. DOI: **10.2134/jeq2011.0417**.

Evidence class: **JEJU FIELD HYDROGEOLOGY / ISOTOPIC PROCESS EVIDENCE**.

Key findings:
- the Gosan area contains a **perched aquifer above an impermeable clay bed** and a deeper regional groundwater system beneath it;
- stable-water isotopes indicate that the perched groundwater is recharged by **local precipitation**;
- regional groundwater is instead predominantly associated with regional flow from the adjacent mountainous area.

Use in EGHM:
- unusually strong independent evidence that Jeju infiltration does not have to behave as one homogeneous groundwater pool;
- supports the conceptual distinction between locally recycled/perched water and deeper/regional groundwater loss;
- strengthens the physical interpretation of `local_frac` as a partition of soil-capacity excess into a local return system, rather than a fraction of total island recharge.

Does **not** set the current `local_frac = 0.45` value.

---

# L4. Jung et al. (2014) — impermeable layer and shallow perched aquifer in basalt

Jung, H.W., Yun, S.T., Kim, K.H., Oh, S.S. & Kang, K.G. (2014). **Role of an impermeable layer in controlling groundwater chemistry in a basaltic aquifer beneath an agricultural field, Jeju Island, South Korea.** *Applied Geochemistry*, 45, 82–93. DOI: **10.1016/j.apgeochem.2014.03.008**.

Evidence class: **JEJU FIELD HYDROGEOLOGY**.

Key finding:
- in western Jeju, an impermeable clay-rich Gosan Formation inhibits direct downward rainwater recharge and permits a **shallow perched aquifer** to form above the basaltic regional aquifer.

Use in EGHM:
- independent peer-reviewed corroboration of the low-permeability-layer / perched-storage mechanism used to justify local subsurface retention and return.

---

# L5. Park et al. (2014) — island-scale water balance and high hydraulic heterogeneity

Park, C., Seo, J., Lee, J., Ha, K. & Koo, M.-H. (2014). **A distributed water balance approach to groundwater recharge estimation for Jeju volcanic island, Korea.** *Geosciences Journal*, 18(2), 193–207. DOI: **10.1007/s12303-013-0063-6**.

Evidence class: **JEJU REGIONAL WATER-BALANCE CONTEXT**.

Key findings:
- Jeju's highly permeable volcanic surface makes groundwater recharge a major water-budget component;
- the modelled island water budget includes substantial evapotranspiration, runoff, and groundwater recharge rather than a single dominant surface-flow pathway;
- calibrated zonal hydraulic conductivity spans orders of magnitude, demonstrating strong hydrogeological heterogeneity.

Use in EGHM:
- regional support for explicit deep/recharge loss from the wetland catchment and for avoiding a single universal volcanic-rock conductivity interpretation;
- supports the decision that not all infiltrated catchment water should be returned to the local pond.

Critical limit:
- island-wide recharge/runoff percentages from this study must **not** be copied into the Seoyeongari `local_frac` or `k_gw` parameters. Scale, terrain, soil, climate period, and groundwater system differ.

---

# L6. Ahn & Kim (2015) — Jeju mid-mountain rainfall storage and water balance

Ahn, J.G. & Kim, T. (안중기·김태호) (2015). **A Hydrogeomorphological Approach to Water-use Facilities in the Mid-mountainous Region of Jeju Island** [제주도 중산간지대의 지표수 이용시설에 대한 수문지형학적 접근]. *Journal of the Korean Geomorphological Association*, 22(1), 17–27. DOI: **10.18339/jkga.2015.22.1.17**.

Evidence class: **JEJU MID-MOUNTAIN SURFACE/SUBSURFACE HYDROLOGY**.

Key findings:
- depressions and microtopographic lows on lava surfaces can hold rainfall-derived surface water where impermeable lava surfaces or local structures limit infiltration;
- studied storage sites received both direct rainfall and temporary-channel surface inflow;
- catchment water balance showed large deep-percolation and ET fractions and very small long-term surface runoff, illustrating strong partitioning in Jeju volcanic terrain.

Use in EGHM:
- useful analogue for the coexistence of direct pond rainfall, episodic surface/lateral inflow, and major deep losses in Jeju mid-mountain terrain;
- reinforces the need to keep surface, local subsurface, and deep-loss pathways separate.

Critical limit:
- the site's reported percentages are not Seoyeongari calibration values.

---

# L7. Park et al. (2025) — four-year daily hydroperiod observations in Jeju lava-forest temporary wetlands

Park, M., Park, E., Seol, A. & Kim, J. (2025). **Characteristics and Delineation of Temporary Wetland in Lava Forest, Jeju Island.** *Forests*, 16(12), 1770. DOI: **10.3390/f16121770**.

Evidence class: **JEJU WETLAND HYDROPERIOD / DIRECT FIELD MONITORING**.

Key findings:
- five Seonheul Gotjawal temporary wetlands were monitored for water level over four years (2020–2023);
- mean annual hydroperiod indices varied from approximately **0.13 to 0.76**, demonstrating large differences in persistence among small Jeju volcanic-terrain wetlands;
- rainfall was related to water-level dynamics;
- some sites showed ecological wetland indicators and waterlogged conditions even when visible surface inundation was absent;
- hydrological boundaries defined from maximum monitored water level were consistently outside vegetation-defined ecological wetland boundaries.

Use in EGHM:
- very useful direct Jeju evidence for distinguishing **visible surface pool state** from the broader wet/waterlogged wetland state;
- supports the current conceptual direction in which zero visible surface-water storage does not imply that all soil/perched water has vanished;
- supports using hydroperiod/exposure as an ecological driver rather than treating pond presence/absence as the entire hydrological state.

Limitations:
- Seonheul Gotjawal is lower-elevation lava forest, not Seoyeongari;
- exact hydroperiod values must not be transferred as site targets.

---

# L8. Han & Cho (2025) — Saraoreum water-level response (supporting regional evidence)

Han, M. & Cho, A. (2025). **Analysis of Geomorphological Characteristics, Water Level Monitoring, and Correlation with Precipitation in Saraoreum, Jeju Island** [제주 사라오름의 지형 특성 및 수위 모니터링 결과와 강수와의 상관성 분석]. Korean Quaternary Research context / Korea Quaternary Association record.

Evidence class: **JEJU MONTANE WETLAND / SUPPORTING FIELD EVIDENCE**.

Available abstract-level findings:
- Saraoreum wetland water level shows pronounced seasonal and interannual variability;
- a 30-day accumulated-rainfall metric had the strongest reported relationship with water-level change;
- groundwater/subsurface drainage was interpreted as important when the wetland surface became exposed, rather than evaporation alone explaining drawdown.

Use in EGHM:
- provides a recent Jeju montane-wetland analogue supporting antecedent rainfall memory on multi-week timescales and subsurface loss during drawdown;
- useful as **supporting** evidence for a causal antecedent-hydrology window, but not sufficient to fix the EGHM `hydro_window = 60 d`.

Bibliographic caution:
- retain as supporting literature until full journal volume/pages/DOI metadata are verified from the publisher record.

---

# L9. Seoyeongari-specific conference evidence

Woo, S.J., Yoo, D.H. & Kim, J.N. (2024). **Analysis of Biogeomorphic Processes and Carbon Storage Capacity of Seoyeongari Wetland, Jeju Island** [제주도 서영아리 습지의 생물지형학적 프로세스 및 탄소보유능 분석]. *2024 Annual Meeting Abstracts, The Korean Geographical Society*, June 2024.

Evidence class: **SITE-SPECIFIC / CONFERENCE ABSTRACT**.

Key site-specific contribution:
- explicitly frames Seoyeongari terrestrialization as a process involving vegetation-driven peat formation and biogeomorphology, rather than only declining inflow or increasing hydrologic outflow;
- reports site soil/vegetation/remote-sensing analyses intended to quantify that mechanism.

Use in EGHM:
- direct site-specific conceptual support for including a biogeomorphic/peat component alongside hydrology and hydrosere succession;
- lower evidentiary weight than a full peer-reviewed article or the archived field report, so it should be cited as conference material when used.

---

# L10. Official Jeju groundwater classification — government context only

Jeju Special Self-Governing Province Water Resources portal, groundwater overview.

Evidence class: **GOVERNMENT TECHNICAL CONTEXT**.

Relevant point:
- Jeju officially distinguishes **perched groundwater (상위지하수)** from basal, parabasal, and bedrock groundwater systems.

Use in EGHM:
- useful terminology/background source showing that perched groundwater is an established Jeju hydrogeological category;
- peer-reviewed Ahn et al. (2017), Koh et al. (2012), and Jung et al. (2014) should be preferred for scientific process claims.

---

# L11. What the Jeju literature now supports strongly

The following conceptual chain can now be defended primarily with Jeju evidence:

`rainfall / soil-capacity excess`

→ infiltration through highly permeable volcanic material

→ interception by local low-permeability clay/paleosol/fine-material horizons

→ local or perched storage and lateral redistribution

→ possible return to depressions/wetlands and/or continued downward leakage

→ deeper/regional groundwater pathway.

This is consistent with the current EGHM separation between:
- local return reservoirs;
- explicit deep/regional loss;
- surface-water storage;
- a broader soil/wetland hydrological state that can persist when visible open water disappears.

The architecture is therefore no longer justified mainly by prairie-wetland analogues. Jeju-specific geomorphic, hydrogeological, isotopic, and water-level studies provide substantial support.

---

# L12. What remains unsupported by these references

Even after the Jeju-specific literature expansion, none of the sources independently determines the current exact values:

- `local_frac = 0.45`
- `FAST_FRAC = 0.75`
- `tau_fast = 30 d`
- `TAU_SLOW = 365 d`
- `k_gw = 4 mm d-1`
- `hydro_window = 60 d`

These remain calibrated or inherited effective parameters unless direct Seoyeongari hydrological observations are found.

The references make the **structure** substantially more defensible; they do not convert empirical parameter magnitudes into measured constants.

---

# L13. Model-development consequence

The Jeju literature reduces the motivation for replacing the present local/perched-groundwater architecture. The high-value remaining work is therefore:

1. robustness-test the two hidden legacy routing constants (`FAST_FRAC`, `TAU_SLOW`);
2. audit the inherited 161.7-mm external soil-store capacity;
3. compare the modelled seasonal pool disappearance pattern against the independent Seoyeongari field description;
4. if future Seoyeongari water-level data become available, use recession and rainfall-response behaviour to constrain `tau_fast`, `TAU_SLOW`, `k_gw`, and the causal hydrology window.

Do **not** add an additional groundwater process term merely because Jeju hydrogeology is complex; the current observations do not identify such added complexity.
