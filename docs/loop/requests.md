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
| REQ-20260712-200417-data-eng | ACCEPTED | product | 2 | docs/loop/goal.md; docs/loop/tracker.md; docs/loop/constraints.md; docs/product/core-foundation.md | docs/loop/messages/REQ-20260712-200417-data-eng/REVIEW_DONE-iter-2.md | Accepted after implementation evidence, independent review PASS, SHIP_CHECK_OK, and a warning-free pre-acceptance doctor gate; await the remaining intake decisions before the next request. | 2026-07-12T20:24:18Z |
| REQ-20260713-073512-data-eng | ACCEPTED | product | 4 | docs/loop/goal.md; docs/loop/tracker.md; docs/loop/constraints.md; docs/product/import-pipeline.md; docs/review/REQ-20260713-073512-data-eng-iter-4-boundary-matrix.md | docs/loop/messages/REQ-20260713-073512-data-eng/REVIEW_DONE-iter-4.md | Accepted implementation 06ac048 after independent PASS, nine exit-0 gates, backend 31/31, and the unchanged 282-path matrix; max_fix_cycles restored to 3. Prepare the categorization, correction, aggregation, and API-contract slice. | 2026-07-14T06:38:43Z |
| REQ-20260714-064051-data-eng | REQUESTED | data-eng | 1 | docs/loop/goal.md; docs/loop/tracker.md; docs/loop/constraints.md; docs/product/analysis-core.md | docs/loop/messages/REQ-20260714-064051-data-eng/IMPLEMENTATION_REQUEST-iter-1.md | Implement deterministic categories, append-only category and duplicate decisions, exact fixture-backed monthly analysis, and typed local contracts; return nine-command evidence and review handoff. | 2026-07-14T06:40:51Z |
