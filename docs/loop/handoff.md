# Handoff

Continuation state for the next session or lane. Keep this current enough that
the next actor can continue from repo files plus the latest message alone.

## Current State

- The SQLite core foundation is accepted. The human has confirmed the browser operating flow and authorized two wholly synthetic TD-style fixtures for committed end-to-end tests.
- Data-eng fixed the remaining Decimal exceptional-value row loss at commit `e94a09a`; all eight iteration-3 commands and the completion gate are green.
- Independent review is active on the verified review thread. The temporary `max_fix_cycles: 4` override remains until product accepts this request, then product must immediately restore 3.

## Next Action

- [ ] Review commit `e94a09a` against the Decimal blocker, original criteria, scope boundaries, and misuse paths; return `REVIEW_DONE` or a blocker-severity `FIX_REQUEST`.

## Active Request

- request_id: REQ-20260713-073512-data-eng
- owner_lane: review
- iteration: 3

## Blockers

- No implementation blocker. The doctor counts five raw entries into thrash statuses against `max_fix_cycles: 4`; this is a control-plane advisory caused by the human-authorized resume, not permission for another fix round. A review PASS can proceed to product acceptance, which must atomically restore the cap to 3.

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
