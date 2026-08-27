# Manuscript replacement blocks for the accepted Stage72 EGHM

These blocks are written to replace the legacy model-description portions of the current Round-1 manuscript. They are code-grounded to the accepted deterministic Stage63/71 structure and intentionally avoid claiming feedback mechanisms not implemented by the model.

## Replacement for Section 2.3. Model development

A daily Eco–Geo–Hydro model was developed to simulate changes in the open-water pond surface area of Seoyeongari wetland from 2011 to 2023. The framework combines (i) a physically closed daily water balance, (ii) a hydrologically conditioned ecological establishment state representing progressive occupation of repeatedly exposed pond margins, and (iii) a peat-accretion surface-expression term representing the progressive loss of visibly open-water area as the peat surface rises. The three components are linked in the modeled pond-area observation operator. In the accepted formulation, hydrology drives ecological exposure and establishment, whereas the ecological state does not feed back to evapotranspiration and the peat term does not alter the conserved hydraulic storage trajectory. These limitations are stated explicitly because the model is intended to test the additional explanatory contribution of ecological occupation and peat-controlled surface expression without introducing unconstrained feedback parameters.

### Meteorological forcing

Daily meteorological forcing was derived from the nearest Seogwang-ri AWS and ASOS sunshine records. Daily terrestrial reference evapotranspiration was calculated using the FAO-56 Penman–Monteith formulation, and daily open-water evaporation was calculated using the Penman formulation. The deterministic implementation evaluates the meteorological equations at fixed numerical precision and converts only the final daily forcing terms to IEEE-754 binary64 values to ensure cross-platform reproducibility. Missing temperature and wind observations were linearly interpolated in chronological order, whereas missing daily precipitation was treated as zero. The active water-balance kernel uses raw daily precipitation, terrestrial reference evapotranspiration, and Penman open-water evaporation. Legacy Curve Number runoff and effective-pond-precipitation arrays retained in the forcing module for compatibility are not used by the accepted hydrologic recurrence.

### Hydrologic domain and non-overlapping spatial accounting

The hydrologic domain was partitioned so that each square metre receives precipitation and evapotranspiration accounting only once. The potential wetland footprint was 5,939.5 m². The reconciled 2011 model reference open-water footprint was 2,241.762 m², leaving a 3,697.738 m² wetland margin. The independently delineated external contributing area was 8,483 m²; after subtracting the wetland margin already represented in the wetland footprint, the non-overlapping upland contributing area was 4,785.262 m². The resulting modeled component sum was 10,724.762 m². The small discrepancy relative to the nominal raster-domain bookkeeping area was retained and reported rather than adjusted through calibration.

For each day, the hydraulic open-water area was calculated from the current surface-water storage. Raw precipitation depth was then converted to separate water volumes over the non-overlapping upland area, the non-open portion of the wetland footprint, and the hydraulic open-water area. Their summed precipitation volume was required to equal precipitation depth multiplied by the modeled component area to within 10⁻⁸ m³.

### Storage–area geometry

Surface-water storage, V, was related to hydraulic open-water area, A, using the power-law relation

\[
A(V)=A_0\left(\frac{V}{V_0}\right)^{\frac{2}{p+2}},
\]

where \(A_0=2241.762\;\mathrm{m^2}\) is the reconciled 2011 model geometry reference, \(V_0=1000\;\mathrm{m^3}\) is the calibrated effective reference storage, and \(p=18\) is the calibrated geometry-shape parameter. The implied reference depth is

\[
h_0=\frac{V_0(p+2)}{A_0p}=0.4956418706\;\mathrm{m},
\]

and the corresponding depth–storage and area–depth relations are

\[
h(V)=h_0\left(\frac{V}{V_0}\right)^{\frac{p}{p+2}}
\]

and

\[
A(h)=A_0\left(\frac{h}{h_0}\right)^{\frac{2}{p}}.
\]

For the selected \(p=18\), the area–storage exponent is 1/10 and the area–depth exponent is 1/9. The geometry was implemented using fixed-order rational-root calculations to obtain identical numerical trajectories across computing environments. Because direct bathymetry was unavailable, \(V_0\) and \(p\) are interpreted as calibrated effective geometry parameters rather than measured pond-volume properties.

### Daily water balance

The daily hydrologic state contains five water stores: upland soil water, non-open wetland soil water, a fast local-return reservoir, a slow local-return reservoir, and open-surface water storage. The accepted model contains no annual relaxation, damping, fitted time trend, or other memory surrogate.

Upland and non-open wetland precipitation first enter their respective soil stores. Terrestrial evapotranspiration is removed from these stores, after which water above the prescribed soil-water capacity becomes excess water. Upland excess is divided into a local-return component and a deep-loss component. A fraction \(f_{local}=0.45\) is retained locally, of which 75% enters the fast reservoir and 25% enters the slow reservoir. The fast and slow reservoirs drain with characteristic time scales of 30 and 365 d, respectively, and their combined return flow enters the surface-water store. Excess from the non-open wetland soil store also enters surface water.

