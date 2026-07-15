# Local Browser API Boundary

## Purpose

Expose the accepted import, run-control, duplicate, correction, and monthly
analysis services through one local, JSON-ready application boundary that the
browser UI can call next. This slice owns the backend application facade and
its persisted run listing; it does not render HTML or start a network listener.

## Local-Only Boundary

- The facade is an in-process request dispatcher. It accepts method, path,
  headers, and bytes and returns a status, headers, and JSON bytes. The frontend
  lane will later attach it to a loopback-only HTTP server and serve static UI
  assets from the same origin.
- No socket binding, network client, CORS allowance, telemetry, subprocess,
  cloud service, OCR process, or system dependency belongs in this slice.
- A per-process CSRF token is returned by `GET /api/session`. Every mutating
  request requires the exact token in `X-Local-Expense-CSRF`; missing or invalid
  tokens fail before any write. Responses never include permissive CORS headers.
- Raw statement bytes and retained source text are never logged or included in
  error messages. Browser JSON may expose structured source locator and parse
  error fields, but not `retained_input`.

## JSON And Exact Money

- Responses are UTF-8 JSON with deterministic key and list ordering.
- Every money field whose Python value is minor units is serialized as a base-10
  string such as `"277617"` or `"-450"`, never a JSON floating-point value.
  Currency remains an explicit uppercase code. Counts remain JSON integers.
- IDs are opaque strings. Dates and timestamps keep their accepted ISO forms.
- Successful responses use `{ "data": ... }`. Errors use
  `{ "error": { "code": ..., "message": ..., "details": ... } }` with no
  traceback or raw input. Validation is 400, missing resources 404, invalid
  state or graph proposals 409, unsupported media 415, oversized uploads 413,
  parser/import failure 422, and unexpected failures 500.

## Request Surface

### Session and read models

- `GET /api/session` returns the CSRF token, `local_only: true`, supported source
  types, maximum upload bytes, canonical categories, and parser modes.
- `GET /api/import-runs` returns all retained import runs newest first, including
  summary counts and state. Run discovery must survive application restarts;
  it cannot depend on browser memory.
- `GET /api/import-runs/{run_id}` returns the run summary and every structured
  detail row, including failed records, locator/error, identity, normalized
  transaction when present, duplicate state, and inclusion reason.
- `GET /api/months` returns effective months newest first.
- `GET /api/months/{YYYY-MM}` returns the accepted month summary contract.
- `GET /api/duplicates` returns every suspected pair and effective decision
  history, enriched with enough left/right transaction date, merchant, exact
  amount, currency, and inclusion state for a human decision.

### Mutations

- `POST /api/import` consumes the raw file bytes, not a filesystem path.
  `X-Statement-Filename` is display text and `Content-Type` is exactly
  `text/csv` or `application/pdf`. Empty bodies, unsupported types, invalid
  filenames, and bodies over the configured limit fail before creating a run.
  A successful import returns 201 with the new run summary/detail. A parser-level
  failure returns 422 with its inspectable failed `run_id` and run detail.
- `POST /api/import-runs/{run_id}/undo` atomically undoes only that run and
  returns its updated summary/detail. Repeated or invalid state changes use 409.
- `POST /api/transactions/{identity_id}/category` accepts a JSON object with
  exactly one canonical `category`, appends one correction, and returns the
  effective state/history.
- `POST /api/duplicates/{duplicate_link_id}/decision` accepts `decision` and
  optional `kept_identity_id`, enforces the centralized graph invariant, and
  returns the enriched effective candidate/history. Rejected proposals append
  nothing and return 409.

## Persisted Run Listing

- Add a typed `CoreStore.list_import_run_summaries()` or equivalent public
  store/service method. It returns the same summary shape as
  `get_import_run_summary`, newest first with a stable run-id tie-breaker.
- Active, failed, and undone runs remain visible. No query physically removes or
  rewrites retained import facts.

## Approved End-To-End Oracle

Tests cross the facade boundary using the committed synthetic fixtures and a
temporary SQLite database:

- CSV import returns one run with 23 records, 22 parsed, one visible
  `missing_amount` failure, and 22 occurrences.
- Text-PDF import returns one run with 12 parsed records and 12 occurrences.
- Both imports yield May `50340` spending / `60000` credits / 12 transactions
  and June `277617` spending / `72999` credits / 22 transactions.
- The two June Tim Hortons records remain distinct and included while pending.
  The Amazon refund and E-Transfer are credits and contribute zero spending.
- Exact CSV re-import creates another inspectable run but leaves June totals and
  transaction counts unchanged.
- A category correction made through the facade survives undo of every active
  support and re-import; per-run undo never removes its history.
- Duplicate mutation routes preserve the accepted centralized component
  invariant and append-only decision history.

## Verification

- Focused API tests cover session/security, import and retained failures, run
  listing/detail/undo, months and exact JSON money, category corrections,
  duplicate decisions, error mapping, and privacy.
- Full backend regression remains green. Evidence records contain only approved
  synthetic assertions, counts, hashes, booleans, and exit codes.

## Non-Goals

- HTML, CSS, browser JavaScript, drag-and-drop, chart rendering, live browser QA,
  or static-file serving.
- A public/LAN server, authentication, remote access, cloud sync, OCR execution,
  scanned receipts, additional bank formats, or raw-statement logging.
