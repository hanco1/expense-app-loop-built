# Local Web Application

## Purpose

Deliver the first complete, locally operated browser experience over the
accepted `LocalWebApi`. A user starts one loopback-only process, opens the
same-origin page, imports CSV or text-PDF statements by file picker or
drag-and-drop, reviews each import run, resolves categories and suspected
duplicates, and sees a monthly dashboard whose totals, list, category buckets,
and pie chart all reconcile.

This is the MVP's user-facing slice. OCR execution remains out of scope.

## Runtime And Local Boundary

- Provide a reproducible command under `frontend/` that starts an HTTP server
  bound only to `127.0.0.1`. It must not bind to `0.0.0.0`, a LAN address, or
  IPv6 wildcard. The database path is an explicit local startup argument and
  continues through the accepted `LocalWebApi.from_database()` guard.
- Serve the HTML, CSS, and JavaScript assets and `/api/**` from the same origin.
  The adapter delegates API requests to `LocalWebApi`; it must not duplicate
  parser, identity, category, duplicate-component, aggregation, or undo logic.
- Reject non-loopback or malformed `Host` headers before dispatch. Do not add
  CORS, remote assets, analytics, telemetry, service workers, cloud calls, or
  statement logging. Use a restrictive content-security policy and security
  headers suitable for local static assets.
- The page fetches `GET /api/session` once per application session and sends
  its exact CSRF token on every mutation. Tokens never enter URLs or logs.
- Startup may print the loopback URL and database location, but never statement
  bytes, retained source input, transaction descriptions, or CSRF tokens.
- The stable human default port must not be the loop dashboard's `8765`; use
  `8766`. Startup must print the URL derived from the listener's actual bound
  address and port (including the allocated port for `--port 0`), and that URL
  must reach this expense app's static page and `/api/session`.
- Listener binding is exclusive. If the requested port is already occupied,
  startup must emit a clear bind error and exit non-zero before printing a
  success URL or entering the serving loop. It must never coexist on one port
  in a state where another process receives the requests.

## Browser Information Architecture

Use one responsive application shell with three primary views:

1. **Overview** — selected month's spending total, credits, transaction count,
   category legend/table, pie chart, and transaction list.
2. **Imports** — drop zone/file picker, current import results, persistent run
   history, per-run details and failed rows, and run-level undo.
3. **Duplicates** — suspected pairs, both transactions' structured context,
   effective state/history, and explicit same/distinct decisions.

The most recent effective month is selected on load. Navigation and all core
actions must work by keyboard and at narrow desktop/mobile widths without
horizontal page scrolling.

## Import And Run Review

- The import control accepts `.csv` and `.pdf` only, through a file picker and
  drag-and-drop. There is no filesystem-path textbox. Multiple selected files
  are imported sequentially as separate runs so each has its own `run_id`.
- Show per-file progress, success, and error state. A successful result exposes
  run ID/state plus parsed, failed, and occurrence counts. An import-level 422
  still links to its inspectable failed run when supplied by the API.
- Run history persists across reloads. Run detail shows every structured row,
  including locator, parse failure code, normalized transaction when present,
  category, duplicate/inclusion state, and provenance. Never show retained raw
  input.
- Undo requires an explicit confirmation naming the run/display filename,
  updates the run in place, refreshes overview/duplicates, and surfaces a
  repeated or stale undo as a non-destructive conflict rather than success.

## Monthly Dashboard And Exact Money

- Use the exact string minor-unit values returned by the API. Formatting may
  produce Canadian-dollar display text, but calculations and pie geometry must
  use integer-safe parsing (`BigInt` or an equivalent exact method), never
  binary floating-point money arithmetic.
- Spending, credits, transaction count, every non-zero category bucket, the
  included transaction list, and the pie chart derive from the same month
  response. Credits are visible but never enter spending or pie slices.
- The category table displays exact amount and percentage. The pie chart has a
  text alternative/legend and a clear zero-spending state; tiny non-zero
  categories remain represented and selectable without changing their amount.
- Exact BigInt allocation and visual SVG coordinates are separate concerns.
  No 1e9-scale accounting unit may be written directly into CSS/SVG length
  geometry. Numerical truth remains the exact amount, percentage, `data-units`,
  and `PIE_SCALE=1000000000`; visual arc angles are a separate derived layer and
  never flow back into those values.
- Every non-zero category receives a minimum visible arc of 1 degree. Categories
  whose exact proportional angle is below 1 degree render at 1 degree; after
  those floors are reserved, the remaining circumference is distributed among
  the larger categories in proportion to their exact spending amounts. This
  water-filling rule preserves the relative proportions of the non-floored
  categories while keeping the rendered arcs gap-free, non-overlapping, and
  exactly one full circumference. The legend/table continues to show exact
  numerical shares, never the visually adjusted angle.
