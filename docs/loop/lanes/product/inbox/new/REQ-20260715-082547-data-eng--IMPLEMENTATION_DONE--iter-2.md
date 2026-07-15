# IMPLEMENTATION_DONE

message_type: IMPLEMENTATION_DONE
request_id: REQ-20260715-082547-data-eng
parent_request_id:
iteration: 2
from_lane: data-eng
to_lane: product
status: IMPLEMENTATION_DONE
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
artifact_scope:
- backend/local_web_api.py
- backend/persistence.py
- tests/backend/test_local_web_api_security.py
- tests/backend/test_local_web_api_runs.py
- tests/backend/test_local_web_api_errors.py
- tests/backend/test_local_web_api_boundary.py
- docs/data/local-web-api.md
- docs/loop/lanes/data-eng/**
changed_files:
- backend/local_web_api.py
- backend/persistence.py
- docs/data/local-web-api.md
- docs/loop/lanes/data-eng/current.md
- docs/loop/lanes/data-eng/inbox/cur/REQ-20260715-082547-data-eng--FIX_REQUEST--iter-2.md
- tests/backend/test_local_web_api_boundary.py
- tests/backend/test_local_web_api_errors.py
- tests/backend/test_local_web_api_runs.py
- tests/backend/test_local_web_api_security.py
root_cause_changes:
- `CoreStore` normalizes the caller-supplied path text and rejects UNC, network-share, and Windows device-namespace shapes before any parent-directory probe or SQLite connection. `LocalWebApi.from_database()` inherits the same guard.
- `CoreStore.undo_import_run_if_active()` performs the active-state comparison and occurrence/run transition inside one `BEGIN IMMEDIATE` transaction. The facade maps a false compare result to 409; the existing restorative `undo_import_run()` behavior remains available for accepted core invariant repair.
- Run detail now reads `AnalysisService`'s active transaction projection directly, preserving current category/duplicate/inclusion state without invoking single-currency monthly aggregation. Month reads still return 409 for mixed currency.
- Explicit configured CSRF tokens must be non-empty ASCII text and are rejected during construction otherwise, before session metadata can expose an unusable token. Generated and accepted configured tokens retain exact constant-time comparison.
criteria_results:
- C1: PASS; exact ASCII tokens authorize, missing/wrong tokens write nothing, and unsupported Unicode configuration fails before session exposure.
- C2/C6: PASS; mixed-currency month aggregation remains 409 while both retained run details remain structured 200 responses with no retained input.
- C3: PASS; two concurrent facades return statuses 200 and 409 for the same active run, with retained entity counts and correction IDs unchanged.
- C7/INV-8: PASS; three UNC/device path shapes are rejected through both public construction routes before SQLite connect; no listener, network client, OCR, subprocess, telemetry, raw logging, or dependency was added.
- Existing fixture counts, exact month oracles, append-only decisions, correction survival, duplicate graph behavior, and fixture hashes remain unchanged.
frozen_artifact:
- tests/acceptance/test_local_web_api_review.py
- sha256: D1E9C7E00429E234980F367ED64913143D33415198665D7EF6EB5C89E7F962E2
verification:
- command: python -m unittest tests.acceptance.test_local_web_api_review -v
  exit_code: 0
  result: 4 tests passed; all four review-owned blocker families are green.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-acceptance-test-local-web-api-review-v.json
- command: python -m unittest tests.backend.test_local_web_api_security -v
  exit_code: 0
  result: 3 tests passed.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-backend-test-local-web-api-security-v.json
- command: python -m unittest tests.backend.test_local_web_api_imports -v
  exit_code: 0
  result: 2 tests passed; CSV 23/22/1/22 and PDF 12/12/0/12 remain exact.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-backend-test-local-web-api-imports-v.json
- command: python -m unittest tests.backend.test_local_web_api_runs -v
  exit_code: 0
  result: 2 tests passed; concurrent atomic undo and correction-preserving re-import are green.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-backend-test-local-web-api-runs-v.json
- command: python -m unittest tests.backend.test_local_web_api_months -v
  exit_code: 0
  result: May 50340/60000/12 and June 277617/72999/22 remain exact JSON strings/counts.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-backend-test-local-web-api-months-v.json
- command: python -m unittest tests.backend.test_local_web_api_decisions -v
  exit_code: 0
  result: 2 tests passed; category and duplicate histories remain append-only.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-backend-test-local-web-api-decisions-v.json
- command: python -m unittest tests.backend.test_local_web_api_errors -v
  exit_code: 0
  result: 3 tests passed; mixed-currency run detail remains inspectable and envelopes remain privacy-safe.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-backend-test-local-web-api-errors-v.json
- command: python -m unittest tests.backend.test_local_web_api_boundary -v
  exit_code: 0
  result: 3 tests passed; both public factories reject all tested UNC/device shapes before persistence.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-tests-backend-test-local-web-api-boundary-v.json
- command: python -m unittest discover -s tests/backend -p "test_*.py" -v
  exit_code: 0
  result: 68 tests passed with no failures or errors.
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-python-m-unittest-discover-s-tests-backend-p-test-py-v.json
- command: python completion_gate.py --loop-dir docs/loop --request-id REQ-20260715-082547-data-eng
  exit_code: 0
  result: SHIP_CHECK_OK REQ-20260715-082547-data-eng
  evidence: docs/loop/evidence/REQ-20260715-082547-data-eng-iter-2-completion-gate.json
fixture_hashes:
- CSV: 9F93F107DDD02AEE2FB0A0AE19EB962180C680D1FB06D4D90959C96ED8CD7BAA
- PDF: F4B6B524D7C6140EE3F3E24CE87C4A36F0B40619395B5DC17B03F1B99DBC11F8
dependency_statement:
- No dependency was added or installed. The existing project pin remains `pypdf==6.12.2`; no system dependency was used.
blockers:
- None.
delivery:
- channel: send_message_to_thread
- target_thread_id: 019fxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- delivery_status: sent
- sent_at: 2026-07-15T09:02:57Z
needs_review_by: review
expected_reply:
- Product retains final acceptance authority.
- Review independently reruns the unchanged acceptance test and all declared gates against implementation commit 0362cb0, then returns REVIEW_DONE PASS or a blocker-severity FIX_REQUEST.
