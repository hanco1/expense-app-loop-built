# Handoff

Continuation state for the next session or lane. Keep this current enough that
the next actor can continue from repo files plus the latest message alone.

## Current State

- The SQLite core foundation is accepted. The human has confirmed the browser operating flow and authorized two wholly synthetic TD-style fixtures for committed end-to-end tests.
- Data-eng fixed the named Decimal exceptional-value row loss at commit `e94a09a`; all eight declared iteration-3 commands and the completion gate are green.
- Independent review found that `1e-999999999` silently becomes an active zero-cent transaction. The human authorized iteration 4 with a temporary cap of 7 and required one whitelist-based class-wide correction.
- Data-eng implemented the frozen class-wide whitelist at `06ac048`; product and independent review reproduced backend 31/31 and the full unchanged 282-path acceptance matrix with all nine recorded gates green. Review returned PASS with no scope, privacy, traceability, or misuse finding.

## Next Action

- [~] Product accepts `06ac048`, restores `max_fix_cycles` from 7 to 3 atomically with ACCEPTED, and reruns the completion gate and doctor.

## Active Request

- request_id: REQ-20260713-073512-data-eng
- owner_lane: product
- iteration: 4

## Blockers

- No blocker. Independent review PASS is recorded; final acceptance is product-owned.
- `max_fix_cycles: 7` is temporary for iteration 4. Restore it to 3 atomically after ACCEPTED.

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
