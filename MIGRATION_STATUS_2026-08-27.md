# EGHM → GitHub consolidation status — 2026-08-27

Target repository: `physical-geogrpahy-forever/Seoyeongari`
Working branch: `data-consolidation-2026-08-27`
Base: latest accumulated ChatGPT work branch `chatgpt-stage30-20260826` at commit `d5134b251f975bc7325172931048e1aae807c2ba`.

## User instruction
Move every EGHM working/data/document file to GitHub except raw drone photographs. Model-reconciliation work (Stage79 vs Stage84) is intentionally deferred until migration is complete.

## Already physically present in GitHub
- `OBS_AWS_DD_20250930013603.csv` — 174,481 bytes
- `OBS_ASOS_DD_20250930041037.csv` — 145,841 bytes
- existing model code, ledgers, decision logs, workflows, Stage79 TLMM code and prior GitHub-stage artifacts inherited from `chatgpt-stage30-20260826`
- mandatory file-handoff rule committed on this consolidation branch
- Stage84 handoff/audit/coupling/source-fidelity text artifacts archived on this consolidation branch

## Verified File Library recovery archive
- file_id: `file_000000006330820bb97e7d8db9ce6984`
- path: `/EGHM/Seoyeongari_RAW_INPUT_RECOVERY_2026-08-27.zip`
- size: 3,146,778 bytes
- SHA-256: `187537eae8d61007f032eaeed352f6264f9b2c25eb00b2a7515e70d2bd8c8955`
- ZIP test: PASS (`testzip() = None`)
- 14 members including both raw meteorology CSVs, `dem.tif`, `plot_2011` shapefile set, `plot_2023.zip`, and verified `plot_2023` shapefile set.

## Latest manuscript originals in File Library
These remain authoritative original binaries until the exact bytes are committed to GitHub. Parsed-text exports are being added separately so their contents are always readable from GitHub.

- Main v11: `file_000000008d3481fbb7a1151c25aa19aa`, `/EGHM/2%20-%20Main%20body_R1_science_fixes_v11.docx`, 113,016 bytes
- Supplement v9: `file_00000000597481f8af7b1622d615c0d2`, `/EGHM/4%20-%20Supplementary_R1_methods_v9.docx`, 6,187,948 bytes
- Figures v2_3: `file_00000000d3b082118aea16d2b4621aaa`, `/EGHM/3%20-%20Figures_R1_sync_v2_3.docx`, 6,770,703 bytes
- Response v1: `file_0000000091048209911fcec43c5f720e`, `/EGHM/Response_to_Reviewers_Round1_scientific_draft_v1.docx`, 42,914 bytes
- Revision master log: `file_0000000068448211a26b25996df399dc`, `/EGHM/Seoyeongari_Round1_revision_master_log_v1.md`, 87,057 bytes

## Binary-transfer constraint of the current GitHub connector
The connected GitHub write interface can create/update UTF-8 repository files and Git objects, but it does not expose an action that accepts a local `/mnt/data/...` file path as a binary upload parameter. Therefore DOCX/TIF/SHP/ZIP bytes cannot be bulk-forwarded directly from `files.materialize` by this connector. This is a connector transfer limitation, not a missing-file condition.

Until binary transfer is completed by a file-capable Git/GitHub path, every such object must remain explicitly listed with its real Library `file_id`; new chats must use `files.list → files.materialize` rather than asking the user to re-upload it.

## Completion rule
Do NOT declare migration complete unless every non-drone Library object is either:
1. physically committed in GitHub with original bytes, or
2. explicitly listed here as a binary-transfer exception with its Library file_id/path/size.

Raw drone photographs are the only intentional exclusion.
