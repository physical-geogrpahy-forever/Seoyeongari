# EGHM reference ledger — Supplement 08: pond-area observation provenance, remote-sensing accuracy and uncertainty

Updated: 2026-08-27

## Scope

The current EGHM is fitted/scored against six mapped open-water-area observations (2013, 2015, 2017, 2019, 2021, 2023), with 2011 used only as the initial/reference footprint. Because the central Integrated RMSE is now approximately 29.9 m², observation/map uncertainty is no longer negligible by default and must be documented separately from model error.

This supplement audits the historical area observations and establishes defensible rules for their use.

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

# Q2. Recovered provenance of the historical mapped areas

The current archived Main body and Supplementary Table A.1 document substantially more mapping provenance than an earlier audit initially recognized.

Recovered method details:

- data provider: **National Geographic Information Institute (NGII; 국토지리정보원), National Geographic Information Platform / 국토정보플랫폼**;
- archived project source URL: `https://map.ngii.go.kr/ms/map/NlipMap.do`;
- source access date recorded in Supplementary Table A.1: **30 April 2024**;
- imagery type: **orthorectified airborne imagery**;
- years: 2011, 2013, 2015, 2017, 2019, 2021, 2023;
- acquisition season: **April or May** according to image metadata;
- spatial resolution: **0.5 m** in the study's archived metadata/method record;
- GIS software: **QGIS 3.26.2**;
- response design: water-body boundaries were **manually interpreted and digitized** for each temporal image;
- area was calculated from the resulting digitized polygons.

Therefore the historical observations are not undocumented satellite-classification outputs. They are NGII-sourced spring orthorectified airborne-image manual delineations.

NGII independently documents that it has operated nationwide digital aerial photography since 2004 and nationwide orthophoto/orthogonal imagery production since 2010, with the products distributed through the National Geographic Information Platform. That institutional documentation supports the provenance of the image source, although the exact year-specific flight records used in this study still need to be recovered from the project/source metadata.

What still remains to be recovered for a complete reproducibility/uncertainty package:

- year-specific NGII dataset/product identifier;
- exact acquisition date for each image;
- orthorectification/georegistration accuracy or RMSE metadata for each selected image/product;
- original source-image files or archived download package and checksums;
- operator/digitizing scale and explicit edge criterion for mixed vegetation/shadow margins;
- inter-operator or repeated-digitization uncertainty;
- checksums and source paths for all original year-specific polygon files.

Audit classification:

**PROVIDER + CORE MAPPING METHOD RECOVERED / YEAR-SPECIFIC POSITIONAL AND INTERPRETATION UNCERTAINTY NOT YET QUANTIFIED.**

This is a materially stronger provenance status than “method unknown.”

---

# Q3. Olofsson et al. (2014) — area estimation and accuracy good practice

Olofsson, P., Foody, G.M., Herold, M., Stehman, S.V., Woodcock, C.E. & Wulder, M.A. (2014). **Good practices for estimating area and assessing accuracy of land change.** *Remote Sensing of Environment*, 148, 42–57. DOI: **10.1016/j.rse.2014.02.015**.

Evidence class: **REMOTE-SENSING ACCURACY / AREA-ESTIMATION BEST PRACTICE**.

Key support:
- mapped land-cover/land-change area and mapping accuracy must be considered together;
- credible accuracy assessment requires explicit reference/response design and analysis;
- map-derived area is not automatically equivalent to true area when boundary/classification error exists;
- uncertainty should be quantified where reference information permits it.

Use in EGHM:
- supports treating the manual pond polygons as mapped observations with nonzero positional/interpretation uncertainty rather than mathematically exact ground truth;
- supports documenting source imagery, interpretation rules and independent validation.

Important scale caveat:
- Olofsson et al. addresses thematic mapping mostly at larger spatial scales. For the small Seoyeongari pond, its principles are more applicable than its regional probability-sampling formulas; a boundary-position/repeated-delineation approach is more natural.

---

# Q4. Stehman & Foody (2019) — independence and imperfect reference data

Stehman, S.V. & Foody, G.M. (2019). **Key issues in rigorous accuracy assessment of land cover products.** *Remote Sensing of Environment*, 231, 111199. DOI: **10.1016/j.rse.2019.05.018**.

Evidence class: **REMOTE-SENSING ACCURACY REVIEW / REPRODUCIBILITY**.

Key support:
- accuracy assessment requires high-quality reference data and a defensible response design;
- imperfect reference data can bias or overstate apparent map accuracy;
- assessment methodology must be documented for reproducibility;
- using the same labels in classifier construction and evaluation can make apparent performance over-optimistic.

