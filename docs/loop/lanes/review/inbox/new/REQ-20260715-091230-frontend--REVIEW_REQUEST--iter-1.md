# REVIEW_REQUEST

message_type: REVIEW_REQUEST
request_id: REQ-20260715-091230-frontend
parent_request_id:
iteration: 1
from_lane: frontend
to_lane: review
status: REVIEWING
created_at: 2026-07-15T09:35:17Z
implementation_commit: aaa931d
lane_handoff_commit: 3225194
product_cross_lane_commit: f70d6a7
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/import-pipeline.md
- docs/product/analysis-core.md
- docs/product/local-web-api.md
- docs/product/local-web-app.md
artifact_scope:
- frontend/**
- tests/frontend/**
- docs/design/**
- implementation commit aaa931d
acceptance_criteria:
- C1: Prove exact 127.0.0.1-only binding, same-origin static/API routing, pre-dispatch Host rejection, complete security headers, per-mutation CSRF, and no statement/token/transaction logging or remote surface.
- C2: Prove picker/drop, sequential distinct runs, exact CSV/PDF fixture counts, visible `missing_amount`, persistent run history/detail, confirmed undo refresh, and non-destructive stale conflict.
- C3: Prove newest June default, exact May/June oracles, BigInt-only formatting, category/included-row/spending/pie/legend reconciliation, credits outside slices, and selectable tiny slices.
- C4: Prove category correction and Tim Hortons pending/distinct/same/keeper flows, append-only history, 409 no optimism, reload persistence, complete support undo, and re-import restoration.
- C5: Prove semantic keyboard/focus/live-region/legend behavior, narrow layout, safe text rendering, complete empty/loading/offline/error states, and per-action double-submit prevention.
- C6: Independently run the real browser through both fixtures and inspect structured evidence, oracle, bad row, decisions, re-import, undo, reload, and persistence.
- C7: Frontend 8/8, browser E2E 1/1, backend 68/68, fixture hashes, startup/shutdown, dependency/privacy boundary, and completion gate remain green.
implementation_notes:
- Runtime is stdlib ThreadingHTTPServer plus accepted LocalWebApi; static/browser code is dependency-free HTML/CSS/JavaScript.
- Money and percentages use BigInt; pie geometry uses a reconciled one-billion-unit integer scale with minimum non-zero slices.
- Browser mutations never update optimistically; successful API responses trigger canonical refresh.
verification:
- `python -m unittest discover -s tests/frontend -p "test_*.py" -v`: exit 0, 8/8.
- `python -m unittest tests.frontend.test_browser_e2e -v`: exit 0, 1/1 on existing Chromium 145.0.7632.6.
- `python -m unittest discover -s tests/backend -p "test_*.py" -v`: exit 0, 68/68.
- completion gate: exit 0, `SHIP_CHECK_OK REQ-20260715-091230-frontend`.
evidence:
- docs/loop/evidence/REQ-20260715-091230-frontend-iter-1-python-m-unittest-discover-s-tests-frontend-p-test-py-v.json
- docs/loop/evidence/REQ-20260715-091230-frontend-iter-1-python-m-unittest-tests-frontend-test-browser-e2e-v.json
- docs/loop/evidence/REQ-20260715-091230-frontend-iter-1-python-m-unittest-discover-s-tests-backend-p-test-py-v.json
- docs/loop/evidence/REQ-20260715-091230-frontend-iter-1-completion-gate.json
dependency_statement:
- No dependency/runtime was added or installed; existing Playwright and Chromium were used. No optional skill, OCR, system dependency, remote asset, CORS, telemetry, analytics, service worker, deployment, authentication, or backend business-rule change.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-15T09:35:17Z
expected_reply:
- REVIEW_DONE PASS or blocker-severity FIX_REQUEST with per-criterion results, scope/misuse/privacy findings, exact commands, browser evidence, and explicit live human-QA readiness/hold.
