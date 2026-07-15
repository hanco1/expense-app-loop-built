# BLOCKED

message_type: BLOCKED
request_id: REQ-20260715-091230-frontend
iteration: 3
from_lane: product
to_lane: human
status: BLOCKED
created_at: 2026-07-15T21:05:45Z
implementation_commit: 38479e5
review_commit: c56c4e1

## Human QA Finding

- The default-port/exclusive-bind issue is resolved, but the donut is not visually acceptable: it shows repeated multicolor stripes rather than one contiguous arc per category.
- June has nine correct category buckets. Housing is 185000 of 277617 minor units, approximately 66.64%, so it should be one dominant arc.

## Reproduced Root Cause

- The UI retains exact category allocation at `PIE_SCALE = 1000000000n` and writes those integers directly into SVG `pathLength`, `stroke-dasharray`, and `stroke-dashoffset`.
- For Housing the intended dash pair is `666385709 333614291`, but Chromium reports computed dash lengths of approximately `3.35544e+07px, 3.35544e+07px`.
- Chromium clamps the oversized SVG/CSS lengths near `2^25` before path normalization. The resulting dash period is far shorter than the declared path, so every category pattern repeats around the circle.
- Exact amounts, category totals, legend values, and BigInt reconciliation are correct; the defect is isolated to visual geometry.

## Requested Fix If Resumed

- Keep the exact BigInt allocation and `data-units` reconciliation unchanged.
- Convert exact fractions to a bounded SVG visual coordinate system, or render explicit non-repeating arcs; no 1e9-scale length may reach CSS/SVG geometry.
- Add red-capable coverage proving nine contiguous, non-repeating arcs for the approved June oracle, including a dominant Housing arc, tiny non-zero slices, selection/focus behavior, and reconciliation.
- Rerun independent review and renewed live human QA.

## Human Decision Needed

- Raw fix-cycle use is 5 at `max_fix_cycles: 5`.
- Recommended: temporarily raise `max_fix_cycles` to 7, authorize iteration 4 for this bounded rendering-class repair, and restore it to 3 only atomically with ACCEPTED.