Use in EGHM:
- direct justification for rejecting circular 2023 RF agreement as an independent validation result;
- supports keeping manual historical polygons as observations while separately quantifying their uncertainty.

---

# Q5. Foody (2002) — classification-accuracy foundations

Foody, G.M. (2002). **Status of land cover classification accuracy assessment.** *Remote Sensing of Environment*, 80(1), 185–201. DOI: **10.1016/S0034-4257(01)00295-4**.

Evidence class: **REMOTE-SENSING ACCURACY REVIEW**.

Use in EGHM:
- background reference for error-based accuracy assessment and the general distinction between a mapped class boundary and error-free ground truth.

---

# Q6. Fuller, Morgan & Aichele (2006) — wetland delineation from high-resolution imagery

Fuller, L.M., Morgan, T.R. & Aichele, S.S. (2006). **Wetland Delineation with IKONOS High-Resolution Satellite Imagery, Fort Custer Training Center, Battle Creek, Michigan, 2005.** U.S. Geological Survey Scientific Investigations Report 2006-5051.

Evidence class: **DIRECT WETLAND-MAPPING METHOD / HIGH-RESOLUTION IMAGERY**.

Key support:
- automated image classifications alone did not necessarily provide reliable wetland boundaries;
- final delineation benefited from high-resolution imagery, manual interpretation and field/reference information;
- boundary positions can differ materially even where total mapped area is similar.

Use in EGHM:
- supports expert manual interpretation as a defensible method for a small, complex water/wetland boundary when source imagery and criteria are documented;
- cautions against assuming an automated classifier is inherently a more independent truth source.

---

# Q7. Boundary positional uncertainty

Wetland/waterline studies comparing high-resolution imagery with field or independent reference boundaries show that mapped shoreline/wetland boundaries retain nonzero positional uncertainty due to spatial resolution, georegistration, slope, vegetation and image timing.

Example:

**Coastal Wetland Shoreline Change Monitoring: A Comparison of Shorelines from High-Resolution WorldView Satellite Imagery, Aerial Imagery, and Field Surveys** (2021), *Remote Sensing* 13, 3030. DOI: **10.3390/rs13153030**.

Evidence class: **BOUNDARY POSITIONAL-UNCERTAINTY ANALOGUE**.

Use in EGHM:
- supports quantifying boundary-position uncertainty rather than assigning a generic percent error;
- relevant even with 0.5-m imagery because mixed shoreline/vegetation pixels and orthorectification error may shift interpreted edges.

Domain caveat:
- coastal shoreline dynamics are not directly transferable to a montane pond; use only for the methodological principle.

---

# Q8. Thieler & Danforth (1994) — historical imagery positioning error

Thieler, E.R. & Danforth, W.W. (1994). **Historical shoreline mapping (I): improving techniques and reducing positioning errors.** *Journal of Coastal Research*, 10(3), 549–563.

Evidence class: **HISTORICAL IMAGERY / POSITIONAL ERROR FRAMEWORK**.

Key support:
- historical boundary-change studies contain source-image, georeferencing and digitization errors;
- these components should be documented/quantified to distinguish mapping noise from true change.

Use in EGHM:
- methodological analogue for the seven-date airborne-image pond series.

---

# Q9. Polygon-area uncertainty

**About polygon area uncertainty in GIS and its implications on agro-forestry estimates** (2024), *Ecological Informatics*, 81, 102617. DOI: **10.1016/j.ecoinf.2024.102617**.

Evidence class: **VECTOR AREA-UNCERTAINTY METHOD**.

Use in EGHM:
- supports propagating boundary/vertex positional uncertainty into polygon-area uncertainty;
- reinforces that GIS-computed areas reported to many decimals have numerical precision, not equivalent observational accuracy.

---

# Q10. Audit of the 2023 Random Forest classification workflow

Archived code: `seoyeongari_rf_plot2023_cells.R`.

The script:

1. uses `plot_2023.shp` as the positive water/lake training label;
2. uses pixels outside `plot_2023.shp` as negative/non-lake training data;
3. trains a Random Forest on RGB-derived spectral/texture features;
4. selects the final probability threshold by maximizing IoU against the same `plot_2023` label mask;
5. reports precision, recall, IoU and F1 against `plot_2023`.

### Consequence

This workflow is useful for:
- testing whether RGB/texture information reproduces the manually supplied 2023 label pattern;
- diagnosing dark-forest/shadow confusion;
- generating a reproducible classifier consistent with the supplied label.

It is **not an independent validation of `plot_2023.shp`**, because the polygon provides both training/reference information and threshold-selection information.

Therefore:

