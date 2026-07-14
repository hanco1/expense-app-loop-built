# Statement Import Pipeline Slice

## Purpose

Turn browser-supplied statement bytes into local, auditable import runs without losing bad rows or double-counting exact re-imports. This slice covers TD-style CSV and text-PDF ingestion, normalization, exact re-import identity, suspected-duplicate visibility, run inspection, and reversible import units. It does not build the HTTP API or UI.

## Input Boundary

- The core entry point accepts file bytes plus a display filename/type. It must not require a browser-visible filesystem path.
- Supported in this slice: the approved TD-style CSV columns `Date,Description,Debit,Credit,Balance` and the approved TD-style text PDF table.
- Dates normalize to real ISO calendar dates (`YYYY-MM-DD`).
- Merchants/payees remain non-empty, non-numeric text.
- CAD amounts use signed integer cents: withdrawals/debits are negative; deposits, refunds, and income are positive. A positive credit is not spending.
- Each raw Debit or Credit cell is validated by one positive whitelist. It is valid if and only if the token is a decimal number, the value is finite, non-negative with no negative-zero spelling, exactly representable in CAD cents without any context-dependent rounding/underflow/overflow, and within the inclusive SQLite minor-unit range. Every other token is a retained row-level `invalid_amount` and creates no normalized transaction or occurrence.
- Validation must derive validity from that whitelist, not from a list of known failure modes or exception types. Decimal context flags, traps, exponent magnitude, and runtime-specific rounding must not change the result.
- The review-owned iteration-4 matrix locks the accepted decimal-token grammar and both valid and invalid representatives before implementation. It covers ordinary boundaries plus exceptional values, signed zero, subnormal/underflow/overflow forms, fractional cents, long mantissas, grouping/currency text, whitespace, tabs, and scientific notation.
- CSV data rows and PDF transaction lines are source records. Headers and statement metadata are not transaction candidate records.
- Every import attempt creates a distinct opaque `run_id`, even when the file bytes were imported before.

## Approved Synthetic Fixtures

The human explicitly authorized both files for unrestricted test use and verbatim repository fixtures:

| Source | SHA-256 | Expected source records | Parsed | Failed |
| --- | --- | ---: | ---: | ---: |
| `td-mock-2026-06.csv` | `9F93F107DDD02AEE2FB0A0AE19EB962180C680D1FB06D4D90959C96ED8CD7BAA` | 23 | 22 | 1 |
| `td-mock-2026-05.pdf` | `F4B6B524D7C6140EE3F3E24CE87C4A36F0B40619395B5DC17B03F1B99DBC11F8` | 12 | 12 | 0 |

Copy them byte-for-byte to `tests/backend/fixtures/` so verification is self-contained and does not depend on the external mock directory.

### CSV facts that must remain true

- The row `BROKEN ROW NO AMOUNT` is retained with a stable locator and explicit `missing_amount` failure; it produces no normalized transaction but appears in the run report.
- The two `TIM HORTONS #2214 TORONTO ON` rows on 2026-06-01 at CAD 4.50 are two legitimate transactions. They have distinct source locators and stable transaction identities, remain included, and may be surfaced as one suspected-duplicate pair; they are never silently merged or excluded.
- `AMAZON.CA REFUND 702-441` is `+12999` CAD cents and `E-TRANSFER RECEIVED J. WU` is `+60000` CAD cents. Both are credits and must not be classified as spending.
- All ordinary debit rows are negative integer cents.

### PDF facts that must remain true

- The one-page text PDF yields 12 valid May transactions.
- `E-TRANSFER RECEIVED J. WU` is a `+60000` CAD-cent credit; the other 11 transactions are debits.
- Merchants shared with the June CSV remain distinct May transactions. A shared merchant name or equal amount across different dates must not cause an automatic merge.

## Identity, Duplicate, and Effective-Inclusion Semantics

- A stable transaction identity for an exact source occurrence is derived from the content fingerprint and source locator, not from date/merchant/amount alone. Renaming an identical file must not create a second real-world identity.
- Re-importing identical bytes creates a new run and new inspectable source/occurrence records linked to the same stable identities. Effective transaction queries return each identity at most once while at least one active included occurrence supports it.
- Consequently, importing both fixtures once yields 34 effective transactions; re-importing either or both does not raise that count.
- Similar-but-distinct records remain separate identities. Suspected duplicate pairs are inspectable and included by default until a later human decision says otherwise.
- Exact re-import links and suspected-duplicate links are explicit state; no raw or normalized record is physically deleted.

## Run Inspection and Undo

- A run summary exposes its `run_id`, source name/type/fingerprint, state, source-record count, parsed count, failed count, and occurrence count.
- Run detail exposes every source locator, parse status/error, normalized transaction when present, stable identity, duplicate state, and inclusion/exclusion reason.
- Undo is atomic and terminal for the selected run. It retains source records, identities, occurrences, duplicate links, and manual-correction history.
- If the same identity is supported by another active import run, undoing one run does not remove that identity from effective results. Undoing every supporting run does.
- A later re-import restores active support for the same stable identities and sees their existing manual correction history.

## Dependency and Privacy Boundary

- A Python package for text extraction (for example `pypdf`) may be installed and recorded as a project dependency under the data-eng scope.
- Do not install or invoke an OCR engine. Scanned PDFs/receipt images remain a later extension behind a parser boundary.
- Do not add network clients, telemetry, uploads, or raw-statement logging.
- The real TD statement is outside this slice and remains private final-local-QA input only.

## Non-Goals

- General bank-format autodetection beyond the two approved TD-style shapes.
- Categories, monthly aggregation, HTTP endpoints, browser UI, charts, or manual duplicate-resolution UX.
- OCR execution, receipt-image processing, or any system-level dependency.
- Backward migration tooling for databases created before this pre-release slice; all existing core behavior and tests must remain compatible on a fresh database.
