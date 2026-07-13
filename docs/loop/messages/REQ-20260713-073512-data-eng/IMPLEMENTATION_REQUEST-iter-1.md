# IMPLEMENTATION_REQUEST

message_type: IMPLEMENTATION_REQUEST
request_id: REQ-20260713-073512-data-eng
parent_request_id:
iteration: 1
from_lane: product
to_lane: data-eng
status: REQUESTED
created_at: 2026-07-13T07:35:12Z
source_docs:
- docs/loop/goal.md
- docs/loop/tracker.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/core-foundation.md
- docs/product/import-pipeline.md
design_system:
- none; this is non-UI work and the human disabled optional design, Superpowers, and visualization-companion skills.
goal: Implement the bounded local TD-style CSV and text-PDF import pipeline against the two authorized synthetic fixtures, including field-correct normalization, explicit failures, exact re-import idempotency, suspected-duplicate visibility, run inspection, and reversible run semantics.
user_facing: false
scope:
- backend/**
- contracts/**
- tests/backend/**
- docs/loop/lanes/data-eng/**
non_goals:
- Do not implement categories, monthly aggregation, an HTTP server/API, browser UI, charts, or manual duplicate-resolution UX.
- Do not support arbitrary bank formats beyond the two approved TD-style shapes.
- Do not install or invoke OCR or any other system-level dependency, and do not process scanned receipts.
- Do not inspect or copy the human's real TD statement.
- Do not change the approved invariants or redesign the already accepted core outside what this import slice requires.
invariants:
- INV-1 no silent data loss: preserve all 23 CSV data rows with exactly one explicit `missing_amount` failure and all 12 PDF transaction records. VERIFY `python -m unittest tests.backend.test_statement_import_csv -v` and VERIFY `python -m unittest tests.backend.test_statement_import_pdf -v` (fail on a dropped candidate record or hidden parse failure).
- INV-2 human edits outrank automation: a correction attached to an imported stable identity survives exact re-import, undo of one or all supporting runs, and a later re-import. VERIFY `python -m unittest tests.backend.test_statement_import_runs -v` (fails on missing or overwritten correction history).
- INV-3 machine ingest is add-only: exact re-import and undo retain source records, identities, occurrences, and duplicate links. VERIFY `python -m unittest tests.backend.test_statement_import_idempotency -v` and VERIFY `python -m unittest tests.backend.test_statement_import_runs -v` (fail on physical deletion or silent overwrite).
- INV-4 independently recoverable import runs: every attempt has a distinct inspectable `run_id`; undo is atomic and only removes that run's active support. VERIFY `python -m unittest tests.backend.test_statement_import_runs -v` (fails on cross-run leakage, partial undo, or an uninspectable run).
- INV-5 no double counting: exact re-imports share stable identities, while the two legitimate same-day/same-price Tim Hortons records remain distinct and included. VERIFY `python -m unittest tests.backend.test_statement_import_idempotency -v` (fails when effective counts grow on re-import or legal lookalikes merge).
- INV-6 every number is traceable: normalized and effective records expose run, content fingerprint, source locator, identity, duplicate state, and inclusion reason. VERIFY `python -m unittest tests.backend.test_statement_import_runs -v` (fails when provenance or state is missing).
- INV-7 exact money: debits are negative integer CAD cents and credits are positive; Amazon refund `+12999` and E-Transfer income `+60000` are not spending. VERIFY `python -m unittest tests.backend.test_statement_import_csv -v` and VERIFY `python -m unittest tests.backend.test_statement_import_pdf -v` (fail on float storage, sign reversal, or implicit FX).
- INV-8 local data boundary: import accepts local bytes, has no network/telemetry/OCR path, and never logs retained statement content. VERIFY `python -m unittest tests.backend.test_statement_import_local_boundary -v` (fails on a network client, OCR invocation, raw-content log, or path-only input contract).
acceptance_criteria:
- The two approved files are copied byte-for-byte into `tests/backend/fixtures/` with their pinned SHA-256 hashes, so tests do not depend on `expense-app-loop-mock`. VERIFY `python -m unittest tests.backend.test_statement_fixtures -v` (fails on a missing fixture or hash mismatch).
- Importing the CSV bytes creates one distinct run with 23 source records, 22 normalized transactions, and one visible `missing_amount` failure; every parsed date is a valid ISO day, every merchant is non-empty/non-numeric, ordinary debits are negative integer CAD cents, and the Amazon refund/E-Transfer credits are `+12999`/`+60000` and not spending. VERIFY `python -m unittest tests.backend.test_statement_import_csv -v` (fails on any count, field, locator, sign, or failure-report mismatch).
- Importing the text-PDF bytes creates one distinct run with 12 parsed transactions and no failed transaction record; every date/merchant is field-correct, the received E-Transfer is `+60000` CAD cents, and the other 11 records are debits with PDF page/record provenance. VERIFY `python -m unittest tests.backend.test_statement_import_pdf -v` (fails on zero rows, garbage fields, sign reversal, or missing page provenance).
- Re-importing identical bytes, including under a renamed filename, creates a new inspectable run without increasing effective transaction identities: CSV remains 22, PDF remains 12, and both together remain 34. The two legal Tim Hortons rows remain distinct/included and appear as an inspectable suspected-duplicate pair rather than being silently merged; shared merchants across May and June remain distinct. VERIFY `python -m unittest tests.backend.test_statement_import_idempotency -v` (fails on double count, missing exact-reimport linkage, auto-exclusion of a suspected pair, or cross-month merge).
- Run summary/detail exposes source name/type/fingerprint, counts, every source locator and parse result, normalized transaction, stable identity, duplicate state, and inclusion/exclusion reason. Undoing one of two supporting exact-import runs leaves the effective identity present; undoing all supporting runs removes it from effective results without deleting facts, and correction history survives a later re-import. VERIFY `python -m unittest tests.backend.test_statement_import_runs -v` (fails on incomplete inspection, non-atomic undo, lost history, or incorrect active-support semantics).
- The import boundary accepts bytes plus filename/type for later browser integration, records a text-parser extension boundary, uses only project-level Python dependencies, and has no OCR/system dependency, network upload, telemetry, or raw-statement logging. VERIFY `python -m unittest tests.backend.test_statement_import_local_boundary -v` (fails on a path-only contract, forbidden dependency/call, network surface, or leaked retained text).
- All existing and new backend tests pass together. VERIFY `python -m unittest discover -s tests/backend -p "test_*.py" -v` (fails on any core-foundation or import regression).
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: pending
- sent_at:
expected_reply:
- implementation commit and changed files
- parser, identity, duplicate, and run-query API decisions
- exact verification commands, exit codes, and flat evidence paths for every declared VERIFY command
- blockers, especially any missing dependency classified as pip versus system
- IMPLEMENTATION_DONE to product followed by REVIEW_REQUEST to the registered review lane when all evidence is green