**DO NOT report its IoU/F1 as independent evidence that the 2023 observational boundary is accurate.**

The RF workflow remains useful as a classification diagnostic only.

---

# Q11. Temporal support of the observations — important unresolved point

The seven historical polygons are **snapshots from April or May**, whereas the current Stage49–52 evaluation feature uses a **May–June mean** for the six evaluation years. This aggregation was adopted while exact year-specific image dates were unavailable, but it is not equivalent to a dated airborne-image observation.

Therefore:
- the May–June mean must not be described as if it were the image acquisition date;
- exact NGII acquisition dates should be recovered if possible;
- until exact dates are recovered, evaluation-window sensitivity (e.g. April, May, April–May, May–June) should be reported as a methodological robustness diagnostic without selecting the window that minimizes RMSE.

This is now a higher-priority temporal-support issue than the already recovered image source/resolution information.

---

# Q12. Site-scale uncertainty protocol now appropriate for Seoyeongari

Because the core image method is already known (NGII 0.5-m orthorectified April/May airborne images + manual digitization), the next uncertainty work should be focused rather than reconstructing the whole method from scratch.

## Level 1 — finish metadata recovery

For each year record:

- exact NGII dataset/product identifier;
- exact acquisition date;
- orthorectification/georegistration accuracy;
- CRS;
- source image path/download package and checksum;
- original polygon path/checksum.

## Level 2 — repeated independent delineation

Where the original image is available:

- blindly redraw the water-body boundary 2–3 times, or use a second independent interpreter;
- do not display the previous polygon during redraw;
- calculate area spread and boundary displacement.

This directly estimates manual interpretation/digitization uncertainty.

## Level 3 — positional-error envelope

Combine available components such as:

- 0.5-m image resolution;
- image georegistration/orthorectification RMSE;
- repeated manual edge-selection error.

Propagate these to polygon-area uncertainty using a boundary buffer or Monte Carlo vertex/edge perturbation approach.

Do not invent a universal fixed percentage.

## Level 4 — model reporting

Keep the current mapped area as the central observation and report the uncertainty interval separately.

Do **not** refit EGHM simply to force predictions inside the observational uncertainty envelope.

Useful diagnostics once intervals exist:
- RMSE relative to mapping uncertainty;
- predictions inside/outside mapped-area intervals;
- scenario-ranking stability under plausible observation perturbations.

---

# Q13. Implication for current 29.9 m² Integrated RMSE

The historical mapping method is now sufficiently documented to state that observations come from NGII orthorectified spring airborne imagery manually digitized in QGIS.

However, **there is still no quantified positional/repeated-delineation uncertainty**, so there is not yet a defensible basis to say whether 29.9 m² is above or below observational uncertainty.

Additionally, the current May–June model aggregation is only an approximate temporal support for April/May image snapshots until exact acquisition dates are recovered.

Manuscript-safe wording:

> Open-water areas were manually delineated from NGII orthorectified airborne imagery acquired in April–May. Model error metrics quantify disagreement with these mapped area estimates. Because year-specific acquisition dates and positional/manual delineation uncertainty were not independently reconstructed in the current reproducibility archive, the mapped polygons were not treated as error-free ground truth and the temporal aggregation window was examined separately for robustness.

---

# Q14. Decimal precision rule

Historical GIS calculations produce area values with many decimal places, but final manuscript tables should not imply centimetre-scale boundary accuracy.

Recommended reporting:
- keep full polygon-computed values internally for reproducibility/calculation;
- present pond areas to approximately **1 m²** unless a more precise observation uncertainty is demonstrated;
- preserve the raw values in supplementary/reproducibility data.

---

# Q15. Highest-priority data recovery

1. Exact NGII product identifier and acquisition date for the 2011, 2013, 2015, 2017, 2019, 2021 and 2023 images.
2. Original source image files/download packages and checksums.
3. Original year-specific pond polygons and checksums.
4. Orthorectification/georegistration accuracy metadata.
5. Independent or repeated manual delineations for direct uncertainty estimation.
6. Independent 2023 field/drone boundary evidence, if available and not derived from `plot_2023.shp`.

---

# Q16. Net judgement

**The six-year observation series has a documented provider and core mapping method and remains suitable for the current model comparison.**

Its remaining weaknesses are:
- unquantified positional/manual delineation uncertainty;
- unresolved exact acquisition dates and therefore imperfect model–observation temporal alignment.

The 2023 RF workflow is not an independent accuracy assessment and must not be presented as one.

The next high-value observation/model task is exact-date recovery if possible and, regardless, a non-optimizing evaluation-window robustness analysis.
