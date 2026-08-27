# EGHM reference ledger — Supplement 08: pond-area observation provenance, remote-sensing accuracy and uncertainty

Updated: 2026-08-27

## Scope

The current EGHM is fitted/scored against six mapped open-water-area observations (2013, 2015, 2017, 2019, 2021, 2023), with 2011 used only as the initial/reference footprint. Because the central Integrated RMSE is now approximately 29.9 m², observation/map uncertainty is no longer negligible by default and must be documented separately from model error.

This supplement audits what is currently recoverable about the historical area observations and establishes defensible rules for their use.

---

# Q1. Current observational data contract

Current pond-area observations used by EGHM:

- 2013: 2154.430 m²
- 2015: 2147.678 m²
- 2017: 2051.218 m²
- 2019: 2045.159 m²
- 2021: 1965.256 m²
- 2023: 1882.700 m²

2011 is the initial/reference footprint.

**No 2022 pond-area observation exists in the current analysis.**

The old undergraduate thesis contains a 2022 mapped value, but current project rules explicitly remove it from fitting, scoring, holdout, validation, and model selection.

---

# Q2. Recoverable provenance of the historical mapped areas

The archived undergraduate thesis describes the 2011–2023 series as derived from **satellite-image analysis** and uses the mapped changes to examine wetland contraction/terrestrialization.

However, the currently searchable thesis text does not document with sufficient precision:

- image provider/source for each year;
- exact acquisition date for each image;
- native/pansharpened spatial resolution;
- georeferencing/orthorectification accuracy;
- software and digitizing scale;
- exact criterion used to distinguish visible open water / wetland boundary from shadow or vegetation;
- whether the polygons were manually digitized, thresholded, or classified;
- inter-operator or repeated-digitization uncertainty.

Audit classification:

**AREA VALUES RECOVERED / FULL HISTORICAL MAPPING PROVENANCE INCOMPLETE.**

This is not evidence that the polygons are wrong. It means the current reproducibility package cannot yet assign them zero or known error.

Action:
- continue searching archived source imagery, GIS project files, shapefile metadata and notes before final manuscript freeze;
- until recovered, describe historical area observations as mapped estimates rather than error-free ground truth.

---

# Q3. Olofsson et al. (2014) — area estimation and accuracy good practice

Olofsson, P., Foody, G.M., Herold, M., Stehman, S.V., Woodcock, C.E. & Wulder, M.A. (2014). **Good practices for estimating area and assessing accuracy of land change.** *Remote Sensing of Environment*, 148, 42–57. DOI: **10.1016/j.rse.2014.02.015**.

Evidence class: **REMOTE-SENSING ACCURACY / AREA-ESTIMATION BEST PRACTICE**.

Key support:
- mapped land-cover/land-change area and classification accuracy must be treated together;
- credible accuracy assessment requires explicit sampling, response/reference-data design, and analysis;
- map-derived area is not automatically equivalent to true area when classification error exists;
- uncertainty should be quantified where reference sampling permits it.

Use in EGHM:
- supports treating pond polygons as observations with potential mapping uncertainty rather than mathematically exact targets;
- supports documenting source imagery, reference interpretation and independent validation.

Important scale caveat:
- Olofsson et al. is designed largely for thematic land-cover/change mapping over larger regions. For the tiny Seoyeongari pond, its principles are more relevant than its specific sampling estimators; a site-specific boundary uncertainty approach may be preferable.

---

# Q4. Stehman & Foody (2019) — independence and imperfect reference data

Stehman, S.V. & Foody, G.M. (2019). **Key issues in rigorous accuracy assessment of land cover products.** *Remote Sensing of Environment*, 231, 111199. DOI: **10.1016/j.rse.2019.05.018**.

Evidence class: **REMOTE-SENSING ACCURACY REVIEW / REPRODUCIBILITY**.

Key support:
- accuracy assessment requires high-quality reference data, a defensible response design, and transparent analysis;
- imperfect reference data can bias or overstate apparent map accuracy;
- accuracy-assessment methodology must be documented sufficiently for reproducibility;
- using data that are not independent of model/classifier construction can make evaluation over-optimistic.

Use in EGHM:
- direct justification for rejecting circular 2023 RF agreement as an independent validation result;
- supports explicitly documenting the provenance gap in historical area mapping rather than hiding it.

---

# Q5. Foody (2002) — classification-accuracy foundations

Foody, G.M. (2002). **Status of land cover classification accuracy assessment.** *Remote Sensing of Environment*, 80(1), 185–201. DOI: **10.1016/S0034-4257(01)00295-4**.

