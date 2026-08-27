# EGHM reference ledger — process-to-reference audit

Updated: 2026-08-27

Purpose: maintain a defensible mapping between the equations/process assumptions actually used in the current Seoyeongari EGHM and the literature or site evidence that supports them. A reference that supports a **process form** must not be presented as evidence for an exact **calibrated parameter value** unless it actually constrains that value.

## Evidence classes

- **DIRECT FORM** — directly supports the mathematical/process class used in the model.
- **DIRECT METHOD** — directly supports the meteorological/measurement method used.
- **SITE / REGIONAL PROCESS** — supports local/regional geological or ecological plausibility.
- **INTERPRETATION / CAVEAT** — constrains how model outputs or field rates may be interpreted.
- **CALIBRATION THEORY** — supports parameter-identifiability, parsimony, robustness, or equifinality decisions.
- **SITE PRIMARY** — direct Seoyeongari field evidence. These data outrank external analogues for the site quantity concerned, but their own measurement/model uncertainty must still be reported.

---

# A. Wetland water balance and storage

## A1. Rosenberry & Hayashi (2013)

Rosenberry, D.O. & Hayashi, M. (2013). **Assessing and measuring wetland hydrology.** In *Wetland Techniques, Volume 1: Foundations*, 87–225. DOI: **10.1007/978-94-007-6860-4_3**.

Evidence class: **DIRECT FORM / DIRECT METHOD**.

Supports:
- explicit wetland water-budget accounting;
- separate source/loss terms and storage change;
- the need to quantify uncertainty and closure of wetland water budgets.

Use in EGHM:
- supports the current daily conservation architecture in which precipitation, evapotranspiration, return flow, surface drainage, subsurface loss, and storage are explicitly accounted for.

Does **not** independently support:
- `tau_surf = 60 d`;
- `k_gw = 4 mm d-1`;
- `local_frac = 0.45`.

## A2. USGS wetland hydrologic-process synthesis

Carter, V. / USGS. **Hydrologic processes in wetlands**, in *History of Wetlands in the Conterminous United States*.

Evidence class: **DIRECT FORM**.

Supports the canonical wetland budget form in which precipitation, surface-water inflow/outflow, groundwater inflow/outflow, evapotranspiration, and change in storage are explicit components.

Use in EGHM: secondary authoritative support for treating every hydrologic gain/loss as a conserved flux rather than as an empirical area correction.

---

# B. Depression wetland hypsometry

## B1. Hayashi & van der Kamp (2000)

Hayashi, M. & van der Kamp, G. (2000). **Simple equations to represent the volume–area–depth relations of shallow wetlands in small topographic depressions.** *Journal of Hydrology*, 237, 74–85. DOI: **10.1016/S0022-1694(00)00300-0**.

Evidence class: **DIRECT FORM**.

Supports:
- using simple parametric area–depth and volume–depth relations for shallow depression wetlands;
- using such equations as geometric models when full fine-resolution bathymetry is unavailable;
- coupling wetland storage volume to inundated surface area.

Use in EGHM:
- strongest reference for the current `V -> A` / `A–V–h` power-law geometry.

Important limitation:
- this paper does **not** provide Seoyeongari-specific `V0 = 1000 m3` or `p_shape = 18`;
- those remain calibrated effective geometry parameters unless independent bathymetry/topographic survey constrains them.

---

# C. Catchment–wetland and groundwater exchange

## C1. Hayashi & Rosenberry (2002)

Hayashi, M. & Rosenberry, D.O. (2002). **Effects of Ground Water Exchange on the Hydrology and Ecology of Surface Water.** *Groundwater*, 40, 309–316. DOI: **10.1111/j.1745-6584.2002.tb02659.x**.

Evidence class: **DIRECT FORM**.

Supports:
- groundwater exchange as an important control on lake/wetland water levels;
- subsurface exchange as a hydrologically and ecologically meaningful process rather than a residual correction.

Use in EGHM:
- supports retaining explicit subsurface return/loss components.

## C2. Hayashi, van der Kamp & Rosenberry (2016)

Hayashi, M., van der Kamp, G. & Rosenberry, D.O. (2016). **Hydrology of prairie wetlands: Understanding the integrated surface-water and groundwater processes.** *Wetlands*, 36(S2), 237–254. DOI: **10.1007/s13157-016-0797-9**.

