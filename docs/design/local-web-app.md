# Local Web App Design

## Runtime boundary

`frontend.server` binds only IPv4 `127.0.0.1`, serves a fixed static-asset allowlist, and forwards `/api/**` request bytes to the accepted `LocalWebApi`. Host validation runs before static or API dispatch. Every response carries a no-store policy, a self-only content security policy, clickjacking protection, MIME sniffing protection, and a no-referrer policy. The adapter emits no request logs.

The browser fetches `/api/session` once during boot and holds the CSRF token only in JavaScript memory. Every mutation sends it in `X-Local-Expense-CSRF`; no token enters a URL, DOM node, or log. All data stays same-origin and no network client, CORS allowance, remote asset, service worker, telemetry, or analytics surface is present.

## Information architecture

The responsive shell has three keyboard-operable views:

- Overview: exact spending, credits, included count, reconciled category table, accessible SVG pie/legend, and traceable included transactions with category correction.
- Imports: file picker/drop zone, sequential per-file results, persistent run history, structured retained-row detail, and confirmed run undo.
- Duplicates: both transaction identities, active support context, inclusion state, append-only history, explicit distinct or same/kept decisions, and local conflict messages.

The newest effective month is selected after every boot or when the current month disappears after support undo.

## Exact money and reconciliation

Browser code accepts money only as signed base-10 strings and parses it with `BigInt`. Canadian-dollar formatting is manual string formatting, not `Number` or `Intl` conversion. Percentages use integer basis-point rounding. The SVG chart uses an exact one-billion-unit integer path scale; every non-zero category gets at least one selectable unit and the units reconcile exactly to the scale.

Before rendering category, chart, or transaction detail, the UI checks that:

- category sums equal `spending_total_minor`;
- included spending rows equal the category sums and spending total;
- included positive credit rows equal `credit_total_minor`;
- included row count equals `transaction_count`; and
- every category equals its contributing included rows.

If reconciliation fails, the app blocks the detailed rendering and shows an error instead of presenting inconsistent financial results.

## Failure and accessibility behavior

Stable API error codes/messages are inserted with `textContent`; retained raw input is never rendered. Loading, empty, offline, validation, parser, oversized, conflict, zero-spending, and unexpected states remain distinct. Destructive undo uses a filename-bearing confirmation. Each mutation button owns its own in-flight guard, preventing double submission without disabling unrelated actions.

All primary actions have semantic buttons/labels, visible focus, live status, alert regions, table captions, and text-based chart alternatives. At narrow widths, layouts collapse without page-level horizontal scrolling; only wide data tables may scroll within their labelled panel.
