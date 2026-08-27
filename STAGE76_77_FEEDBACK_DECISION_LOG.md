# Stage76–77 feedback decision log

Updated: 2026-08-27

## Stage76 — woody canopy interception

Independent Seoyeongari evidence confirms woody encroachment and a strong tree age-distance relation. A diagnostic positive feedback was therefore tested:

hydraulic exposure -> cumulative exposure D -> terrestrialized area A_terr -> fixed woody establishment lag -> woody area -> canopy interception -> hydrology -> exposure.

The woody lag was fixed at 5.283 yr from the intercept of the site tree-ring regression Age = 5.283 + 1.760 Distance (n=6, R2 approximately 0.916). This is a field-anchored approximation, not a directly measured universal establishment lag.

Rainfall interception was not fitted. Tested anchors were 0, 0.1337 and 0.255, spanning published young and mature Cryptomeria japonica measurements; Saito et al. (2013, J Hydrol, DOI 10.1016/j.jhydrol.2013.09.053) measured 25.5% interception.

Workflow run: 33042998989. Ubuntu 22.04 and 24.04 both succeeded.

Result:
- best full-six candidate: interception = 0
- beta_D = 78 m2/exposure-yr
- RMSE = 26.0538 m2
- nRMSE = 1.27647%
- nested LOOCV nRMSE = 2.10459%
- only the 2017 LOOCV fold selected positive interception (0.255); five folds selected zero.

Decision: **do not include woody canopy interception in the central model from pond-area fit alone.** Woody encroachment is independently observed, but its hydrologic interception effect is not identified by the six open-water observations. Keep canopy interception as a process sensitivity / future independently constrained feedback.

## Stage77 — terrestrialization-dependent peat-forming area

Site carbon/vegetation evidence is more direct for peat feedback: aquatic-center cores contain significantly more organic matter than terrestrial grassland and Cryptomeria peripheral cores, and the peripheral terrestrialized zones were interpreted as having greater drainage and decomposition.

General peat literature likewise supports reduced peat preservation under longer oxic exposure / water-table lowering (Laiho 2006, DOI 10.1016/j.soilbio.2006.02.017; Philben et al. 2014, DOI 10.1002/2013JG002573) and explicit ecohydrological feedbacks in peatland development (Morris, Belyea & Baird 2011, DOI 10.1111/j.1365-2745.2011.01842.x).

No fitted decomposition coefficient was introduced. The independently field-derived local wet-peat rate remains 0.38 mm/yr. The lumped area contribution is partitioned as:

f_peat(t) = max[1 - A_terr(t)/A0, 0]
G_eff(t) = f_peat(t) G_wet(t)

This means the 0.38 mm/yr local wet-peat vertical rate is preserved where the wet peat-forming regime remains; already terrestrialized area no longer receives the same wet-peat surface-expression contribution.

Three structures were tested:
1. uniform peat, one-way;
2. peat-forming area partition only;
3. causal coupled area partition, where prior A_terr reduces the peat-forming fraction and peat surface expression contributes to the next ecological exposure update.

Workflow run: 33043218204. Both Ubuntu jobs succeeded.

At 0.38 mm/yr:
- uniform peat: nRMSE 1.27615%, beta_D=78
- one-way area partition: 1.28394%, beta_D=78
- coupled area partition: **1.27510%**, beta_D=77

Coupled 2023 state:
- D = 4.41024 exposure-yr
- A_terr = 339.59 m2
- remaining peat-forming fraction = 0.84853
- peat surface-expression contribution G = 3.133 m2

Nested formulation+beta LOOCV nRMSE = 2.00687%, slightly below the Stage74 simple cumulative-exposure diagnostic (2.02804%). Four of six LOOCV folds selected the coupled area-partition formulation; 2019 and 2023 selected uniform peat.

Decision: **carry the coupled peat-forming-area formulation forward as the preferred Integrated-process candidate**, not because the RMSE improvement is large, but because it (a) prevents conceptual/spatial overlap between terrestrialized and wet-peat-forming areas, (b) adds no fitted process coefficient, (c) is directly supported by site vegetation/organic-matter evidence, and (d) does not degrade predictive diagnostics.

The formulation must be described as an area-partition approximation in a lumped model, not as a measured linear decomposition law and not as evidence that local peat accumulation rate itself equals 0.38*(1-A_terr/A0).

## Data contract
- observations: 2013, 2015, 2017, 2019, 2021, 2023
- 2011 initial/reference only
- 2022 pond-area observation absent
- observation variable: mapped open-water pond surface area
- current support: April-May
