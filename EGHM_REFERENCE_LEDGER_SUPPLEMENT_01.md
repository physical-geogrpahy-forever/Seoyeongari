# EGHM reference ledger — Supplement 01: integrated ecohydrology and terrestrialization

Updated: 2026-08-27

This supplement adds references useful for defending the **Integrated** model as a coupled ecohydrological/biogeomorphic formulation, rather than merely an arithmetic sum of independent corrections.

## J1. van der Valk (1981)

van der Valk, A.G. (1981). **Succession in Wetlands: A Gleasonian Approach.** *Ecology*, 62(3), 688–696. DOI: **10.2307/1937737**.

Evidence class: **DIRECT ECOLOGICAL FORM**.

Key support:
- freshwater wetland succession can be represented using species life-history traits, propagule longevity and establishment requirements;
- changes in environmental conditions alter whether species remain as propagules, become established adults, or disappear;
- succession need not be represented as a deterministic calendar-only sequence.

Use in current EGHM:
- supports moving away from the legacy fixed one-year/five-year calendar succession rule toward hydrologically conditioned establishment;
- complements Casanova & Brock (2000), Nicol & Ganf (2000), and Webb et al. (2012).

Does not support:
- exact `r_est = 0.05 yr-1`;
- exact `est_window = 7 d`.

## J2. Wheeler & Proctor (2000)

Wheeler, B.D. & Proctor, M.C.F. (2000). **Ecological gradients, subdivisions and terminology of north-west European mires.** *Journal of Ecology*, 88. DOI: **10.1046/j.1365-2745.2000.00455.x**.

Evidence class: **TERRESTRIALIZATION / HYDROSERE CONTEXT**.

Key support:
- reviews the long-established hydrosere concept in which open water can be progressively encroached by emergent/fen vegetation and later more terrestrial communities;
- links continued peat accumulation and declining contact with minerotrophic water to longer-term mire development.

Use in current EGHM:
- supports the broad process interpretation of open-water terrestrialization and vegetation encroachment;
- should be used as conceptual background, not as evidence for a fixed chronological succession schedule.

## J3. Morris, Belyea & Baird (2011)

Morris, P.J., Belyea, L.R. & Baird, A.J. (2011). **Ecohydrological feedbacks in peatland development: a theoretical modelling study.** *Journal of Ecology*, 99, 1190–1201. DOI: **10.1111/j.1365-2745.2011.01842.x**.

Evidence class: **DIRECT INTEGRATED PROCESS FORM**.

Key support:
- peatlands are coupled ecohydrological systems rather than separable hydrological and ecological subsystems;
- long-term peatland development depends on feedbacks among water-table/oxic-zone conditions, organic-matter addition and decomposition, hydraulic properties, drainage, and lateral expansion;
- omitting feedback links can change long-term development behaviour.

Use in current EGHM:
- strong conceptual support for an Integrated scenario in which hydrology controls vegetation establishment while peat accumulation alters the surface expression of open water;
- supports the *existence of coupling*, not the exact simplified form or parameter values used in EGHM.

## J4. Waddington et al. (2015)

Waddington, J.M., Morris, P.J., Kettridge, N., Granath, G., Thompson, D.K. & Moore, P.A. (2015). **Hydrological feedbacks in northern peatlands.** *Ecohydrology*, 8, 113–127. DOI: **10.1002/eco.1493**.

Evidence class: **REVIEW / INTEGRATED ECOHYDROLOGY**.

Key support:
- water-table dynamics, vegetation, peat physical properties, decomposition and water storage participate in interacting autogenic feedbacks;
- peatlands show both fast hydrological feedbacks and slower vegetation/decomposition feedbacks;
- water-table depth is a central predictor linking ecological, hydrological and biogeochemical processes.

Use in current EGHM:
- supports the study's basic premise that hydrological, ecological and geomorphic/peat processes should be considered jointly;
- useful Discussion reference for why Integrated effects may differ from isolated Hydrosere or Eco-Geo processes.

Climate/domain caveat:
- synthesis is focused on northern peatlands; use for process theory, not for direct transfer of rates to subtropical/montane Jeju.

## J5. Malhotra et al. (2016)

Malhotra, A., Roulet, N.T., Wilson, P., Giroux-Bougard, X. & Harris, L.I. (2016). **Ecohydrological feedbacks in peatlands: an empirical test of the relationship among vegetation, microtopography and water table.** *Ecohydrology*, 9, 1346–1357. DOI: **10.1002/eco.1731**.

Evidence class: **EMPIRICAL INTEGRATED PROCESS SUPPORT**.

Key support:
- empirical associations among vegetation composition, water-table depth and microtopography;
- supports theories in which vegetation, hydrology and peatland surface form are mutually related;
- feedback strength varies spatially, cautioning against universal fixed coupling coefficients.

Use in current EGHM:
- empirical reinforcement that hydrology–vegetation–surface-form coupling is real;
- also reinforces the decision to avoid introducing a universal fitted peat–vegetation feedback coefficient without site observations.

## J6. Lamers et al. (2015)

Lamers, L.P.M. et al. (2015). **Ecological restoration of rich fens in Europe and North America: from trial and error to an evidence-based approach.** *Biological Reviews*. DOI: **10.1111/brv.12102**.

Evidence class: **TERRESTRIALIZATION / FEN PROCESS REVIEW**.

Key support:
- explicitly discusses hydrosere/terrestrialization from shallow open water to floating/rich fen systems;
- emphasizes hydrology, biogeochemistry and vegetation interactions in fen development.

Use in current EGHM:
- useful modern review-level support for terrestrialization as an ecologically recognized process;
- domain/type differences mean it should not constrain Seoyeongari rate parameters.

---

# Why these references matter for scenario comparison

The four scenarios in the current model should be interpreted as **process-ablation experiments**:

- **Baseline**: short-term hydrologic expression only;
- **Hydrosere Only**: adds hydroperiod-conditioned ecological occupation;
- **Eco-Geo Only**: adds persistent peat/surface-elevation proxy effect;
- **Integrated**: retains both coupled long-term mechanisms.

The references above establish that hydrology, vegetation succession/establishment, peat formation, microtopography and water-table dynamics are recognized as coupled processes in wetland/peatland science. They therefore support the *scientific rationale for testing an Integrated configuration*.

They do **not** prove in advance that Integrated must fit Seoyeongari best. Scenario ranking must remain an empirical model output.

# Manuscript-safe wording

Recommended:

> Wetland and peatland development is governed by coupled feedbacks among hydrological regime, plant establishment, organic-matter accumulation, and surface microtopography (van der Valk, 1981; Morris et al., 2011; Waddington et al., 2015; Malhotra et al., 2016). Accordingly, the Integrated scenario was formulated to test the combined contribution of hydrosere development and persistent peat-related surface change, rather than assuming that either mechanism operates independently.

Avoid:

> Previous studies prove that the Integrated model is correct/best.

The literature supports the process hypothesis; the Seoyeongari observations determine whether the Integrated configuration performs better in this case.