Evidence class: **REMOTE-SENSING ACCURACY REVIEW**.

Use in EGHM:
- background reference for confusion/error-based classification accuracy and the long-standing need to evaluate thematic maps rather than treating classified boundaries as ground truth.

---

# Q6. Fuller, Morgan & Aichele (2006) — wetland delineation from high-resolution imagery

Fuller, L.M., Morgan, T.R. & Aichele, S.S. (2006). **Wetland Delineation with IKONOS High-Resolution Satellite Imagery, Fort Custer Training Center, Battle Creek, Michigan, 2005.** U.S. Geological Survey Scientific Investigations Report 2006-5051.

Evidence class: **DIRECT WETLAND-MAPPING METHOD / HIGH-RESOLUTION IMAGERY**.

Key support:
- automated supervised/unsupervised image classifications alone did not produce sufficiently reliable wetland boundaries in the case study;
- the final delineation combined high-resolution imagery, automated results, manual interpretation and field verification;
- wetland boundary positions can differ materially even where total mapped wetland area is similar.

Use in EGHM:
- supports visual/manual expert boundary interpretation as potentially defensible for a small complex wetland, provided imagery and criteria are documented;
- cautions against treating an automated classifier as an inherently superior independent truth source.

---

# Q7. National wetland-mapping evidence on pseudo-reference data

Recent national wetland-mapping research using remote sensing and AI emphasizes that boundaries derived by visual interpretation of very-high-resolution imagery can be useful pseudo-reference data but generally have higher uncertainty in class labeling and polygon contours than independent georeferenced field plots. Using the same or closely related interpreted imagery for both training and evaluation may produce over-optimistic accuracy estimates.

Use in EGHM:
- reinforces the requirement for independent validation or repeated delineation if classification accuracy is to be quoted.

---

# Q8. Wetland shoreline positional uncertainty

High-resolution wetland-shoreline studies comparing satellite/aerial boundaries with field surveys show that even high-resolution imagery can produce metre-scale positional uncertainty, and error depends on shoreline slope, vegetation, image timing and water level.

Example:

**Coastal Wetland Shoreline Change Monitoring: A Comparison of Shorelines from High-Resolution WorldView Satellite Imagery, Aerial Imagery, and Field Surveys** (2021), *Remote Sensing* 13, 3030. DOI: **10.3390/rs13153030**.

The study reported approximately metre-scale mean shoreline agreement but substantially larger local deviations under difficult boundary conditions.

Evidence class: **BOUNDARY POSITIONAL-UNCERTAINTY ANALOGUE**.

Use in EGHM:
- demonstrates why a small polygon's area error can be controlled by boundary-position uncertainty even when imagery is high resolution;
- supports quantifying boundary-position uncertainty rather than assigning a generic percent accuracy.

Domain caveat:
- coastal/tidal wetland shoreline behaviour is not directly transferable to a small montane pond; use only for the methodological principle that mapped shoreline position has nonzero uncertainty.

---

# Q9. Thieler & Danforth (1994) — extracting change from historical imagery

Thieler, E.R. & Danforth, W.W. (1994). **Historical shoreline mapping (I): improving techniques and reducing positioning errors.** *Journal of Coastal Research*, 10(3), 549–563.

Evidence class: **HISTORICAL IMAGERY / POSITIONAL ERROR FRAMEWORK**.

Key support:
- historical image/map boundary-change studies contain multiple sources of positional error, including georeferencing, digitization and source-image limitations;
- these errors should be quantified to distinguish technological/mapping noise from true spatial change.

Use in EGHM:
- methodological analogue for historical pond-boundary mapping;
- reinforces the need to recover orthorectification/source resolution and digitization information for each year.

---

# Q10. Polygon-area uncertainty

Recent GIS work explicitly shows that polygon-area estimates have uncertainty related to positional/vertex error and polygon geometry:

**About polygon area uncertainty in GIS and its implications on agro-forestry estimates** (2024), *Ecological Informatics*, 81, 102617. DOI: **10.1016/j.ecoinf.2024.102617**.

Evidence class: **VECTOR AREA-UNCERTAINTY METHOD**.

Use in EGHM:
- supports propagating boundary/vertex uncertainty into polygon area rather than assuming that the numeric GIS area returned to several decimals is known to that precision;
- especially relevant because current pond areas are reported to approximately 0.001–0.01 m² numerical precision while real mapping uncertainty is necessarily much larger.

Important distinction:
- GIS numerical area precision is not observational accuracy.

---

# Q11. Audit of the 2023 Random Forest classification workflow

Archived code: `seoyeongari_rf_plot2023_cells.R`.

