# Tracker

Phase dashboard for the loop. Keep checkpoints small and verifiable. Use the status legend so the doctor and other lanes can read progress mechanically.

## Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` done and verified
- `[!]` blocked

## Checkpoints

- [~] Confirm objective, Done-When, standing data invariants, operating flow, and approved redacted input shape.
- [ ] Implement local ingestion, raw/normalized storage, source traceability, deduplication, and reversible `run_id` import units.
- [ ] Implement categorization, persistent human corrections, monthly aggregation, and API contracts.
- [ ] Implement browser import/review flows and the monthly dashboard with reconciled pie-chart data.
- [ ] Pass independent acceptance/privacy review and human QA on the live local application.

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
- Record verification commands, evidence paths, and blockers next to each checkpoint as it closes.