Evidence class: **DIRECT FORM**.

Supports:
- treating wetland and catchment as an integrated hydrological unit;
- catchment runoff/lateral input as a control on wetland permanence;
- exchange between the central pond, moist margin, and groundwater;
- the role of surface and subsurface storage/connectivity.

Use in EGHM:
- supports the conceptual `upland -> local storage/return -> wetland` architecture.

Important limitation:
- it does not provide exact Seoyeongari reservoir time constants or routing fractions.

## C3. Ahn et al. (2017) — Jeju field geology

Ahn, U.S., Jeon, Y., Ki, J.S., Kim, G.P., Koh, S.H., Lee, B.C. & Jung, C.Y. (2017). **Proposal of new groundwater model through field observations in Jeju Island** [야외지질학적 관찰을 통한 제주도 지하수 모델 제안]. *Journal of the Geological Society of Korea*, 53(2), 347–360. DOI: **10.14770/jgsk.2017.53.2.347**.

Evidence class: **SITE / REGIONAL PROCESS**.

Supports:
- laterally extensive low-permeability clay-rich interbeds between volcanic units on Jeju;
- perched groundwater above low-permeability layers;
- the 1100 Highland wetland example of surface water associated with clay deposits;
- repeated collection, lateral movement, and deeper leakage of infiltrated water controlled by interbedded low-permeability layers.

Use in EGHM:
- strong Jeju-specific process justification for conceptual local/perched subsurface storage and return pathways.

Does **not** support exact `local_frac`, `tau_fast`, or `k_gw` values.

## C4. Jung et al. (2014)

Jung, H.W., Yun, S.T., Kim, K.H., Oh, S.S. & Kang, K.G. (2014). **Role of an impermeable layer in controlling groundwater chemistry in a basaltic aquifer beneath an agricultural field, Jeju Island, South Korea.** *Applied Geochemistry*, 45. DOI: **10.1016/j.apgeochem.2014.03.008**.

Evidence class: **SITE / REGIONAL PROCESS**.

Supports:
- a shallow perched aquifer above an impermeable clay-rich layer in the Jeju basaltic setting;
- local precipitation recharge of a perched system physically separated from deeper regional groundwater.

Use in EGHM:
- independent regional corroboration of the perched-storage concept.

## C5. Kim & Yang (2019)

Kim, M.C. & Yang, S.K. (2019). **Analysis of Groundwater Flow Characteristics and Hydraulic Conductivity in Jeju Island Using Groundwater Model.** *Journal of Environmental Science International*, 28(12), 1157–1169. DOI: **10.5322/JESI.2019.28.12.1157**.

Evidence class: **SITE / REGIONAL PROCESS**.

Supports:
- strongly heterogeneous groundwater flow and hydraulic properties in Jeju;
- use of observed groundwater levels and recharge information to constrain island groundwater modelling.

Use in EGHM:
- contextual support for not interpreting a single effective wetland loss coefficient as a rock-scale universal hydraulic conductivity.

---

# D. Evapotranspiration and open-water evaporation

## D1. Allen et al. (1998) — FAO-56

Allen, R.G., Pereira, L.S., Raes, D. & Smith, M. (1998). **Crop evapotranspiration — Guidelines for computing crop water requirements.** FAO Irrigation and Drainage Paper 56. ISBN **92-5-104219-5**.

Evidence class: **DIRECT METHOD**.

Supports:
- FAO-56 reference evapotranspiration framework;
- radiation, vapour-pressure, aerodynamic and psychrometric terms used in Penman–Monteith reference ET calculations;
- standard radiation estimation procedures used with meteorological observations.

Use in EGHM:
- primary reference for the vegetation/reference ET meteorological calculations.

## D2. Penman (1948)

Penman, H.L. (1948). **Natural evaporation from open water, bare soil and grass.** *Proceedings of the Royal Society A*, 193(1032), 120–145. DOI: **10.1098/rspa.1948.0037**.

Evidence class: **DIRECT METHOD**.

Supports:
- combining energy-balance and aerodynamic information to estimate natural evaporation;
- open-water evaporation from standard meteorological data.

