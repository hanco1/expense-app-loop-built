# Constraints

Boundaries every lane must respect. Read before implementing or reviewing.

## Hard Constraints

- Do not commit secrets, credentials, or tokens.
- Do not run destructive, billing, or production-deployment actions without explicit human approval.
- Stay inside each lane's declared write_scope in `agent-lanes.md`.
- Keep the application and financial data local by default; do not upload statements or transaction data to external services.
- Do not enable optional skills (including Superpowers, visualization companions, or design add-ons) unless the human explicitly requests them.

## Technical Constraints

- Project/package dependencies may be installed automatically.
- Ask the human before installing any system-level dependency, including an OCR engine.

## Process Constraints

- Only switch sessions at a checkpoint boundary.
- Update `tracker.md`, `handoff.md`, `requests.md`, and lane `current.md` before any handoff.
- Reuse the same `request_id` across fix cycles; increment `iteration`.

## Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` done and verified
- `[!]` blocked

## Auto-Chain Permission

auto_chain_next_session: false
