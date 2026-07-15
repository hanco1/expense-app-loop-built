# FIX_REQUEST

message_type: FIX_REQUEST
request_id: REQ-20260715-091230-frontend
parent_request_id:
iteration: 3
from_lane: product
to_lane: frontend
status: FIX_REQUESTED
created_at: 2026-07-15T19:56:35Z
implementation_commit: 8131762
review_commit: 9e8e183
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/local-web-app.md
- docs/review/REQ-20260715-091230-frontend-iter-2.md
- tests/acceptance/test_local_web_app_review.py
design_system:
- disabled by explicit human constraint; do not enable Superpowers, visualization companions, or optional design skills.
user_facing: true
artifact_scope:
- frontend/server.py
- frontend/README.md
- tests/frontend/**
- docs/design/**
- docs/loop/lanes/frontend/**
failed_criteria:
- C1/C6/C7 and the no-silent-outcome requirement: the stable app default `8765` collides with the loop dashboard. On Windows, `LocalExpenseHTTPServer.allow_reuse_address = True` allowed the dashboard (PID 73908) and app (PID 164384) to listen on the same endpoint while requests reached only the dashboard; `/api/*` returned 404 from the wrong service.
- Startup printed an apparently successful expense-app URL even though that URL did not reach the expense app. This is a wrong-but-accepted runtime state and invalidates the prior human-QA link.
severity: blocker
live_evidence:
- Before cleanup, `http://127.0.0.1:8765/` rendered the loop dashboard and `http://127.0.0.1:8765/api/session` returned 404.
- Product stopped only expense-app PID 164384. Dashboard PID 73908 remains the sole 8765 listener, and its `/api/session` still returns 404 as expected for the dashboard.
- Port 8766 was unoccupied at dispatch time.
requested_fix:
- Change the stable human default to `8766`; keep exact loopback host `127.0.0.1` and `--port 0` support.
- Make the listener exclusive on every supported platform. On Windows, use the platform's exclusive-address option before bind and do not enable address reuse. If any requested nonzero port is occupied, construction/CLI startup must fail immediately with a clear bind error and non-zero exit; do not print a success URL or enter `serve_forever`.
- Derive the startup URL from `server.server_address` only after a successful bind. The printed URL must be the exact reachable expense-app origin, including the allocated port for `--port 0`.
- Add class-wide red-capable tests: hold a loopback port open and prove every public construction/startup path rejects a second bind atomically; assert no success URL is emitted on failure; assert the printed successful URL reaches the expense app page and `/api/session`; assert the default is not 8765 and is documented as 8766.
- Update frontend-owned startup documentation and return the exact root README text product must apply after implementation. Do not edit product-owned `README.md`.
invariants:
- INV-8 local-only boundary remains applicable: VERIFY `python -m unittest tests.frontend.test_server -v` fails if binding escapes exact loopback, Host/security handling regresses, or the listener can silently share an occupied endpoint.
- Human-observed no-silent runtime outcome: VERIFY `python -m unittest tests.frontend.test_server -v` fails if startup reports success without a reachable expense-app root and `/api/session`, or if an occupied requested port does not exit non-zero.
acceptance_criteria:
- Default startup uses `127.0.0.1:8766`, and both the parser help and frontend-owned docs agree. VERIFY `python -m unittest tests.frontend.test_server -v`.
- An already-occupied loopback port is rejected by server construction and CLI startup before any success URL/serving loop; no silent co-bind remains. VERIFY `python -m unittest tests.frontend.test_server -v`.
- Successful startup prints the actual bound URL, and the exact printed origin serves this app plus a valid `/api/session`, including an ephemeral `--port 0` case. VERIFY `python -m unittest tests.frontend.test_server -v`.
- The unchanged independent acceptance remains green. VERIFY `python -m unittest tests.acceptance.test_local_web_app_review -v`.
- Original frontend behavior and real approved-fixture browser flow remain green. VERIFY `python -m unittest discover -s tests/frontend -p "test_*.py" -v` and VERIFY `python -m unittest tests.frontend.test_browser_e2e -v`.
- Accepted backend behavior remains green. VERIFY `python -m unittest discover -s tests/backend -p "test_*.py" -v`.
- All flat iteration-3 evidence exists and the deterministic gate passes. VERIFY `python completion_gate.py --loop-dir docs/loop --request-id REQ-20260715-091230-frontend`.
non_goals:
- Do not kill, reconfigure, or move the loop dashboard process.
- Do not add automatic port fallback: an occupied requested port is an error, not permission to choose a different port silently.
- Do not change backend business rules, import parsing, analysis, UI design, OCR, dependencies, network scope, or privacy behavior.
human_qa:
- The previous live QA failed and is not a PASS. After implementation and independent review, product must start the app, verify the exact printed URL reaches this app and `/api/session`, and request a new explicit human PASS at that actual URL.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: pending
- sent_at:
expected_reply:
- changed_files and implementation commit
- red-capable occupied-port, CLI-failure, and printed-URL verification results with flat evidence
- unchanged acceptance/frontend/browser/backend gate results
- root README startup-text proposal for product
- IMPLEMENTATION_DONE to product and REVIEW_REQUEST to review; product retains live human-QA and final acceptance authority
