# Analysis Core Decisions

## Persistence

- Canonical category corrections use the existing append-only
  `manual_corrections` table with `correction_type = 'category'`. A SQLite
  trigger rejects values outside the closed canonical vocabulary, and the
  effective value is the last row in `(created_at, correction_id)` order.
- Duplicate decisions use a dedicated append-only `duplicate_decisions` table.
  `same_transaction` requires a kept identity belonging to the linked pair;
  `distinct` has no kept identity. Updates and deletes are rejected by triggers.
- `AnalysisService` uses one component projection for decision validation and
  every read. Only effective latest-wins `same_transaction` edges connect a
  component; pending and `distinct` links do not. The identities that are never
  named as a non-keeper by those edges define the structural keeper, and every
  committed component must have exactly one. A proposal with zero or multiple
  structural keepers is rejected before history append. A `distinct` proposal
  is also rejected when its endpoints remain connected through another
  `same_transaction` path.
- An active component includes exactly one representative. Its structural keeper
  is used while active; otherwise the lexicographically smallest active stable
  identity is the deterministic fallback. A component with no active identity
  includes none. Undo, exact or renamed re-import, and support restoration all
  reuse this projection without appending or rewriting human decision history;
  restored keeper support automatically resumes the human preference.
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
