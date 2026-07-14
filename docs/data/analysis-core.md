# Analysis Core Decisions

## Persistence

- Canonical category corrections use the existing append-only
  `manual_corrections` table with `correction_type = 'category'`. A SQLite
  trigger rejects values outside the closed canonical vocabulary, and the
  effective value is the last row in `(created_at, correction_id)` order.
- Duplicate decisions use a dedicated append-only `duplicate_decisions` table.
  `same_transaction` requires a kept identity belonging to the linked pair;
  `distinct` has no kept identity. Updates and deletes are rejected by triggers.
- Before a `same_transaction` decision is appended, `AnalysisService` evaluates
  the proposed latest-wins decision graph for the affected connected component.
  A kept-choice cycle, or any proposal that would exclude every currently active
  representative, is rejected with `ValueError`; the rejected proposal appends
  no history row. Existing isolated-pair and later `distinct` reversal semantics
  remain unchanged.
- Automatic categories are not written over normalized transaction facts. They
  are deterministically recomputed under rule version `mvp-1`, after which the
  latest human correction, when present, becomes effective.

## Local Service Contract

`AnalysisService` exposes typed dataclass results from `contracts.analysis`:

- `list_months()` returns active, included months newest first.
- `get_month_summary(month)` returns exact integer totals, ordered non-zero
  spending buckets, contributing identity IDs, and deterministic audit rows.
- `set_category()` and `get_category_state()` expose append-only correction
  history and effective provenance.
- `list_duplicate_candidates()`, `get_duplicate_candidate()`, and
  `set_duplicate_decision()` expose append-only decision history and current
  inclusion state.

Month counts and totals include only transactions with active import support
that are not excluded by an effective `same_transaction` decision. An excluded
duplicate with active support remains in the month audit rows with
`included = false` and `human_duplicate_same_transaction`, so the exclusion is
traceable without retaining it in totals. Positive amounts remain visible as
credits but never contribute to spending or category spending buckets.

Every transaction row carries active run/source support, category rule and
correction identifiers, duplicate link/decision identifiers, and an explicit
inclusion reason. Category buckets carry sorted contributing identity IDs, so
frontend totals and pie-chart data can reconcile without reproducing backend
rules.
