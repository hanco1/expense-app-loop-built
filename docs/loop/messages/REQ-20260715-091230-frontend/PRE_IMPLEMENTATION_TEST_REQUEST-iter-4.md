# PRE_IMPLEMENTATION_TEST_REQUEST

message_type: PRE_IMPLEMENTATION_TEST_REQUEST
request_id: REQ-20260715-091230-frontend
iteration: 4
from_lane: product
to_lane: review
status: BLOCKED
created_at: 2026-07-15T21:08:14Z
implementation_commit: 38479e5

## Purpose

- Freeze one implementation-independent, real-Chromium acceptance test that is red on the current repeated-stripe donut before frontend changes code.
- Review does not dispatch implementation or change product-owned request status.

## Required Observable Contract

- The approved June oracle renders exactly nine non-zero category segments.
- Around the visible ring, each category appears in exactly one contiguous run; the full ring has no repeated category runs, gaps, or overlap-induced replacement.
- Housing is one dominant arc representing 185000 of 277617 minor units and visibly covers more than half of the circumference.
- Every tiny non-zero category remains visibly present, keyboard focusable, selectable, and matched to the text legend.
- Exact `PIE_SCALE = 1000000000n`, `data-units`, BigInt totals, category/transaction reconciliation, credits exclusion, and percentages remain unchanged; only bounded visual coordinates may differ.
- No CSS/SVG computed length may be silently clamped into a repeated pattern. The test should sample or otherwise verify the actually visible browser geometry rather than trusting source attributes alone.

## Freeze Rules

- Commit the review-owned test and a concise boundary document/evidence before frontend implementation.
- Record the frozen hashes and the current red/green path inventory.
- Do not modify the frozen artifacts after the baseline run and do not issue a FIX_REQUEST; product converts the frozen contract into the single authoritative iteration-4 request.

## Policy

- Human approved temporary `max_fix_cycles: 7` for this iteration. Current raw use stays 5 until product performs the sole `BLOCKED -> FIX_REQUESTED` transition; frontend's later claim reaches 7/7.
- Restore `max_fix_cycles: 3` only atomically with ACCEPTED after independent review and explicit renewed human PASS.
