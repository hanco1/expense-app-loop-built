# Requests

Use the table below as the durable queue for cross-agent work. Recover from
here instead of from chat memory.

## Schema

Required columns, in order: request_id, status, owner_lane, iteration,
source_docs, last_message, next_action, updated_at.

Rules:

- request_id is stable across fix cycles: REQ-YYYYMMDD-HHMMSS-<lane>.
- status lifecycle: PLANNED -> REQUESTED -> IMPLEMENTING -> IMPLEMENTATION_DONE -> REVIEWING -> FIX_REQUESTED -> ACCEPTED | BLOCKED.
- Terminal states are ACCEPTED and BLOCKED.
- Only the current owner_lane moves a request forward.
- Increment iteration when a request returns to implementation after review.
- next_action must let any lane resume after compaction or a new session.
- updated_at is ISO-8601 UTC, e.g. 2026-06-23T11:00:00Z.

This file must contain exactly one Markdown table (the queue below). Keep the
schema described as prose above so recovery tooling reads only real rows.

## Queue

| request_id | status | owner_lane | iteration | source_docs | last_message | next_action | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- |
| REQ-20260712-200417-data-eng | REVIEWING | review | 1 | docs/loop/goal.md; docs/loop/tracker.md; docs/loop/constraints.md; docs/product/core-foundation.md | docs/loop/messages/REQ-20260712-200417-data-eng/REVIEW_REQUEST-iter-1.md | Independently rerun the seven declared commands, review criteria/invariants/scope creep/looks-done-but-wrong outcomes and ease of misuse, then return REVIEW_DONE or a blocker FIX_REQUEST. | 2026-07-12T20:13:23Z |