- The rendered chart must show exactly one contiguous, non-repeating visible arc
  per non-zero category. Real-browser acceptance measures each non-zero arc at
  or above the 1-degree visual floor and separately proves exact numerical
  reconciliation; it does not require pixel-exact visual proportionality for a
  category lifted by the floor. For the approved June oracle, nine categories
  render and Housing remains one dominant arc covering more than half the circle.
- Every category amount must equal the sum of its included spending rows, and
  all category amounts must equal the displayed spending total. Tests assert
  reconciliation before any visual assertion.
- Each transaction exposes date, merchant, exact signed amount, currency,
  category/provenance, inclusion state/reason, and its active source supports.
  A canonical category correction is performed in place and refreshes the
  affected month without hiding append-only history.

## Duplicate Decisions

- Show both sides of every candidate with date, merchant, exact signed amount,
  currency, current inclusion, run/source context, and decision history.
- `distinct` requires an explicit user action. `same_transaction` requires the
  user to choose the kept identity. Pending candidates stay visible and both
  sides remain included until decided.
- A 409 graph rejection is shown next to the candidate and must not optimistically
  change either side or append a fake history row. Successful decisions refresh
  duplicates, affected run details, and monthly totals.

## Accessibility And Failure UX

- Use semantic headings, landmarks, tables/lists, labels, buttons, and a visible
  keyboard focus indicator. Status messages use an appropriate live region.
- The drop zone is also operable by keyboard through the labelled file input.
  Do not encode category identity by color alone; legend text and amounts are
  always present.
- Loading, empty, offline/server-unavailable, validation, conflict, parser,
  oversized-file, and unexpected states are distinct. Error text comes from
  the stable API envelope and never renders raw HTML.
- Destructive actions require confirmation; mutations are disabled only while
  that specific action is in flight, and double submission is prevented.

## Approved Fixture Oracle

Live and automated browser checks use only the two committed synthetic fixtures:

- CSV import: 23 retained rows, 22 parsed transactions, one visible
  `missing_amount` failure, and 22 occurrences.
- PDF import: 12 parsed rows and 12 occurrences with no failed row.
- May: spending `50340`, credits `60000`, 12 transactions.
- June: spending `277617`, credits `72999`, 22 transactions.
- The two same-day/same-price Tim Hortons records remain visible and distinct
  while pending. Amazon refund and E-Transfer are visible credits and contribute
  zero spending.
- Exact CSV re-import adds an inspectable run without changing June totals.
- A category correction and duplicate decision update the browser immediately,
  persist after reload, and survive complete support undo plus later re-import.
- Undoing one run changes only that run's support and never removes correction
  or decision history.

## Verification Contract

- Server tests prove loopback-only binding, same-origin static/API routing,
  Host rejection, headers, exact byte forwarding, startup persistence, and no
  raw logging or network-client surface.
- UI tests prove file picker/drop, sequential per-file runs, visible bad rows,
  run detail/undo, month selection, exact formatting, reconciliation, category
  correction, duplicate same/distinct decisions, 409 behavior, reload
  persistence, keyboard operation, and error/empty states.
- A browser end-to-end test starts the real loopback adapter with a temporary
  database, imports both approved fixtures, checks the exact May/June oracle,
  validates exact pie/legend reconciliation, the one-degree minimum visible arc
  for every non-zero category, non-repeating gap-free geometry, and
  the visible bad row, exercises one
  correction, duplicate decision, re-import, and undo, then confirms persistence
  after a page reload.
- Full backend discovery remains green. Final review includes privacy inspection
  and live browser evidence. Product performs the human-QA gate separately on
  the running application before marking the overall goal complete.

## Delivery And Startup Documentation

- Add a concise root `README.md` startup section with the exact local command,
  database location behavior, supported formats, synthetic test command, and
  the explicit note that scanned receipts/OCR are not yet supported.
- The server must support an ephemeral port for automated tests and a stable
  documented default of `8766` for humans. Shutdown must close the listener
  cleanly. Automated tests must hold a port open and prove a second app server
  fails to bind rather than silently sharing it.

## Non-Goals

- OCR or scanned-receipt processing, an OCR engine installation, new bank
  formats, exchange-rate conversion, bank connections, cloud sync, remote/LAN
  access, authentication, multi-user support, telemetry, or deployment.
- Editing retained source facts, deleting import history, or replacing the
  accepted backend rules in browser code.
