# Tracker

Phase dashboard for the loop. Keep checkpoints small and verifiable. Use the status legend so the doctor and other lanes can read progress mechanically.

## Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` done and verified
- `[!]` blocked

## Checkpoints

- [x] Confirm objective, Done-When, standing data invariants, operating flow, and approved synthetic input shape.
- [x] Implement local ingestion, raw/normalized storage, source traceability, deduplication, and reversible `run_id` import units.
- [x] Implement categorization, persistent human corrections, monthly aggregation, and API contracts.
- [x] Implement browser import/review flows and the monthly dashboard with reconciled pie-chart data.
- [~] Pass independent acceptance/privacy review and human QA on the live local application.

## Done When

- [ ] Browser file selection and drag-and-drop import text-based PDF and CSV statements without a path textbox.
- [ ] Parseable transactions are stored; unparseable rows are retained and visibly reported rather than silently dropped.
- [ ] Re-import does not double-count, and suspected duplicate decisions are visible and user-correctable.
- [ ] Automatic categories can be corrected, and human corrections survive later imports and processing runs.
- [ ] Monthly total, category breakdown, transaction list, and pie chart reconcile exactly.
- [ ] Transactions and aggregates trace to their source file and CSV row or PDF page/record.
- [ ] Each import has a `run_id`, can be inspected as a unit, and can be undone without losing manual correction history.
- [ ] The app runs locally without default data upload, with automated verification and reproducible startup instructions.

## Notes

- OCR remains an extension boundary only for this MVP; installing a system OCR engine requires explicit human approval.
- REQ-20260712-200417-data-eng accepted the SQLite core foundation at commit `0ea7be5`; ingestion/parsing, deduplication decisions, categorization, aggregation, API, and UI remain unchecked work.
- The human approved the operating flow and two wholly synthetic TD-style fixtures on 2026-07-13. These fixtures may be committed and are the end-to-end input for the ingestion slice; the real TD statement remains final-local-QA only.
- REQ-20260713-073512-data-eng accepted the CSV/text-PDF ingestion slice at commit `06ac048`: backend 31/31, frozen numeric matrix 282/282, independent review PASS, and `max_fix_cycles` restored to 3.
- REQ-20260714-064051-data-eng accepted the analysis core at commit `9268a5e`: frozen public-write and component-state matrices passed 145/145 and 56/56, backend discovery passed 52/52, independent review returned PASS, and `max_fix_cycles` was restored to 3.
- REQ-20260715-082547-data-eng accepted the local JSON-ready facade at `0362cb0`: independent review PASS, unchanged boundary acceptance 4/4, backend discovery 68/68, exact string money, persistent run listing, and all local-only invariants preserved.
- Record verification commands, evidence paths, and blockers next to each checkpoint as it closes.
