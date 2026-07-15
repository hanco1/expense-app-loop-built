# Categorization And Monthly Analysis Core

## Purpose

Turn effective imported transactions into deterministic categories, durable human
decisions, and exact monthly analysis contracts that the browser UI can consume
later. This slice is local Python/SQLite core only; it does not add HTTP routes or
render charts.

## Canonical Categories

The MVP category vocabulary is closed and ordered for stable UI contracts:

1. `Housing`
2. `Groceries`
3. `Dining`
4. `Transportation`
5. `Shopping`
6. `Bills & Utilities`
7. `Health & Fitness`
8. `Entertainment`
9. `Fees`
10. `Income`
11. `Refunds & Credits`
12. `Uncategorized`

Every normalized transaction receives exactly one automatic category. Category
matching is case-insensitive whole-description matching with this `mvp-1` rule
order:

- A positive amount whose description contains `REFUND` -> `Refunds & Credits`.
- Any other positive amount -> `Income`.
- `RENT` or `LANDLORD` -> `Housing`.
- `LOBLAWS` or `SOBEYS` -> `Groceries`.
- `TIM HORTONS` or `COFFEE` -> `Dining`.
- `PRESTO`, `PETRO-CANADA`, or `UBER` -> `Transportation`.
- `AMAZON`, `WALMART`, or `LCBO` -> `Shopping`.
- `BELL` or `HYDRO` -> `Bills & Utilities`.
- `SHOPPERS DRUG MART` or `GOODLIFE` -> `Health & Fitness`.
- `NETFLIX` -> `Entertainment`.
- `MONTHLY PLAN FEE` -> `Fees`.
- Otherwise -> `Uncategorized`.

The output exposes `auto_category`, `effective_category`,
`category_source` (`auto` or `human`), and `category_rule_version`. Automatic
reprocessing may change only the automatic result; it must never overwrite an
effective human correction.

## Human Category Corrections

- A category correction is append-only and linked to stable `identity_id`.
- Only canonical category values are accepted. Invalid values fail before a row
  is appended.
- The latest correction in deterministic `(created_at, correction_id)` order is
  effective; the complete history remains inspectable.
- Undoing all active supports hides the transaction from monthly analysis but
  retains its correction. Exact re-import or later active support restores the
  transaction with the same effective correction.

## Duplicate Decisions

- Suspected pairs remain visible and both identities remain included while the
  decision is `pending`.
- Human decisions are append-only records tied to the stable duplicate link.
  Allowed decisions are `same_transaction` and `distinct`; the latest decision
  is effective and history remains inspectable.
- `same_transaction` names one of the pair as `kept_identity_id`. Monthly
  analysis includes that identity and excludes only the other one with explicit
  reason `human_duplicate_same_transaction`; neither raw nor normalized fact is
  deleted or mutated.
- Effective `same_transaction` links form connected components. At every
  committed state, a component with one or more active identities has exactly
  one included active representative: the human-designated keeper while it is
  active, otherwise one deterministic active fallback. A component with no
  active identities has no included representative.
- Fallback is derived from current component/support state and never appends,
  rewrites, or deletes human decision history. When the designated keeper gains
  active support again, it resumes as the included representative.
- One centralized component projection/validation rule applies whenever state
  can change: source/support append, suspected-link creation or acceptance,
  human same/distinct/keeper redecision, per-run undo including final-support
  loss, and exact or renamed re-import. Operation-specific patches that can
  diverge are not part of the contract.
- Every exported or otherwise public decision-writing entry point must enforce
  that same rule atomically before appending history. In particular, a public
  persistence writer may not bypass the service validator. Zero-keeper,
  multiple-keeper, and alternate-path `distinct` proposals must be rejected
  before any history row is committed; an unvalidated low-level writer must be
  private and unreachable from the supported public API.
- `distinct` includes both identities. A later decision may reverse an earlier
  one because history is append-only and latest-wins.
