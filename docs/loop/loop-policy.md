# Loop Policy

## Handoff Gates

- Start loop engineering only when the goal is clear, work is checkpointable, verification exists, and state must survive across sessions.
- Hand off only at checkpoint boundaries after verification and state updates.
- The next lane must be able to act from repo files plus the message alone.

## Request Policy

<!-- max_fix_cycles bounds token burn per request; humans may edit it here or via the loop dashboard's POST /api/policy control. Keep the "max_fix_cycles: <int>" line format. -->
max_fix_cycles: 7
auto_dispatch: true
auto_chain_next_session: false

<!-- dependency_install controls the missing-dependency exit ramp (F16): ask = always ask the human before installing anything (default); auto-pip-only = a lane may auto-install a pip-installable Python package but must still ask before installing a system binary; never = never install, always stay BLOCKED for a human to resolve. Keep the "dependency_install: <value>" line format. -->
dependency_install: auto-pip-only

## Anti-Thrash Policy

- Cap consecutive FIX_REQUESTED <-> IMPLEMENTING cycles for one request at `max_fix_cycles`.
- When the cap is reached, stop the fix loop and escalate the request to product as BLOCKED.
- Do not reopen an ACCEPTED request without a new request_id.
- Completed temporary override: `REQ-20260713-073512-data-eng` iteration 4 used `max_fix_cycles: 7`, reached `ACCEPTED`, and restored the standing cap to `3` in the same product checkpoint.
- Iteration 4 closed the amount-validity class with one positive whitelist and the frozen 282-path review matrix; do not reopen the accepted request without a new request_id.
- Superseded override: `REQ-20260714-064051-data-eng` iteration 3 used `max_fix_cycles: 5` for the frozen component-state/operation matrix, but review found an exported write-boundary bypass before acceptance.
- Active human-approved override: `REQ-20260714-064051-data-eng` iteration 4 may use `max_fix_cycles: 7` only to close every exposed duplicate-decision write boundary against the frozen writer/proposal matrix.
- Restore the standing `max_fix_cycles: 3` in the same product checkpoint that moves `REQ-20260714-064051-data-eng` to `ACCEPTED`.

## Completion Token

- Emit `SHIP_CHECK_OK` only when every checkpoint verify command exited 0 and evidence is recorded under `evidence/`.
- If any verify command cannot run or exits non-zero, the checkpoint is BLOCKED, not accepted-with-caveat.

## Human Gates

Stop before credentials, production deployment, destructive actions, billing changes, private external data, or unclear acceptance criteria.

## Thread Policy

- Returned thread IDs are provisional until read_thread or list_threads verifies them.
- Create at most one replacement continuation for a stale or unreadable thread.
- Do not create a new thread when a verified active thread already owns the same request.
