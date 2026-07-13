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

- **INV-1 — No silent data loss.** Preserve every source record, including records that cannot be parsed, categorized, or are suspected duplicates; represent their state explicitly instead of dropping them.
- **INV-2 — Human edits outrank automation.** A human category, duplicate decision, or other correction must survive re-import and automated reprocessing and must never be silently overwritten.
- **INV-3 — Machine ingest is add-only.** Automated import must not physically delete or silently overwrite raw or normalized records; deduplication and undo use explicit links and states.
- **INV-4 — Import runs are independently recoverable.** Every import has a `run_id`, exposes the records it introduced, and can be undone as a unit. Manual correction history is stored independently so undo and later re-import do not erase it.
- **INV-5 — No double counting.** The same real-world transaction is included at most once in any monthly result, while every suspected duplicate record remains inspectable.
- **INV-6 — Every number is traceable.** Each transaction and aggregate must trace to its source, import run, applied category/duplicate decision, and inclusion or exclusion reason.
- **INV-7 — Money is exact.** Store amounts as integer minor units or exact decimals with their original currency; prohibit binary floating-point amounts and implicit exchange-rate conversion.
- **INV-8 — Financial data stays local.** Raw statements and transaction data are not uploaded, written to application logs, or committed to Git.

## Out Of Scope

- OCR execution for scanned receipts in this MVP; define an extension boundary, but do not install an OCR engine or process receipt images yet.
- Direct bank-account connections, cloud synchronization, multi-user accounts, authentication, mobile-native applications, tax filing, or financial advice.

## Verification Surface

- Backend/core tests for PDF and CSV field correctness, normalization, add-only ingest behavior, deduplication, categorization, `run_id` inspection, reversible import runs, correction persistence, aggregation reconciliation, and source traceability.
- Frontend tests for browser file selection/drag-and-drop, import review, duplicate review, manual corrections, month filtering, totals, and pie-chart data.
- Independent end-to-end acceptance and privacy checks, followed by the required human-QA pass against a live local instance.

## Confirmed Operating Flow

1. Open the local web application and drag in, or select, one or more statement files.
2. Review an import summary showing successful transactions, failed source records, and suspected duplicates.
3. Inspect the records introduced by any `run_id`, and undo an entire import when needed.
4. Land on the most recent month with data by default, see the monthly total and category pie chart first, then drill into category and transaction details.

## Approved Test Inputs

- The synthetic TD-style CSV and text-PDF statements described in `docs/product/import-pipeline.md` are explicitly approved for verbatim test-fixture use and repository commits.
- The human's real TD statement is not an approved fixture. It remains private and may be used only for final local human verification under INV-8.

## Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` done and verified
- `[!]` blocked

## Auto-Chain Permission

auto_chain_next_session: false