The open-surface store receives direct precipitation over the current hydraulic open-water footprint, wetland-soil excess, and fast plus slow local return flow. Three surface losses are then evaluated concurrently from the same pre-loss storage state: Penman open-water evaporation, surface drainage, and an effective area-proportional subsurface loss. The potential surface-drainage flux is

\[
Q_{out}^{*}=\frac{V}{\tau_{surf}},
\]

with \(\tau_{surf}=60\) d, and the potential subsurface-loss flux is

\[
Q_{gw}^{*}=\frac{k_{gw}A}{1000},
\]

where \(k_{gw}=4\;\mathrm{mm\,d^{-1}}\). This parameter is an effective area-proportional subsurface-loss flux and is not interpreted as saturated hydraulic conductivity. If the sum of potential open-water evaporation, surface drainage, and subsurface loss exceeds the available surface storage, all three losses are reduced by the same proportional factor. This avoids arbitrary within-day loss priority.

For every day, total water storage satisfies

\[
S_{tot,t+1}=S_{tot,t}+P_t-ET_t-E_{w,t}-D_t-Q_{out,t}-Q_{gw,t},
\]

where the terms represent total precipitation input, terrestrial evapotranspiration, open-water evaporation, deep loss, surface drainage, and effective subsurface loss, respectively. Maximum daily mass-balance, spatial-area-partition, and precipitation-partition errors were required to be ≤10⁻⁸ in their corresponding units; the accepted deterministic trajectory closes at approximately 10⁻¹² numerical precision.

### Hydrologically conditioned ecological establishment

The ecological component represents gradual occupation of repeatedly exposed portions of the original pond footprint. Daily exposed fraction was defined as

\[
E_t=\min\left[1,\max\left(0,\frac{A_0-A_t}{A_0}\right)\right].
\]

Because brief single-day exposure was not considered sufficient for establishment, the ecological driver was the minimum exposed fraction over the preceding seven consecutive days, \(E_{7,t}\). The remaining unestablished fraction, \(R_t\), was updated as

\[
R_{t+1}=R_t\left(1-\frac{r_{est}}{365}E_{7,t}\right),
\]

and the cumulative establishment state was

\[
S_t=1-R_t,
\]

with \(r_{est}=0.05\;\mathrm{yr^{-1}}\). The establishment state is irreversible in the accepted model. A previously tested flood-reversal coefficient was removed after calibration repeatedly drove it to biologically negligible century-to-millennial reciprocal time scales. The ecological state therefore reflects accumulated establishment opportunity rather than a fitted year trend.

### Short-term hydrologic feature

To preserve interannual hydrologic information relevant to the acquisition season, fast plus slow return flow was summed over a causal trailing 14-d window. For each observation year, the April–May mean of this trailing return-flow sum was expressed relative to the April–May 2011 reference mean. The resulting hydrologic anomaly is denoted \(H\). The window is antecedent only; no centered window, future shift, or explicit year predictor is used.

### Peat-controlled surface expression

Long-term peat accretion was represented as a prescribed persistent surface-rise rate rather than as a fitted annual relaxation term. The primary site-informed persistent-net range was 0.29–0.47 mm yr⁻¹, with 0.38 mm yr⁻¹ used as the reference value. Higher recent apparent rates (2.89–7.00 mm yr⁻¹) were retained only as stress tests and were not interpreted as sustained long-term topographic rise.

For cumulative peat rise \(B_t\), the hydraulic storage trajectory was first solved independently. The equivalent hydraulic depth \(h(V_t)\) and hydraulic area \(A_{hyd,t}\) were then obtained from the accepted storage geometry. The residual depth above the rising peat surface was defined as

\[
h_{res,t}=\max[h(V_t)-B_t,0],
\]

with corresponding surface-expression area

\[
A_{peat,t}=A_0\left(\frac{h_{res,t}}{h_0}\right)^{2/p}.
\]

The geomorphic loss of modeled open-water surface expression was

\[
G_t=\max(A_{hyd,t}-A_{peat,t},0).
\]

This term changes the surface area represented as open water but does not remove water from the conserved storage state. Thus the present peat formulation represents a geomorphic surface-expression pathway rather than a fully coupled peat-to-storage-capacity feedback.

## Replacement for Section 2.4. Model scenarios

Four nested scenario formulations were evaluated using the same conserved daily hydrologic trajectory. Daily ecological establishment and peat surface-expression terms were aggregated over April and May to correspond to the available airborne-image acquisition-season metadata.

Let \(S_y\) denote the April–May ecological establishment support for year \(y\), \(H_y\) the short-term return-flow anomaly, and \(G_y\) the April–May peat surface-expression loss. Predicted mapped open-water pond area was defined as follows:

\[
A_{Baseline,y}=A_0+K_hH_y,
\]

\[
A_{Hydrosere,y}=A_0-K_cS_y+K_hH_y,
\]

