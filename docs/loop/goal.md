# Goal

## Objective

Build a local-first Canadian monthly expense analysis web application that imports text-based bank-statement PDFs and CSV files, preserves and normalizes their transactions, identifies duplicates, categorizes spending, and presents auditable monthly totals and category breakdowns including a pie chart.

## Done When

- [ ] A user can select or drag text-based PDF and CSV statement files into the browser and import them without entering a filesystem path.
- [ ] Every parseable transaction is stored locally, while rows that cannot be parsed are retained and shown with a clear error instead of being silently dropped.
- [ ] Re-importing the same statement does not double-count transactions; suspected duplicates are visible and can be confirmed or rejected by the user.
- [ ] Transactions receive an automatic category, the user can correct categories, and those corrections survive later imports and processing runs.
- [ ] For a selected month, the total, category breakdown, transaction list, and pie chart reconcile exactly to the same included transactions.
- [ ] Every transaction and displayed aggregate can be traced to its source file and original CSV row or PDF page/record.
- [ ] Every import is an independently identifiable unit with a `run_id`; the user can inspect all transactions introduced by a run and undo the entire run without losing the user's manual correction history.
- [ ] The application runs locally, does not upload financial data by default, has automated verification for its core and user-visible behavior, and includes reproducible local startup instructions.

## Invariants

- Pending human confirmation. No implementation request may be created until the standing data invariants are agreed.

## Out Of Scope

- OCR execution for scanned receipts in this MVP; define an extension boundary, but do not install an OCR engine or process receipt images yet.
- Direct bank-account connections, cloud synchronization, multi-user accounts, authentication, mobile-native applications, tax filing, or financial advice.

## Verification Surface

- Backend/core tests for PDF and CSV field correctness, normalization, add-only ingest behavior, deduplication, categorization, `run_id` inspection, reversible import runs, correction persistence, aggregation reconciliation, and source traceability.
- Frontend tests for browser file selection/drag-and-drop, import review, duplicate review, manual corrections, month filtering, totals, and pie-chart data.
- Independent end-to-end acceptance and privacy checks, followed by the required human-QA pass against a live local instance.

## Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` done and verified
- `[!]` blocked

## Auto-Chain Permission

auto_chain_next_session: false