Use in EGHM:
- foundational reference for Penman-type open-water evaporation.

## D3. Drexler et al. (2004)

Drexler, J.Z., Snyder, R.L., Spano, D. & Paw U, K.T. (2004). **A review of models and micrometeorological methods used to estimate wetland evapotranspiration.** *Hydrological Processes*, 18(11), 2071–2101. DOI: **10.1002/hyp.1462**.

Evidence class: **DIRECT METHOD / INTERPRETATION CAVEAT**.

Supports:
- use of Penman/Penman–Monteith-class approaches in wetland ET work;
- explicit acknowledgement that wetland ET is heterogeneous and method/site dependent.

Use in EGHM:
- supports the method class but argues against presenting any fixed wetland/open-water ET multiplier as universally valid.

---

# E. Hydroperiod, exposure and vegetation establishment

## E1. Casanova & Brock (2000)

Casanova, M.T. & Brock, M.A. (2000). **How do depth, duration and frequency of flooding influence the establishment of wetland plant communities?** *Plant Ecology*, 147, 237–250. DOI: **10.1023/A:1009875226637**.

Evidence class: **DIRECT FORM**.

Supports:
- establishment and resulting wetland community composition being controlled by flooding depth, duration, and frequency;
- use of hydrologic exposure/inundation history rather than calendar year alone to drive recruitment.

Use in EGHM:
- strong process support for exposure-conditioned recruitment.

Does **not** independently establish a universal 7-day threshold.

## E2. Nicol & Ganf (2000)

Nicol, J.M. & Ganf, G.G. (2000). **Water regimes, seedling recruitment and establishment in three wetland plant species.** *Marine and Freshwater Research*, 51(4), 305–309. DOI: **10.1071/MF99147**.

Evidence class: **DIRECT FORM**.

Supports:
- species-specific recruitment niches under different hydrologic regimes;
- drawdown/water-level conditions affecting germination, establishment and subsequent reproduction.

Use in EGHM:
- supports causal hydroperiod-conditioned establishment and cautions against treating one timing threshold as universal across species.

## E3. Webb, Wallis & Stewardson (2012)

Webb, J.A., Wallis, E.M. & Stewardson, M.J. (2012). **A systematic review of published evidence linking wetland plants to water regime components.** *Aquatic Botany*, 103, 1–14. DOI: **10.1016/j.aquabot.2012.06.003**.

Evidence class: **DIRECT FORM / REVIEW**.

Supports, from a systematic evidence base:
- causal links between waterlogging/inundation/depth/duration/frequency/timing and plant establishment, growth, reproduction, composition and diversity.

Use in EGHM:
- strongest review-level reference for the decision to make recruitment a function of causal water regime rather than fitted calendar time.

## E4. Korean wetland establishment context

**Establishment strategy of a rare wetland species *Sparganium erectum* in Korea.** *Journal of Ecology and Environment* (2017). DOI: **10.1186/s41610-017-0045-0**.

Evidence class: **REGIONAL ECOLOGICAL CONTEXT**.

Supports:
- Korean wetland seedling establishment and survival being strongly water-level dependent;
- establishment success depending on inundation condition and water-level stabilization.

Use in EGHM:
- regional contextual reinforcement only; not a calibration source for Seoyeongari species or a 7-day threshold.

---

# F. Peat growth, accumulation and geomorphic interpretation

## F1. Clymo (1984)

Clymo, R.S. (1984). **The limits to peat bog growth.** *Philosophical Transactions of the Royal Society of London B*, 303(1117), 605–654. DOI: **10.1098/rstb.1984.0002**.

Evidence class: **DIRECT FORM / FIELD-METHOD BACKGROUND**.

Supports:
- long-term peat-growth modelling in which organic-matter input and decomposition govern peat accumulation;
- the conceptual basis of the Clymo-type age/depth model used to derive the site long-term accumulation estimate.

Use in EGHM:
- methodological background for the field-derived peat accumulation estimate, not a substitute for the Seoyeongari radiocarbon evidence itself.

## F2. Seoyeongari field report — site primary evidence

Woo, S.J. & Kim, J.N., supervised by Kim, D.H. **제주도 이탄습지의 탄소순환 분석** [Analysis of carbon cycling in a Jeju peat wetland], student autonomous education final report.

