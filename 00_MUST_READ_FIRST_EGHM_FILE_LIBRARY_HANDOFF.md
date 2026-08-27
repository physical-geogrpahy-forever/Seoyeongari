# MUST READ FIRST — EGHM File Library / Runtime Handoff Rules

Status: PERMANENT HANDOFF / MANDATORY PRE-FLIGHT
Project: EGHM / Seoyeongari
Created: 2026-08-27

## Mandatory file-access rule

Any new chat working on EGHM / Seoyeongari MUST follow this before concluding that a required file is missing or asking the user to re-upload data.

1. Never equate “not present in current `/mnt/data`” with “file does not exist”.
2. Never treat a semantic `files.search` miss as proof that a file is absent.
3. If the Library folder/path is known, use `files.list` on that exact Library location first.
4. Obtain the real `file_id` returned by `files.list` or `files.search`.
5. Use `files.materialize` with that real `file_id` to copy the raw bytes into `/mnt/data`.
6. After materialization verify byte size, SHA-256, archive integrity and archive member inventory as applicable.
7. Search parent ZIPs / handoff archives before declaring any internal raw file missing.
8. Use `TRULY_MISSING` only after exact Library listing, exact path/file_id, parent archives, latest handoff and runtime mount state are checked.

State vocabulary: `LIBRARY_DIRECT`, `LIBRARY_IN_ARCHIVE`, `RUNTIME_READY`, `RUNTIME_NOT_MOUNTED`, `MATERIALIZE_FAILED`, `REFERENCE_ONLY`, `TRULY_MISSING`.

## Verified recovery archive

- file_id: `file_000000006330820bb97e7d8db9ce6984`
- Library path: `/EGHM/Seoyeongari_RAW_INPUT_RECOVERY_2026-08-27.zip`
- size: 3,146,778 bytes
- verified SHA-256: `187537eae8d61007f032eaeed352f6264f9b2c25eb00b2a7515e70d2bd8c8955`
- ZIP entries: 14
- `ZipFile.testzip() = None`

Verified members include both meteorological raw CSVs, DEM, plot_2011 shapefile set, plot_2023 ZIP and verified plot_2023 shapefile set.

## Meteorological source rule

The raw meteorological observations are TWO files only:

- `OBS_AWS_DD_20250930013603.csv`
- `OBS_ASOS_DD_20250930041037.csv`

`daily_forcing_v5_equations.csv` is a derived reproducibility product, not a third raw meteorological dataset. The correct dependency is AWS + ASOS raw CSVs → V5 forcing equations → derived daily forcing → EGHM/TLMM.

## GitHub consolidation rule

GitHub is the canonical code/workflow location. File Library remains a recovery/provenance layer. The consolidation target is to place every non-drone EGHM working file/data object in GitHub or record an explicit binary transfer exception until the original bytes are committed. Raw drone photographs are the only intentional bulk-data exclusion requested by the user.
