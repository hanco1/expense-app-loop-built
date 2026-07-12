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
| REQ-20260712-200417-data-eng | REVIEWING | product | 2 | docs/loop/goal.md; docs/loop/tracker.md; docs/loop/constraints.md; docs/product/core-foundation.md | docs/loop/messages/REQ-20260712-200417-data-eng/REVIEW_DONE-iter-2.md | Review passed at commit 0ea7be5 with all eight commands and completion gate green; product performs the final acceptance decision and chooses the next bounded request. | 2026-07-12T20:22:56Z |
