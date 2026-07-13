# Handoff

Continuation state for the next session or lane. Keep this current enough that
the next actor can continue from repo files plus the latest message alone.

## Current State

- The SQLite core foundation is accepted. The human has confirmed the browser operating flow and authorized two wholly synthetic TD-style fixtures for committed end-to-end tests.
- Data-eng implemented `REQ-20260713-073512-data-eng` at commit `9fccab6`; all seven declared commands and the completion gate are green.
- Independent review found a blocker: a rejected supported-shape CSV can leave earlier rows effective in a partial active run whose `run_id` was not returned. Iteration 2 is routed to data-eng.

## Next Action

- [ ] Data-eng makes failed import handling explicit/atomic, adds red-capable regression coverage, and returns iteration-2 implementation evidence for review.

## Active Request

- request_id: REQ-20260713-073512-data-eng
- owner_lane: data-eng
- iteration: 2

## Blockers

- Review blocker: a later storage failure can leave an active partial run and effective data even though `import_bytes` raised.

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
