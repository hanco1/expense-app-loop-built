# FIX_REQUEST

message_type: FIX_REQUEST
request_id: REQ-20260715-091230-frontend
parent_request_id:
iteration: 5
from_lane: product
to_lane: frontend
status: FIX_REQUESTED
created_at: 2026-07-15T22:56:30Z
implementation_commit: 4b88b11
freeze_commit: 4b3e0d8
review_delivery_commit: 8c08c7e
design_system:
- disabled by explicit human constraint
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/local-web-app.md
- docs/review/REQ-20260715-091230-frontend-iter-5-minimum-arc-boundary.md
- tests/acceptance/test_local_web_app_minimum_arc_review.py
artifact_scope:
- frontend/**
- tests/frontend/**
- docs/design/**
- docs/loop/lanes/frontend/**

## Frozen Artifacts

- `tests/acceptance/test_local_web_app_minimum_arc_review.py`
  - SHA-256 `9FABFD79773E1419363E73508D2FB2125B5E6D1F087661C18AE559762984C88D`
- `docs/review/REQ-20260715-091230-frontend-iter-5-minimum-arc-boundary.md`
  - SHA-256 `34B7562E606A2B9C691D4629FCB6CB442CD83A28689472189289C8C48B326AED`
- Do not modify either frozen artifact or any earlier frozen acceptance artifact.

## Baseline To Close As One Class

- `MA-01-one-unit-near-full`: exact `data-units` are `1/999999999`, but both categories currently render with zero path length and zero visible hits. Required visual arcs are `1°/359°`.
- `MA-02-canonical-count-simultaneous-floors`: all 12 canonical categories are non-zero, with 11 one-unit categories. All 11 tiny categories are currently invisible and the large category overpaints the intended remainder. Required visual arcs are eleven `1°` floors and one `349°` remainder.
- Both baselines already preserve exact amounts, displayed percentages, reconciliation, exact `data-units` and their `PIE_SCALE=1000000000` sum, zero-category absence, and credit exclusion. These green facts must remain unchanged.

## Required Class-Wide Repair

- Implement a separate visual allocation layer with a strict one-degree minimum visible arc for every exact non-zero spending category. Do not tune decimal coordinate precision or add case-specific branches.
- Use water-filling semantics: reserve the one-degree floor for categories whose exact share is below that floor, then distribute the remaining circumference among non-floored categories in proportion to their exact amounts. The visual arcs must cover one full circle without silent gaps or overlap replacement.
- Numerical truth stays independent and exact: minor-unit amounts, displayed percentages, category reconciliation, `data-units`, and `PIE_SCALE=1000000000` must not be derived from visually adjusted angles.
- Every non-zero category must paint one contiguous real-Chromium arc of at least one degree, including the supported one-unit allocation and 11 simultaneous sub-floor categories. Zero categories remain absent and credits remain outside spending and the pie.
- Preserve focus, Enter selection, legend mapping, accessibility, approved-fixture behavior, the 8766 exclusive-bind boundary, privacy, append-only history, and every prior blocker closure.

## Verification Manifest

- VERIFY `python -m unittest tests.acceptance.test_local_web_app_minimum_arc_review -v`
- VERIFY `python -m unittest tests.acceptance.test_local_web_app_pie_geometry_review -v`
- VERIFY `python -m unittest tests.acceptance.test_local_web_app_tiny_slice_review -v`
- VERIFY `python -m unittest tests.frontend.test_server -v`
- VERIFY `python -m unittest tests.acceptance.test_local_web_app_review -v`
- VERIFY `python -m unittest discover -s tests/frontend -p "test_*.py" -v`
- VERIFY `python -m unittest tests.frontend.test_browser_e2e -v`
- VERIFY `python -m unittest discover -s tests/backend -p "test_*.py" -v`
- VERIFY `python completion_gate.py --loop-dir docs/loop --request-id REQ-20260715-091230-frontend`

## Policy And Human QA

- Human approved temporary `max_fix_cycles: 9`; this FIX_REQUEST reaches raw use 8/9 and frontend's later implementation claim reaches 9/9.
- No dependency or system package is authorized or needed.
- Product retains independent review, renewed live human QA, final ACCEPTED authority, and restores `max_fix_cycles: 3` only atomically with ACCEPTED.

delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-15T22:57:52Z
