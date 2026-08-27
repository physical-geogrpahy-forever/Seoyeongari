# Stage75 ET-feedback decision log

Updated: 2026-08-27

## Question

After replacing the abstract ecological state S with cumulative hydrologic exposure dose D and a directly interpretable terrestrialized area

A_terr(t) = beta_D * D(t),

should A_terr feed back to the conserved daily water balance by changing vegetation evapotranspiration?

## Literature-bounded experiment

The ET direction was not forced. The current wet-vegetation reference was K_wet = 1.0 relative to FAO-PM grass-reference ETo, and the terrestrialized/woody vegetation coefficient was restricted to literature anchors:

- K_terr = 0.75
- K_terr = 0.85
- K_terr = 1.00
- K_terr = 1.18
- K_terr = 1.23

Primary reference: Pereira, Paredes & Espirito-Santo (2024), Irrigation Science, DOI 10.1007/s00271-024-00923-9. The review shows that wetland and riparian vegetation Kc values overlap broadly: emergent wetland vegetation often exceeds 1, while some woody/shrub cases are below 1 and well-watered Populus can exceed 1. Hence woody encroachment cannot be assumed a priori to increase ET relative to the existing wetland vegetation.

The daily feedback calculation was causal: today's post-loss hydraulic exposure increased tomorrow's persistent A_terr, and A_terr replaced an equal portion of wetland-vegetation area in the ET calculation. Spatial double counting with open water was prohibited. Peat central rate remained the field-derived 0.38 mm/yr.

## Reproducible Stage75b result

Workflow run: 33042560130
Both Ubuntu 22.04 and Ubuntu 24.04 jobs succeeded.

Best full-six-year candidate:
- K_terr = 0.85
- beta_D = 78.0 m2 per exposure-year
- RMSE = 25.8835399490 m2
- nRMSE = 1.2681336536%
- K_hydro = 0.0742722713 m2/m3
- A_terr(2023 April-May) = 338.5094710 m2

No-ET-contrast anchor (K_terr = 1.0):
- beta_D = 78.0 m2 per exposure-year
- RMSE = 26.0537573637 m2
- nRMSE = 1.2764732560%
- K_hydro = 0.0824530926 m2/m3
- A_terr(2023 April-May) = 340.4969770 m2

Improvement from allowing the best literature ET anchor versus no ET contrast:
- RMSE improvement = 0.1702174147 m2
- nRMSE improvement = 0.0083396024 percentage points

Nested LOOCV across K_terr and beta_D:
- RMSE = 42.9086823072 m2
- nRMSE = 2.1022605167%
- five folds selected K_terr = 0.85, but the 2017 holdout selected K_terr = 1.23.

For comparison, the Stage74 no-ET cumulative-exposure model had:
- full-six nRMSE = 1.2758689194%
- LOOCV nRMSE = 2.0280448429%
- one fewer ET-model selection dimension.

Physical closure remained approximately 1e-12.

## Decision

**Do not adopt a fitted vegetation-ET feedback as the central model yet.**

Reasons:
1. The best full-six candidate implies lower, not higher, vegetation ET after terrestrialization (K_terr = 0.85).
2. Its improvement over K_terr = 1 is only 0.00834 percentage points nRMSE, far too small to establish feedback direction from six pond-area observations.
3. Nested LOOCV is slightly worse than the simpler Stage74 cumulative-exposure model.
4. The literature itself shows substantial overlap between wetland and woody/riparian Kc values; vegetation identity, rooting access and water limitation determine the direction.
5. Selecting K_terr by pond-area fit would make the claimed ecohydrologic feedback weakly identified and unnecessarily data-driven.

Therefore:
- retain cumulative exposure D -> A_terr as the preferred ecological-memory structure;
- treat Stage75 ET feedback as a sensitivity experiment;
- determine vegetation identity/cover and woody encroachment from independent Seoyeongari field/imagery evidence before assigning K_terr or canopy interception;
- if independent site evidence supports forest/shrub encroachment, choose the ET/interception representation from external vegetation-specific evidence rather than pond-area rank.

## References

- Pereira LS, Paredes P, Espirito-Santo D. 2024. Crop coefficients of natural wetlands and riparian vegetation. Irrigation Science. DOI: 10.1007/s00271-024-00923-9.
- Drexler JZ et al. 2004. A review of models and micrometeorological methods used to estimate wetland evapotranspiration. Hydrological Processes. DOI: 10.1002/hyp.1462.
- Mohamed YA et al. 2012. Wetland versus open-water evaporation. Physics and Chemistry of the Earth. DOI: 10.1016/j.pce.2011.08.005.

## Data contract

- observed pond-area years: 2013, 2015, 2017, 2019, 2021, 2023;
- 2011: initial/reference only;
- 2022 pond-area observation: absent;
- observation variable: mapped open-water pond surface area;
- observation support: April-May until exact image dates are recovered.
