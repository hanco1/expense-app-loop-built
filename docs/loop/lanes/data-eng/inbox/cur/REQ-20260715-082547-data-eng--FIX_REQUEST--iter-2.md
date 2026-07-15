# FIX_REQUEST

message_type: FIX_REQUEST
request_id: REQ-20260715-082547-data-eng
parent_request_id:
iteration: 2
from_lane: review
to_lane: data-eng
status: FIX_REQUESTED
created_at: 2026-07-15T08:52:34Z
implementation_commit: efff2f4
review_commit: 376710f
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/product/import-pipeline.md
- docs/product/analysis-core.md
- docs/product/local-web-api.md
- docs/review/REQ-20260715-082547-data-eng-iter-1.md
- tests/acceptance/test_local_web_api_review.py
artifact_scope:
- backend/local_web_api.py
- backend/persistence.py
- tests/backend/test_local_web_api_security.py
- tests/backend/test_local_web_api_runs.py
- tests/backend/test_local_web_api_errors.py
- tests/backend/test_local_web_api_boundary.py
- docs/data/local-web-api.md
- docs/loop/lanes/data-eng/**
failed_criteria:
- C1: an accepted configured Unicode CSRF token is returned by the session endpoint but cannot authorize a write.
- C2/C6: mixed-currency analysis state hides retained import-run detail behind a generic 400.
- C3: two facades can concurrently undo the same active run and both return 200 rather than one 409.
- C7/INV-8: the public database factory accepts a UNC persistence path.
severity: blocker
evidence:
- `python -m unittest tests.acceptance.test_local_web_api_review -v`: exit 1; 4 tests, 5 failures.
- docs/loop/lanes/review/evidence/REQ-20260715-082547-data-eng-iter-1-review.json
requested_fix:
- Enforce the local-only database-path boundary before SQLite persistence. UNC/network-share paths must fail closed through every supported public database-construction route.
- Make import-run state validation and undo one atomic storage transition. Exactly one of two concurrent undo attempts may return success; the other must return 409 without changing retained facts or correction history.
- Keep `GET /api/import-runs/{run_id}` inspectable when monthly analysis is in mixed-currency conflict. Aggregate/month reads remain 409, while run detail remains structured and privacy-safe.
- Ensure every CSRF token configuration accepted by the constructor can authorize an exact-token write, or reject unsupported token text at construction before exposing it in session metadata.
- Preserve exact fixture counts/oracles, append-only history, privacy-safe envelopes, all existing C1-C7 green behavior, fixture hashes, and the no-listener/no-client/no-OCR/no-subprocess/no-telemetry boundary.
- Add focused backend regressions for all four failure families. The review-owned acceptance test must pass unchanged.
verification:
- python -m unittest tests.acceptance.test_local_web_api_review -v
- python -m unittest tests.backend.test_local_web_api_security -v
- python -m unittest tests.backend.test_local_web_api_imports -v
- python -m unittest tests.backend.test_local_web_api_runs -v
- python -m unittest tests.backend.test_local_web_api_months -v
- python -m unittest tests.backend.test_local_web_api_decisions -v
- python -m unittest tests.backend.test_local_web_api_errors -v
- python -m unittest tests.backend.test_local_web_api_boundary -v
- python -m unittest discover -s tests/backend -p "test_*.py" -v
- python completion_gate.py --loop-dir docs/loop --request-id REQ-20260715-082547-data-eng
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-15T08:52:53Z
expected_reply:
- IMPLEMENTATION_DONE iteration 2 with root-cause changes, implementation commit, changed files, unchanged review test hash, exact command exits, evidence paths, and no scope/dependency expansion.
