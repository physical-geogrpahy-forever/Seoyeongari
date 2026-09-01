# Stage55 decision log — observation temporal support

Updated: 2026-08-27

## External reason for the audit

The historical open-water polygons were manually digitized from NGII orthorectified airborne images. Archived manuscript metadata states that all images were acquired in **April or May**. The current Stage49–52 model, however, aggregates ecological and hydrological observation features over **May–June** because exact year-specific image dates had not been recovered.

Stage55 tested whether this temporal-support mismatch controls the scenario conclusion. No alternative time window was chosen by fit, and no process parameter was changed.

## Tested windows

- April
- May
- April–May
- May–June (current)
- April–June

Two analyses were separated:

1. **fixed transfer** — Stage52 May–June Kc/Kh coefficients locked;
2. **profile refit** — only Kc/Kh refitted, with all hydro/ecological process parameters fixed.

## Results

Integrated ranked first in **all 5/5 windows** under both fixed transfer and profile refit.

| Window | Integrated fixed nRMSE | Hydrosere fixed nRMSE | Integrated profile nRMSE | Hydrosere profile nRMSE |
|---|---:|---:|---:|---:|
| April | 1.525% | 1.585% | 1.507% | 1.582% |
| May | 1.390% | 1.611% | 1.383% | 1.609% |
| April–May | 1.388% | 1.596% | 1.374% | 1.592% |
| May–June | 1.463% | 1.621% | 1.463% | 1.621% |
| April–June | 1.459% | 1.605% | 1.455% | 1.604% |

Thus the Integrated-vs-Hydrosere conclusion is not an artifact of the May–June aggregation.

## Methodological conclusion

The known image temporal support is April/May. Exact acquisition dates still take priority if recovered, but without those dates the **April–May mean is a more defensible provisional observation-support window than May–June**, because June is outside the documented acquisition months.

This decision is based on image metadata, **not because April–May produces a lower RMSE**. The lower RMSE is reported only as a diagnostic outcome.

Therefore the next model revision should rerun the unchanged Stage49 calibration architecture using April–May aggregation from the start. No grid range, physical gate, scenario-rank requirement, or pond-area target is to be altered.

## Important structural diagnostic

The direct hydraulic footprint `A(V)` alone remains a poor predictor of the mapped long-term pond areas (window-dependent nRMSE roughly 53–61%). This is not new in Stage55 and confirms that the calibrated observation operator is doing substantial work to map hydrologic/ecological state to the observed open-water footprint.

Accordingly, the final model should continue to be described as **process-based/semi-mechanistic with calibrated observation operators**, not as a fully physically determined bathymetric model.

## Data contract

- 2011: initial/reference only.
- Observed pond-area targets: 2013, 2015, 2017, 2019, 2021, 2023.
- 2022 pond-area observation: absent.
- Exact image dates: not yet recovered.
- Window selection by fit: prohibited.
