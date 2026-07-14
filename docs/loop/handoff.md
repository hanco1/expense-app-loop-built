# Handoff

Continuation state for the next session or lane. Keep this current enough that
the next actor can continue from repo files plus the latest message alone.

## Current State

- The SQLite core foundation is accepted. The human has confirmed the browser operating flow and authorized two wholly synthetic TD-style fixtures for committed end-to-end tests.
- Data-eng fixed the named Decimal exceptional-value row loss at commit `e94a09a`; all eight declared iteration-3 commands and the completion gate are green.
- Independent review found that `1e-999999999` silently becomes an active zero-cent transaction. The human authorized iteration 4 with a temporary cap of 7 and required one whitelist-based class-wide correction.
- Data-eng implemented the frozen class-wide whitelist at `06ac048`; product and independent review reproduced backend 31/31 and the full unchanged 282-path acceptance matrix with all nine recorded gates green. Review returned PASS with no scope, privacy, traceability, or misuse finding.
- Product accepted the ingestion slice and restored the standing `max_fix_cycles: 3` in the same checkpoint.
- Product specified the next core slice in `docs/product/analysis-core.md`: deterministic categories, append-only category/duplicate decisions, exact monthly fixture oracles, and typed local contracts.
- Data-eng implemented the analysis core at `8aa5b6f`; all nine recorded commands are exit 0, backend discovery is 45/45, and product independently reproduced the exact May/June, correction, and duplicate checks.
- Independent review found a C3 blocker in iteration 1: three pairwise kept choices could form a cycle and exclude every active identity.
- Data-eng fixed the blocker at `6b9378f` by validating the proposed latest-wins connected component before appending a `same_transaction` decision. The cycle-closing proposal now raises `ValueError` with no history row, accepted decisions survive undo/re-import, and one representative remains included.
- The unchanged review acceptance, all original focused gates, backend discovery 46/46, and the completion gate are green with ten flat iteration-2 evidence records.
- Independent iteration-2 review added the missing selective-support transition: after a valid same-transaction decision, undoing only the designated keeper's run leaves the non-kept identity active in storage but excluded from analysis. The expanded acceptance is red at `tests/acceptance/test_analysis_core_review.py:119`.
- The live raw fix-cycle count is 3 at `max_fix_cycles: 3`; review returned the request to product as BLOCKED instead of dispatching iteration 3. The recommended human decision is a temporary cap of 5 for one bounded final round, restored to 3 after acceptance.

## Next Action

- [!] Human decides whether to authorize a temporary `max_fix_cycles: 5` for one bounded iteration-3 repair of selective keeper-support undo.

## Active Request

- request_id: REQ-20260714-064051-data-eng
- owner_lane: product
- iteration: 2

## Blockers

- C3 blocker: a normal selective run undo can leave an active duplicate component with zero included representatives; see `docs/review/REQ-20260714-064051-data-eng-iter-2.md`.
- Anti-thrash gate: another full implementation round requires explicit human authorization because raw fix-cycle count is 3 at the standing cap of 3.

## Pending Inbox Deliveries

- None.

## Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` done and verified
- `[!]` blocked

## Done When

- [x] Both approved fixtures import with field-level correctness, bad rows remain visible, exact re-imports do not double-count, legitimate lookalikes remain separate, and each run is inspectable and independently undoable without losing manual corrections.
- [ ] May and June fixture summaries match the exact oracle, category buckets reconcile to spending, credits remain outside spending, and human category/duplicate decisions persist through undo and re-import.

## Memory Protocol

The decision memory (`memory/decisions.jsonl`) is an append-only cache, never a
source of truth. Follow this protocol so it survives compaction and never lies:

1. Before deciding, grep `memory/decisions.jsonl` for this request_id and
   follow the `supersedes` chain to the newest live decision.
2. Before trusting any recorded `gate_status`, re-run
   `completion_gate.py --request-id <id>` and `multi_agent_loop_doctor.py`.
   The recorded token is only a hint; the live gate is the authority.
3. If the doctor reports a `stale_decision`, discard that cached decision and
   re-read the live source docs before acting on it.
4. At checkpoint close, append EXACTLY one line via `record_decision.py`. Never
   edit or delete an old line. To change a prior decision, append a new line
   whose `supersedes` names the old `decision_id`.

## Auto-Chain Permission

auto_chain_next_session: false
