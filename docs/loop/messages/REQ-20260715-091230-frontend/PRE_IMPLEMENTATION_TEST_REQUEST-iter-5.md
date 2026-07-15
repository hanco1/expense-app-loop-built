# PRE_IMPLEMENTATION_TEST_REQUEST

message_type: PRE_IMPLEMENTATION_TEST_REQUEST
request_id: REQ-20260715-091230-frontend
parent_request_id:
iteration: 5
from_lane: product
to_lane: review
status: BLOCKED
created_at: 2026-07-15T22:48:17Z
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/local-web-app.md
- docs/review/REQ-20260715-091230-frontend-iter-4.md
- tests/acceptance/test_local_web_app_tiny_slice_review.py
design_system:
- disabled by explicit human constraint
artifact_scope:
- tests/acceptance/**
- docs/review/**
- docs/loop/lanes/review/**
non_goals:
- Do not modify frontend or backend implementation, prior frozen artifacts, exact accounting rules, dependencies, runtime ports, privacy behavior, or root lifecycle state.
human_decision:
- Temporarily raise `max_fix_cycles` from 7 to 9, enter iteration 5, replace coordinate-precision patching with a minimum-visible-arc strategy, and restore the cap to 3 only with ACCEPTED.
superseding_visual_contract:
- Numerical truth remains exact: minor-unit amounts, displayed percentages, category reconciliation, `data-units`, and `PIE_SCALE=1000000000` are unchanged and never derived from visual angles.
- Every non-zero spending category has one contiguous visible arc of at least 1 degree in real Chromium, regardless of how small its exact share is or how coordinates are serialized.
- Categories below 1 degree are visually lifted to 1 degree. The remaining circumference is distributed among non-floored categories in proportion to their exact amounts, so the chart covers one full circle without gaps or overlaps and preserves the relative ordering/proportions of larger categories.
- The numerical legend/table reports exact shares rather than the visually adjusted floor. Zero categories remain absent; credits remain excluded from spending and pie slices.
acceptance_criteria:
- Freeze one concise real-Chromium iteration-5 acceptance that fails on implementation `4b88b11` and proves actual visible path length/hit geometry, not only DOM attributes. VERIFY `python -m unittest tests.acceptance.test_local_web_app_minimum_arc_review -v`.
- Cover the supported one-unit/near-full case plus multiple simultaneous sub-floor categories up to the canonical spending-category count; every non-zero arc must measure at least the one-degree threshold, remain one contiguous run, and the circle must have no silent gaps or overlap replacement. VERIFY `python -m unittest tests.acceptance.test_local_web_app_minimum_arc_review -v`.
- In the same test, prove exact amounts, displayed percentages, category reconciliation, `data-units` values and 1e9 sum remain unchanged, with zero categories absent and credits excluded. VERIFY `python -m unittest tests.acceptance.test_local_web_app_minimum_arc_review -v`.
- Keep the approved-June geometry, interaction, server, prior acceptance, frontend, browser E2E, backend, privacy, and completion-gate contracts available as unchanged later regression gates; do not reinterpret visual flooring as permission to change numerical truth.
expected_reply:
- Commit one review-owned acceptance module plus a concise iteration-5 boundary document/evidence; report frozen hashes and the red/green inventory against `4b88b11`.
- Do not dispatch frontend implementation. Product retains the sole `BLOCKED -> FIX_REQUESTED` transition after the freeze.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: pending
- sent_at:
