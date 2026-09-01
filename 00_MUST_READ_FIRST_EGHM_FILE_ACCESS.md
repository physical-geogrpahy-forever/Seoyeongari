# MUST READ FIRST — EGHM File Access / Handoff Rule

Status: **MANDATORY PRE-FLIGHT**
Project: **EGHM / Seoyeongari**

Any future ChatGPT/Codex session working on this repository must read and follow this file before declaring that a required input is missing or asking the user to upload it again.

## Binding file-access workflow

1. Do **not** equate `not in /mnt/data` with `does not exist`.
2. Do **not** treat a semantic `files.search` miss as proof of absence.
3. If the ChatGPT File Library path/folder is known, call `files.list` on the exact folder first.
4. Use the real `file_id` returned by `files.list`/`files.search`.
5. Call `files.materialize` with that `file_id` to copy the raw file into `/mnt/data`.
6. After materialization, verify byte size and SHA-256. For ZIPs also run archive-integrity (`ZipFile.testzip()`) and inventory members.
7. Before `TRULY_MISSING`, check exact Library path/file_id, parent ZIPs, latest runtime/handoff archives, and current runtime mount status.
8. Never ask the user to re-upload a known Library file until `files.list -> files.materialize` has actually been attempted and failed.

Recommended status vocabulary:
`LIBRARY_DIRECT`, `LIBRARY_IN_ARCHIVE`, `RUNTIME_READY`, `RUNTIME_NOT_MOUNTED`, `MATERIALIZE_FAILED`, `REFERENCE_ONLY`, `TRULY_MISSING`.

## Verified precedent

Library file:
- `file_000000006330820bb97e7d8db9ce6984`
- `/EGHM/Seoyeongari_RAW_INPUT_RECOVERY_2026-08-27.zip`
- 3,146,778 bytes

Verified sequence:
`files.list(/EGHM/) -> file_id -> files.materialize -> /mnt/data/Seoyeongari_RAW_INPUT_RECOVERY_2026-08-27.zip`

Fresh SHA-256:
`187537eae8d61007f032eaeed352f6264f9b2c25eb00b2a7515e70d2bd8c8955`

ZIP integrity: 14 members; `testzip() = None`.

Key raw members:
- `raw/met/OBS_AWS_DD_20250930013603.csv`
- `raw/met/OBS_ASOS_DD_20250930041037.csv`
- `raw/gis/dem/dem.tif`
- `raw/gis/plot_2011/plot_2011.shp/.shx/.dbf/.prj`
- `raw/gis/plot_2023.zip`
- `raw/gis/plot_2023_verified/plot_2023.shp/.shx/.dbf/.prj/.cpg`

## Meteorology rule

The original meteorological inputs are exactly two raw files:
- `OBS_AWS_DD_20250930013603.csv`
- `OBS_ASOS_DD_20250930041037.csv`

`daily_forcing_v5_equations.csv` is derived output, not a third raw meteorological input. If the two raw CSVs and the established V5 forcing equations are available, absence of the derived CSV must not block model execution.

## Repository note

This GitHub repository already contains the two raw AWS/ASOS CSVs. A future session must check GitHub first for repository-tracked inputs, then File Library for non-repository assets. File Library is a fallback/source archive, not evidence that the project cannot proceed.