- Decisions survive undo, exact re-import, and automatic reprocessing.
- The two same-day CAD 4.50 Tim Hortons records start `pending`, remain separate,
  and are included. Marking them `distinct` must preserve both.

## Monthly Spending Semantics

- Month keys are strict `YYYY-MM` calendar values derived from transaction date.
- Spending is the positive magnitude of included negative transactions:
  `spending_minor = -amount_minor`. Positive credits are never spending and do
  not reduce or increase the spending total.
- `spending_total_minor` equals the exact sum of every category's
  `spending_minor`. Every included spending `identity_id` appears in exactly one
  category bucket and in the month transaction list.
- Credits remain visible in the month transaction list and contribute only to
  `credit_total_minor` and credit counts.
- A failed source row has no normalized transaction and cannot enter an
  aggregate, but remains visible through its import run detail.
- Exact re-import support never changes totals or counts. Undo changes analysis
  only when it removes the final active support for an identity.
- All money remains signed integer minor units with explicit currency. This MVP
  rejects mixed-currency aggregation rather than converting implicitly.

## Approved Fixture Oracle

With both approved fixtures imported once and no human duplicate exclusion:

| Month | Transactions | Spending tx | Credits | Spending total | Credit total |
| --- | ---: | ---: | ---: | ---: | ---: |
| `2026-05` | 12 | 11 | 1 | 50340 | 60000 |
| `2026-06` | 22 | 20 | 2 | 277617 | 72999 |

May spending breakdown:

| Category | Spending minor |
| --- | ---: |
| `Bills & Utilities` | 16774 |
| `Groceries` | 16378 |
| `Transportation` | 6437 |
| `Shopping` | 5423 |
| `Health & Fitness` | 1984 |
| `Entertainment` | 1799 |
| `Fees` | 1095 |
| `Dining` | 450 |

June spending breakdown:

| Category | Spending minor |
| --- | ---: |
| `Housing` | 185000 |
| `Shopping` | 30521 |
| `Groceries` | 25727 |
| `Bills & Utilities` | 16774 |
| `Transportation` | 8047 |
| `Health & Fitness` | 6554 |
| `Dining` | 2100 |
| `Entertainment` | 1799 |
| `Fees` | 1095 |

The June Amazon refund (`+12999`) and received E-Transfer (`+60000`) appear as
credits with `Refunds & Credits` and `Income`, respectively, and contribute zero
to spending.

## Service And Contract Surface

Provide stable, typed local contracts for:

- `list_months()` -> available effective months newest first.
- `get_month_summary(month)` -> exact totals, counts, category breakdown, and
  deterministic transaction rows.
- `set_category(identity_id, category)` plus category history/effective state.
- `list_duplicate_candidates()` plus decision history/effective state.
- `set_duplicate_decision(duplicate_link_id, decision, kept_identity_id=None)`.

Month transaction rows expose identity/date/merchant/signed amount/currency,
spending flag, automatic/effective category provenance, effective duplicate
decision and inclusion reason, active support run/source locators, and correction
identifiers. Category buckets expose their contributing identity IDs so totals
can be reconciled without guessing. Ordering is deterministic.

## Privacy And Dependency Boundary

- All operations use the local SQLite store and in-process Python only.
- No HTTP server, network client, telemetry, cloud API, OCR process, subprocess,
  raw-statement log, or system-level dependency.
- No project dependency is expected for this slice; if one becomes necessary,
  follow `dependency_install: auto-pip-only` and ask before any system package.
- The real TD statement remains outside automated tests and repository evidence.

## Non-Goals

- HTTP endpoint implementation, browser UI, pie-chart rendering, CSS, or human QA.
- Machine-learning or third-party categorization, user-authored category names,
  merchant renaming, budgets, exchange rates, recurring-payment detection, or
  financial advice.
- OCR execution or receipt-image ingestion.
