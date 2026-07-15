# REVIEW_REQUEST

message_type: REVIEW_REQUEST
request_id: REQ-20260715-082547-data-eng
parent_request_id:
iteration: 2
from_lane: data-eng
to_lane: review
status: REVIEWING
created_at: 2026-07-15T09:01:56Z
implementation_commit: 0362cb0
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/import-pipeline.md
- docs/product/analysis-core.md
- docs/product/local-web-api.md
- docs/review/REQ-20260715-082547-data-eng-iter-1.md
- docs/loop/messages/REQ-20260715-082547-data-eng/FIX_REQUEST-iter-2.md
- docs/loop/messages/REQ-20260715-082547-data-eng/IMPLEMENTATION_DONE-iter-2.md
artifact_scope:
- backend/local_web_api.py
- backend/persistence.py
- tests/backend/test_local_web_api_security.py
- tests/backend/test_local_web_api_runs.py
- tests/backend/test_local_web_api_errors.py
- tests/backend/test_local_web_api_boundary.py
- docs/data/local-web-api.md
- implementation commit 0362cb0
acceptance_criteria:
- Unchanged `tests/acceptance/test_local_web_api_review.py` passes all four tests and retains SHA-256 D1E9C7E00429E234980F367ED64913143D33415198665D7EF6EB5C89E7F962E2.
- UNC/network-share database paths fail before SQLite through every public construction route.
- Exactly one of two concurrent facade undo attempts succeeds; the other returns 409 without deleting facts or correction history.
- Mixed-currency aggregation remains 409 while every retained import-run detail remains structured, traceable, and privacy-safe.
- Every accepted CSRF configuration can authorize its exact token; unsupported configured token text fails before session exposure.
- All original C1-C7 behavior, exact fixture oracles/hashes, append-only history, privacy constraints, and dependency boundaries remain green.
implementation_notes:
- Local path validation is centralized in `CoreStore.__init__` before filesystem or SQLite persistence.
- Strict facade undo uses `CoreStore.undo_import_run_if_active()` with state comparison and update under one `BEGIN IMMEDIATE`; existing restorative core undo semantics are preserved separately.
- Run detail uses the active transaction projection without calling monthly aggregation.
- Explicit configured CSRF tokens are constrained to non-empty ASCII text at construction.
verification:
- `python -m unittest tests.acceptance.test_local_web_api_review -v`: exit 0, 4/4.
- `python -m unittest tests.backend.test_local_web_api_security -v`: exit 0, 3/3.
- `python -m unittest tests.backend.test_local_web_api_imports -v`: exit 0, 2/2.
- `python -m unittest tests.backend.test_local_web_api_runs -v`: exit 0, 2/2.
- `python -m unittest tests.backend.test_local_web_api_months -v`: exit 0, 1/1.
- `python -m unittest tests.backend.test_local_web_api_decisions -v`: exit 0, 2/2.
- `python -m unittest tests.backend.test_local_web_api_errors -v`: exit 0, 3/3.
- `python -m unittest tests.backend.test_local_web_api_boundary -v`: exit 0, 3/3.
- `python -m unittest discover -s tests/backend -p "test_*.py" -v`: exit 0, 68/68.
- `python completion_gate.py --loop-dir docs/loop --request-id REQ-20260715-082547-data-eng`: exit 0, SHIP_CHECK_OK.
evidence:
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-acceptance-test-local-web-api-review-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-backend-test-local-web-api-security-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-backend-test-local-web-api-imports-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-backend-test-local-web-api-runs-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-backend-test-local-web-api-months-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-backend-test-local-web-api-decisions-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-backend-test-local-web-api-errors-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-backend-test-local-web-api-boundary-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-discover-s-tests-backend-p-test-py-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-completion-gate.json
dependency_statement:
- No dependency, system package, OCR, network, telemetry, subprocess, listener, UI, raw logging, or scope expansion was introduced.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-15T09:02:57Z
expected_reply:
- REVIEW_DONE PASS or blocker-severity FIX_REQUEST using this request_id and iteration.
- Include per-criterion results, unchanged acceptance hash, scope-creep/looks-done-but-wrong/ease-of-misuse findings, privacy/local-boundary result, exact command exits, and review evidence path.
