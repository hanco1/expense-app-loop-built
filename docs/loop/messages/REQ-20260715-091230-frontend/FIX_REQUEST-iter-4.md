# FIX_REQUEST

message_type: FIX_REQUEST
request_id: REQ-20260715-091230-frontend
iteration: 4
from_lane: product
to_lane: frontend
status: FIX_REQUESTED
created_at: 2026-07-15T21:15:56Z
implementation_commit: 38479e5
freeze_commit: cc27d2e
evidence_commit: 30dab03

## Frozen Artifacts

- `tests/acceptance/test_local_web_app_pie_geometry_review.py`
  - SHA-256 `D5EEA84080B915C6C1978A20D47C61EE06FD96DFF65E6ED46A822BD33A076912`
- `docs/review/REQ-20260715-091230-frontend-iter-4-pie-geometry-boundary.md`
  - SHA-256 `EA19310EDC2DE2DA13AD447872E569BB845F410B74E9AA21EDE54C23A2F2C4D0`
- Do not modify either frozen artifact.

## Baseline To Close As One Class

- PG-02: 639 of 720 sampled points have multiple segment strokes; maximum allowed is 18 boundary-tolerant points.
- PG-03: the visible ring has 140 cyclic runs; exactly nine are required, one per category.
- PG-04: Groceries and Shopping are absent from the topmost visible ring.
- PG-05: Housing occupies 81 of 720 visible samples; it must exceed 360 and approximate its exact 185000/277617 share.
- PG-01 exact June accounting, nine category amounts, `PIE_SCALE=1000000000`, exact `data-units` sum, transaction/category reconciliation and credit exclusion are green and must remain green.
- PG-06 all nine keyboard focus, Enter selection, and legend-label paths are green and must remain green.

## Required Repair

- Keep exact BigInt allocation, `PIE_SCALE`, `data-units`, displayed amounts, percentages, and reconciliation unchanged.
- Never write 1e9-scale accounting units directly into CSS/SVG length geometry. Convert exact fractions to a bounded visual coordinate system or draw explicit non-repeating arcs.
- The actually painted ring must contain exactly one contiguous visible arc per non-zero category, complete the circumference without gaps or overlap replacement, show Housing as the dominant over-half arc, and preserve every tiny non-zero category.
- Preserve chart focus/selection/legend behavior, credits exclusion, exact-money behavior, approved fixture flows, the 8766 exclusive-bind fix, privacy, accessibility, and all prior blocker closures.

## Verification Manifest

- VERIFY `python -m unittest tests.acceptance.test_local_web_app_pie_geometry_review -v`
- VERIFY `python -m unittest tests.frontend.test_server -v`
- VERIFY `python -m unittest tests.acceptance.test_local_web_app_review -v`
- VERIFY `python -m unittest discover -s tests/frontend -p "test_*.py" -v`
- VERIFY `python -m unittest tests.frontend.test_browser_e2e -v`
- VERIFY `python -m unittest discover -s tests/backend -p "test_*.py" -v`
- VERIFY `python completion_gate.py --loop-dir docs/loop --request-id REQ-20260715-091230-frontend`

## Policy And Human QA

- Human approved temporary `max_fix_cycles: 7`; this FIX_REQUEST reaches raw use 6/7 and frontend's later implementation claim reaches 7/7.
- No dependency or system package is authorized or needed.
- Product retains independent review, renewed live human QA, final ACCEPTED authority, and restores `max_fix_cycles: 3` only atomically with ACCEPTED.