The script:

1. uses `plot_2023.shp` cells/polygons as the positive water/lake training label;
2. uses pixels outside `plot_2023.shp` as negative/non-lake training data;
3. trains a Random Forest on RGB-derived spectral/texture features;
4. selects the final water-probability threshold by **maximizing IoU against the same `plot_2023` label mask**;
5. reports precision, recall, IoU and F1 against `plot_2023`.

### Consequence

This workflow is useful for:
- checking whether RGB/texture information can reproduce the manually supplied 2023 label pattern;
- diagnostic visualization of dark forest/shadow confusion;
- producing a reproducible alternative boundary consistent with the supplied training label.

It is **not an independent validation of `plot_2023.shp`** because the reference polygon is used both to generate training labels and to optimize the classification threshold.

Therefore:

**DO NOT report its IoU/F1 as independent evidence that the 2023 observational boundary is accurate.**

This would be circular validation and would conflict with the independence principles emphasized by Stehman & Foody (2019).

The RF workflow can remain in the reproducibility archive as a classification diagnostic.

---

# Q12. Recommended observation-uncertainty protocol for Seoyeongari

Given the very small study area and only six observation years, a full regional Olofsson-style probability sample is unnecessary and may be awkward. A better site-scale protocol is:

## Level 1 — recover source provenance

For each mapped year record:

- image provider/platform;
- acquisition date and season;
- native spatial resolution;
- orthorectification/georegistration metadata;
- coordinate reference system;
- visual/spectral criterion for open-water edge;
- operator/software;
- original polygon file and checksum.

## Level 2 — repeated independent delineation

Where the source image is available:

- have the same operator redraw the pond boundary blindly at least 2–3 times, or preferably use two independent interpreters;
- do not show the previous polygon while redrawing;
- calculate area spread and boundary displacement.

This directly estimates interpretation/digitization uncertainty at the site scale.

## Level 3 — positional-error envelope

For each image, combine known positional-error components where available, such as:

- image pixel/resolution contribution;
- georegistration error;
- manual edge-selection/digitization error.

Propagate these to a boundary buffer / polygon-area envelope rather than inventing a universal percent error.

## Level 4 — model reporting

Keep the current observed area as the central mapped estimate, but report mapping uncertainty separately.

Do **not** refit the model simply to force predictions inside an uncertainty envelope.

If uncertainty is quantified, useful diagnostics include:
- RMSE relative to mapping uncertainty;
- number of model predictions falling within observation intervals;
- sensitivity of scenario ranking to plausible observation perturbations.

---

# Q13. Implication for current 29.9 m² Integrated RMSE

At present there is **no defensible basis to state that 29.9 m² is larger or smaller than observational mapping uncertainty**, because the historical imagery and delineation-error metadata have not yet been fully recovered.

Therefore the central manuscript should currently say:

> Model fit was evaluated against mapped open-water-area estimates from six observation years. Because full historical image/delineation uncertainty could not yet be reconstructed, RMSE represents disagreement with the mapped estimates rather than error relative to an assumed error-free ground truth.

If source imagery is recovered, this statement can be strengthened with explicit observation intervals.

---

# Q14. Decimal precision rule

Historical GIS calculations produce areas with many decimal places, but final manuscript tables should not imply centimetre-scale boundary accuracy.

Recommended reporting:
- keep full values internally for reproducibility/calculation;
- present pond areas to approximately **1 m²** or another precision justified by the eventual image-resolution audit;
- preserve raw shapefile-computed values in supplementary data.

This separates numerical precision from measurement accuracy.

---

# Q15. Highest-priority data recovery after this audit

1. Original historical source images for 2011, 2013, 2015, 2017, 2019, 2021 and 2023.
2. Original corresponding pond polygons/shapefiles for each year.
3. GIS project or notes that identify image platform, acquisition dates and digitization criteria.
4. Any repeated/manual validation files generated during the original thesis work.
5. Independent 2023 field/drone boundary evidence, if one exists, that was **not** derived from `plot_2023.shp`.

Until those are recovered, the model itself should not be structurally modified in response to unknown observation error.

---

# Q16. Net judgement

**The six-year observation series remains usable, but its uncertainty is presently under-documented.**

This is a reporting/provenance priority rather than a reason to discard the model or the area series.

The 2023 RF workflow is not an independent accuracy assessment and must not be presented as one.

The next scientifically valuable step is source-image/polygon recovery and independent boundary uncertainty estimation. Once that is available, observation uncertainty can be propagated into the scenario comparison without introducing new fitted ecohydrological parameters.