\[
A_{EcoGeo,y}=A_0-G_y+K_hH_y,
\]

and

\[
A_{Integrated,y}=A_0-K_cS_y-G_y+K_hH_y.
\]

Here \(K_c\) (m²) converts the dimensionless establishment state to a colonized/non-open area contribution, and \(K_h\) (m² m⁻³) converts the return-flow anomaly to an area contribution. Both coefficients were restricted to non-negative values, with \(K_c\leq A_0\). These coefficients are calibrated observation-operator quantities rather than direct field measurements.

The four scenarios therefore test whether adding hydrologically conditioned ecological occupation, peat-controlled surface expression, or both improves the representation of the historical mapped open-water trajectory relative to the common water-balance backbone. They do not represent separate hydrologic simulations with scenario-specific vegetation evapotranspiration or peat-modified conserved storage.

## Replacement for Section 2.5. Calibration, goodness-of-fit and sensitivity analysis

The active mapped open-water target contains six observation years: 2013, 2015, 2017, 2019, 2021 and 2023. The 2011 state is used only for initialization and hydrologic reference, and there is no 2022 mapped pond-area observation in the current analysis. Meteorological forcing remains continuous through 2022 because absence of a mapped-area target does not imply absence of meteorological data.

Model development followed a hierarchy in which physical and ecological constraints were applied before goodness-of-fit. Daily water-balance closure, exact non-overlapping spatial accounting, causal predictor construction, absence of fitted time trends, and ecological plausibility were treated as mandatory constraints. Because only six mapped-area target years are available, leave-one-year-out and nested cross-validation diagnostics were not used as acceptance or model-ranking gates. Remaining unmeasured geometry, hydrologic, ecological, and observation-operator quantities are reported as calibrated effective parameters rather than measured constants.

Model fit was quantified using

\[
RMSE=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(P_i-O_i)^2}
\]

and

\[
nRMSE=100\frac{RMSE}{\bar O},
\]

where \(P_i\) and \(O_i\) are predicted and observed mapped open-water pond areas, \(\bar O\) is the mean observed area, and \(n=6\).

Primary peat-rate sensitivity used the independently motivated persistent-net range 0.29, 0.38 and 0.47 mm yr⁻¹. Higher recent apparent rates were evaluated only as stress tests. Parameter one-at-a-time analyses were used to examine robustness; scenario rank was always treated as an output rather than as a calibration target.

## Replacement for the core model-results paragraph in Section 3.2

Using the six mapped open-water observations from 2013 to 2023 and the reference persistent-net peat-rise rate of 0.38 mm yr⁻¹, the Integrated configuration had the lowest error (RMSE = 28.81 m²; nRMSE = 1.411%). The Hydrosere Only configuration ranked second (RMSE = 32.38 m²; nRMSE = 1.587%), whereas the Eco-Geo Only and Baseline configurations produced substantially larger errors (RMSE = 215.50 and 222.42 m²; nRMSE = 10.558% and 10.897%, respectively). For the central Integrated fit, the calibrated ecological area coefficient was \(K_c=1877.51\) m² and the short-term hydrologic coefficient was \(K_h=0.08285\) m² m⁻³. The ranking was not imposed during calibration. Exact daily mass-balance, spatial-area, and precipitation-partition closure remained at approximately machine precision.

## Replacement for the main model-interpretation paragraph in the Discussion

The Integrated configuration produced the lowest mapped pond-area error, indicating that the historical trajectory is more consistent with a representation that combines hydrologically conditioned ecological establishment and peat-related surface expression than with the common hydrologic backbone alone. The ecological pathway in the accepted model is causal: contraction of hydraulic open-water area creates continuous exposure opportunities, which accumulate into an establishment state and progressively reduce the area represented as open water. The geomorphic pathway represents the effect of persistent peat accretion on the surface expression of open water relative to the conserved hydraulic state. These results therefore support the added explanatory value of including ecological occupation and geomorphic surface-expression processes when interpreting terrestrialization at Seoyeongari. However, they should not be interpreted as numerical evidence that vegetation-driven evapotranspiration feedback or peat-driven reduction of conserved storage capacity caused the observed change, because those feedback pathways are not included in the accepted model.

## Replacement / addition for model limitations

The model is constrained by the small number of historical mapped-area observations and by the absence of direct bathymetric, continuous water-level, and vegetation-specific evapotranspiration measurements. Several hydrologic and geometry parameters therefore remain calibrated effective quantities. In addition, ecological establishment affects the mapped open-water observation operator but does not modify evapotranspiration in the accepted formulation, and peat accretion modifies open-water surface expression without feeding back into conserved hydraulic storage. Exact acquisition days for the historical imagery have not yet been recovered, so April–May mean modeled support is used from the available acquisition-season metadata. Finally, numerical zero surface storage is not assumed to be equivalent to visually absent surface water; quantitative validation of seasonal pool disappearance would require an independently constrained relationship among water depth, microtopography, vegetation cover, and visible open-water expression.
