# REVIEW_REQUEST

message_type: REVIEW_REQUEST
request_id: REQ-20260715-082547-data-eng
parent_request_id:
iteration: 1
from_lane: data-eng
to_lane: review
status: REVIEWING
created_at: 2026-07-15T08:41:53Z
implementation_commit: efff2f4
source_docs:
- docs/loop/goal.md
- docs/loop/constraints.md
- docs/loop/loop-policy.md
- docs/product/import-pipeline.md
- docs/product/analysis-core.md
- docs/product/local-web-api.md
- docs/loop/messages/REQ-20260715-082547-data-eng/IMPLEMENTATION_REQUEST-iter-1.md
- docs/loop/messages/REQ-20260715-082547-data-eng/IMPLEMENTATION_DONE-iter-1.md
artifact_scope:
- backend/**
- contracts/**
- tests/backend/**
- docs/data/**
- implementation commit efff2f4
acceptance_criteria:
- C1: session metadata is deterministic per facade; every mutation requires the CSRF token; rejection writes nothing; responses have no CORS allowance or raw-data logging.
- C2: both fixtures import from bytes with exact 23/22/1/22 and 12/12/0/12 counts; the failed CSV row is visible by locator/code; active, failed, and undone runs persist newest first; detail omits retained input.
- C3: exact re-import creates a distinct inspectable run without double counting; per-run undo is inspectable, repeated undo is 409, and correction history survives all support loss and later re-import.
- C4: May and June match the exact oracles and category maps; every JSON money field is a base-10 string; refund/income remain visible non-spending credits.
- C5: category and duplicate writes append exactly once; the Tim Hortons pair supports pending/same/distinct behavior; invalid component proposals return 409 and append nothing.
- C6: stable privacy-safe envelopes cover validation, missing, conflict, media, size, parser/import, mixed-currency state, and unexpected failures without raw input or traceback.
- C7: all prior backend tests remain green and no listener, network client, OCR, subprocess, telemetry, system dependency, raw logging, or out-of-path persistence was added.
implementation_notes:
- `LocalWebApi` is a listener-free typed dispatcher. It delegates writes to accepted services and serializes exact money only at the final JSON boundary.
- `CoreStore.list_import_run_summaries()` is the sole persistence addition and orders every retained run by `(created_at DESC, run_id DESC)`.
- CSRF validation precedes every POST write. JSON and case-insensitive header duplicates are rejected. Run responses remove retained input and enrich effective duplicate/inclusion state.
verification:
- `python -m unittest tests.backend.test_local_web_api_security -v`: exit 0, 2/2.
- `python -m unittest tests.backend.test_local_web_api_imports -v`: exit 0, 2/2.
- `python -m unittest tests.backend.test_local_web_api_runs -v`: exit 0, 1/1.
- `python -m unittest tests.backend.test_local_web_api_months -v`: exit 0, 1/1.
- `python -m unittest tests.backend.test_local_web_api_decisions -v`: exit 0, 2/2.
- `python -m unittest tests.backend.test_local_web_api_errors -v`: exit 0, 3/3.
- `python -m unittest tests.backend.test_local_web_api_boundary -v`: exit 0, 2/2.
- `python -m unittest discover -s tests/backend -p "test_*.py" -v`: exit 0, 65/65.
- `python completion_gate.py --loop-dir docs/loop --request-id REQ-20260715-082547-data-eng`: exit 0, SHIP_CHECK_OK.
evidence:
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-tests-backend-test-local-web-api-security-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-tests-backend-test-local-web-api-imports-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-tests-backend-test-local-web-api-runs-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-tests-backend-test-local-web-api-months-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-tests-backend-test-local-web-api-decisions-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-tests-backend-test-local-web-api-errors-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-tests-backend-test-local-web-api-boundary-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-python-m-unittest-discover-s-tests-backend-p-test-py-v.json
- docs/loop/evidence/REQ-20260715-082547-data-eng-iter-1-completion-gate.json
fixture_hashes:
- CSV: 9F93F107DDD02AEE2FB0A0AE19EB962180C680D1FB06D4D90959C96ED8CD7BAA
- PDF: F4B6B524D7C6140EE3F3E24CE87C4A36F0B40619395B5DC17B03F1B99DBC11F8
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-15T08:42:50Z
expected_reply:
- REVIEW_DONE PASS or blocker-severity FIX_REQUEST for this request_id and iteration.
- Per-criterion results, scope-creep assessment, looks-done-but-wrong assessment, invariant check, privacy/local-boundary check, ease-of-misuse answer, exact command exits, and review evidence path.
