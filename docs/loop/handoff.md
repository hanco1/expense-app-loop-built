# Handoff

Continuation state for the next session or lane. Keep this current enough that
the next actor can continue from repo files plus the latest message alone.

## Current State

- The SQLite core foundation is accepted. The human has confirmed the browser operating flow and authorized two wholly synthetic TD-style fixtures for committed end-to-end tests.
- Data-eng fixed the partial-active-state blocker at commit `6bca89e`; all eight declared iteration-2 commands and the completion gate were green.
- The human approved a temporary `max_fix_cycles: 4` override. The same request is resumed as iteration 3 to fix the remaining INV-1 Decimal-exception source-row loss; the cap must return to 3 immediately after ACCEPTED.

## Next Action

- [ ] Data-eng maps every Decimal construction/arithmetic/comparison/conversion exception to retained row-level `invalid_amount`, adds NaN and overflow-exponent regressions, and returns iteration-3 evidence for review.

## Active Request

- request_id: REQ-20260713-073512-data-eng
- owner_lane: data-eng
- iteration: 3

## Blockers

- None. The human authorized the final fix round.

## Pending Inbox Deliveries

- None.

## Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` done and verified
- `[!]` blocked

## Done When

- [ ] Both approved fixtures import with field-level correctness, bad rows remain visible, exact re-imports do not double-count, legitimate lookalikes remain separate, and each run is inspectable and independently undoable without losing manual corrections.

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