Evidence class: **SITE PRIMARY**.

Reported field/model evidence:
- Core 13, 75 cm radiocarbon result: approximately BP 2000–1830 at 95.4% confidence;
- Clymo-model long-term peat accumulation lower/central/upper estimate: **0.29 / 0.38 / 0.47 mm yr-1**;
- recent post-1980 apparent accumulation: **2.89 / 5.91 / 7.00 mm yr-1**;
- the report explicitly notes that radiocarbon sample number was limited and that the Clymo-model accuracy could not be independently verified at the site.

Use in EGHM:
- **0.38 mm yr-1 is the field-derived central long-term estimate used by the central model**;
- 0.29 and 0.47 mm yr-1 are the reported lower/upper long-term estimates used for site-informed sensitivity;
- 2.89–7.00 mm yr-1 is recent apparent accumulation and is retained only as stress-test context.

Critical wording:
- do not call 0.29/0.38/0.47 three independent replicate measurements;
- do not call 0.38 a direct annual surface-elevation measurement;
- do not call it a pond-area-fit-selected parameter.

## F3. Økland & Ohlson (1998)

Økland, R.H. & Ohlson, M. (1998). **Age-Depth Relationships in Scandinavian Surface Peat: A Quantitative Analysis.** *Oikos*, 82(1), 29–36. DOI: **10.2307/3546914**.

Evidence class: **INTERPRETATION / CAVEAT**.

Supports:
- strong early compaction of surface peat through biological decomposition and physical consolidation;
- age–depth relationships near the surface not being equivalent to a constant long-term vertical growth rate.

Use in EGHM:
- supports separating recent apparent accumulation from persistent long-term peat rise.

## F4. Young et al. (2019)

Young, D.M., Baird, A.J., Charman, D.J., Evans, C.D., Gallego-Sala, A.V., Gill, P.J., Hughes, P.D.M., Morris, P.J. & Swindles, G.T. (2019). **Misinterpreting carbon accumulation rates in records from near-surface peat.** *Scientific Reports*, 9, 17939. DOI: **10.1038/s41598-019-53879-8**.

Evidence class: **INTERPRETATION / CAVEAT**.

Supports:
- recent near-surface apparent accumulation being systematically higher than long-term preserved accumulation because recently deposited material has not yet undergone continuing decomposition;
- recent accumulation rates not being safely extrapolated as sustained long-term carbon/peat accumulation.

Use in EGHM:
- strong justification for not using the 2.89–7.00 mm yr-1 recent site range as the primary persistent geomorphic rate.

## F5. Cahoon (2024)

Cahoon, D.R. (2024). **Measuring and interpreting the surface and shallow subsurface process influences on coastal wetland elevation: A review.** *Estuaries and Coasts*, 47, 1708–1734. DOI: **10.1007/s12237-024-01332-z**.

Evidence class: **INTERPRETATION / CAVEAT**.

Supports:
- vertical accretion often differing from actual surface-elevation change because compaction, decomposition, root-zone processes, shrink–swell, and shallow subsidence/expansion also contribute.

Use in EGHM:
- strongest citation for the caveat that the Seoyeongari Clymo accumulation estimate is a **persistent biogeomorphic elevation proxy**, not a directly measured surface-elevation-change series.

Important domain caveat:
- Cahoon focuses on coastal/tidal wetlands, so this is a process/measurement caveat, not a site analogue for Seoyeongari rates.

---

# G. Calibration, identifiability and parsimony

## G1. Beven (2006)

Beven, K. (2006). **A manifesto for the equifinality thesis.** *Journal of Hydrology*, 320, 18–36. DOI: **10.1016/j.jhydrol.2005.07.007**.

Evidence class: **CALIBRATION THEORY**.

Supports:
- multiple parameter/model configurations often being observationally acceptable;
- the need to avoid interpreting a single optimum fit as unique truth.

Use in EGHM:
- supports keeping parameter perturbation and provenance visible rather than endlessly widening calibration grids to lower RMSE.

## G2. Efstratiadis & Koutsoyiannis (2010)

