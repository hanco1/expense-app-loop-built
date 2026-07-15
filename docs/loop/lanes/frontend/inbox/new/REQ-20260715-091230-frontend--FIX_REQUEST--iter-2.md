# FIX_REQUEST

message_type: FIX_REQUEST
request_id: REQ-20260715-091230-frontend
parent_request_id:
iteration: 2
from_lane: review
to_lane: frontend
status: FIX_REQUESTED
created_at: 2026-07-15T09:45:44Z
implementation_commit: aaa931d
review_commit: 6fe6083
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/product/local-web-app.md
- docs/review/REQ-20260715-091230-frontend-iter-1.md
- tests/acceptance/test_local_web_app_review.py
artifact_scope:
- frontend/server.py
- frontend/static/app.js
- tests/frontend/**
failed_criteria:
- C1/C5: unimplemented HTTP methods such as PATCH, TRACE, CONNECT, and PROPFIND bypass Host-first handling, return default HTML 501, and omit the required security headers for both valid and invalid Host cases.
- C2/C4/C5: import, category, duplicate, and undo POSTs can commit successfully and then be falsely reported failed when the follow-up canonical refresh is unavailable.
severity: blocker
evidence:
- `python -m unittest tests.acceptance.test_local_web_app_review -v` exits 1: six test methods, one green complete error-family guardrail, four red committed-mutation families, and eight red public-method/Host matrix cells (12 reported failures including subtests).
- The unchanged review acceptance SHA-256 is `4EB538618C7455BB857DA7F30F1341F77AE6EA3086B151E87AFA6940B4D3C7D7`.
- Frontend discovery 8/8, real Chromium E2E 1/1, backend 68/68, and SHIP_CHECK_OK remain green; the new test exposes behavior outside those existing happy/conflict paths.
requested_fix:
- Route every public HTTP method through the same Host-first structured response boundary. Invalid Host returns 421 and valid-loopback unsupported methods return 405; every response carries the required security headers and no default HTML error path remains reachable.
- Separate successful mutation acknowledgement from subsequent refresh failure for import, category, duplicate, and undo. A committed write must never be relabelled failed or unsaved; report refresh/stale-state failure separately without a second write or optimistic pre-response state.
- Preserve all existing exact-money, reconciliation, privacy, accessibility, append-only history, conflict, fixture, and browser behavior.
acceptance_criteria:
- The unchanged review-owned acceptance passes all six test methods, including all eight public-method/Host cells, all four committed-mutation refresh paths, and the complete error-family guardrail. VERIFY `python -m unittest tests.acceptance.test_local_web_app_review -v`.
- Original frontend behavior remains green. VERIFY `python -m unittest discover -s tests/frontend -p "test_*.py" -v`.
- The real approved-fixture browser flow remains green. VERIFY `python -m unittest tests.frontend.test_browser_e2e -v`.
- Accepted backend behavior remains green. VERIFY `python -m unittest discover -s tests/backend -p "test_*.py" -v`.
- The completion gate remains green with flat evidence for every declared command. VERIFY `python completion_gate.py --loop-dir docs/loop --request-id REQ-20260715-091230-frontend`.
human_qa:
- Not started. Product requests live human QA only after a later independent code PASS and keeps the request at REVIEWING until explicit confirmation.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-15T09:46:28Z
expected_reply:
- Frontend waits for product's committed FIX_REQUESTED owner transition, then claims iteration 2 and returns IMPLEMENTATION_DONE plus the unchanged review acceptance and all original gates.
- Product commits this root message, requests.md/run-log/heartbeat, and the formal iteration-2 owner transition before frontend implementation starts.