Efstratiadis, A. & Koutsoyiannis, D. (2010). **One decade of multi-objective calibration approaches in hydrological modelling: a review.** *Hydrological Sciences Journal*, 55(1), 58–78. DOI: **10.1080/02626660903526292**.

Evidence class: **CALIBRATION THEORY / REVIEW**.

Supports:
- poor identifiability and equifinality in complex parameterizations;
- use of additional response information and hydrologic expertise/soft data to constrain calibration;
- the principle that additional parameters without supplementary information can worsen identifiability and overfitting.

Use in EGHM:
- directly supports the current freeze recommendation: do not add fitted process terms unless new independent observations constrain them.

## G3. Her (2015)

Her, Y. (2015). **Impact of the numbers of observations and calibration parameters on equifinality, model performance, and output and parameter uncertainty.** *Hydrological Processes*, 29, 4220–4237. DOI: **10.1002/hyp.10487**.

Evidence class: **CALIBRATION THEORY**.

Supports:
- calibration behaviour, equifinality, and parameter/output uncertainty depending strongly on the ratio of observation information to calibrated parameters.

Use in EGHM:
- reinforces the caution that six pond-area target years cannot independently identify all current process and observation-operator coefficients.

---

# H. Current parameter-to-evidence status

| Model item | Best supporting evidence | Current status |
|---|---|---|
| Daily mass-conserved wetland water budget | Rosenberry & Hayashi 2013; USGS wetland water-budget synthesis | **Strong form** |
| Penman/PM meteorological evaporation framework | Penman 1948; Allen et al. 1998; Drexler et al. 2004 | **Strong method class** |
| A–V–h depression geometry | Hayashi & van der Kamp 2000 | **Strong form; site values calibrated** |
| Catchment–wetland coupling | Hayashi et al. 2016 | **Strong form** |
| Jeju perched/local storage concept | Ahn et al. 2017; Jung et al. 2014 | **Strong regional process support** |
| `local_frac = 0.45` | no direct measurement | **Calibrated effective parameter** |
| `tau_fast = 30 d` | no direct site recession measurement | **Calibrated effective parameter** |
| `k_gw = 4 mm d-1` | groundwater-exchange literature supports process, not magnitude | **Calibrated effective flux; weakly identified** |
| Exposure-conditioned recruitment | Casanova & Brock 2000; Nicol & Ganf 2000; Webb et al. 2012 | **Strong form** |
| `est_window = 7 d` | literature supports timing dependence, not exact threshold | **Calibrated/bounded timing parameter** |
| `r_est = 0.05 yr-1` | process support only | **Calibrated ecological rate** |
| Long-term peat rate central value 0.38 mm/yr | Seoyeongari field report | **Site-derived central estimate; not pond-area calibrated** |
| Recent peat rate not used as persistent rate | Young et al. 2019; Økland & Ohlson 1998 | **Strong interpretation support** |
| Accretion != measured surface elevation change | Cahoon 2024 | **Strong caveat** |
| Avoid adding extra fitted terms with six targets | Beven 2006; Efstratiadis & Koutsoyiannis 2010; Her 2015 | **Strong calibration-theory support** |

---

# I. Highest-priority reference gaps remaining

1. **Seoyeongari-specific water-level/recession observations** that could constrain `tau_surf`, `tau_fast`, or effective `k_gw`.
2. **Independent bathymetry/RTK/UAV surface elevations** that could constrain `V0` and `p_shape` rather than fitting them.
3. **Species/site-specific establishment observations** that could independently constrain `est_window_d` and `r_est_yr`.
4. A direct **surface-elevation time series** (SET, repeated leveling, RTK, equivalent) if the peat accumulation proxy is ever to be replaced by observed elevation change.
5. Exact bibliographic/publication metadata for the Seoyeongari field report should be retained alongside the archived report and radiocarbon laboratory result in the final reproducibility package.

## Reference-use rule for manuscript drafting

Never write that a literature source *determined* a calibrated value unless it actually did. Preferred language:

- “The process formulation follows / is consistent with …” for literature-supported forms.
- “The parameter was calibrated within the pre-specified admissible range …” for effective parameters.
- “The central value was independently derived from site field evidence …” for the 0.38 mm yr-1 peat rate.
- “Used as a sensitivity/stress-test range …” for values not used in central calibration.
